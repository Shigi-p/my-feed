"""FastAPI application factory for local my-feed UI."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from my_feed.models import RenderMeta, SourceName
from my_feed.web.deps import WebDeps, create_default_web_deps

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _safe_next_url(next_url: str, *, default: str = "/") -> str:
    """Allow only same-app relative paths (local tool; still avoid open redirects)."""
    candidate = (next_url or "").strip() or default
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return default


def create_app(deps: WebDeps | None = None) -> FastAPI:
    """Build the app with injectable stores / pipeline / renderer.

    Fetch runs synchronously inside the request (acceptable for local use).
    Real adapters may block for seconds — disable double-submit or move to a
    background job later if that becomes painful.
    """
    deps = deps or create_default_web_deps()
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    # Item IDs may contain ``/`` (e.g. github_trending:owner/repo); encode for hrefs.
    templates.env.filters["path_quote"] = lambda value: quote(str(value), safe="")
    app = FastAPI(title="my feed", docs_url=None, redoc_url=None)
    app.state.deps = deps

    def _latest_run_id() -> str | None:
        runs = deps.run_store.list_runs()
        return runs[0] if runs else None

    def _favorite_ids() -> dict[str, str]:
        """Map item.id -> favorite_id for buttons (read-only; no store writes)."""
        mapping: dict[str, str] = {}
        store = deps.favorite_store
        for item in store.list():
            fav_id = store.favorite_id_for(item.id)
            if fav_id is not None:
                mapping[item.id] = fav_id
        return mapping

    def _scorer_choices() -> list[str]:
        # Keep ``fake`` visible on purpose: comparing fake vs hybrid (and reading
        # score_breakdown) remains useful for debugging.
        return deps.list_scorers_fn()

    def _page_config():
        return deps.load_config_fn(deps.config_path)

    def _run_context(run_id: str | None, result) -> dict:
        config = _page_config()
        return {
            "scorers": _scorer_choices(),
            "default_scorer": config.default_scorer,
            "enabled_sources": [s.value for s in config.enabled_sources],
            "using_fake_only": config.enabled_sources == [SourceName.FAKE],
            "config_path": str(deps.config_path),
            "run_id": run_id,
            "result": result,
            "favorite_ids": _favorite_ids(),
        }

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        run_id = _latest_run_id()
        result = deps.run_store.get_run(run_id) if run_id else None
        ctx = _run_context(run_id, result)
        ctx["nav"] = "home"
        return templates.TemplateResponse(request, "index.html", ctx)

    @app.post("/runs")
    async def create_run(scorer: str = Form("hybrid")) -> RedirectResponse:
        # Blocks until pipeline returns (see create_app docstring).
        config = deps.load_config_fn(deps.config_path)
        config = config.model_copy(update={"default_scorer": scorer})
        result = deps.run_pipeline_fn(config)
        run_id = deps.run_store.save_run(result)
        return RedirectResponse(url=f"/runs/{run_id}", status_code=303)

    @app.get("/runs", response_class=HTMLResponse)
    async def list_runs(request: Request) -> HTMLResponse:
        run_ids = deps.run_store.list_runs()
        rows = []
        for rid in run_ids:
            result = deps.run_store.get_run(rid)
            if result is None:
                continue
            rows.append(
                {
                    "id": rid,
                    "fetched_at": result.fetched_at,
                    "scorer": result.scorer,
                    "count": len(result.items),
                    "status": result.status.value,
                }
            )
        return templates.TemplateResponse(
            request,
            "runs.html",
            {"runs": rows, "nav": "runs"},
        )

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    async def get_run(request: Request, run_id: str) -> HTMLResponse:
        result = deps.run_store.get_run(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="run not found")
        ctx = _run_context(run_id, result)
        ctx["nav"] = "runs"
        return templates.TemplateResponse(request, "run_detail.html", ctx)

    @app.get("/runs/{run_id}/markdown")
    async def download_bundle(run_id: str) -> Response:
        result = deps.run_store.get_run(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="run not found")
        meta = RenderMeta(
            generated_at=result.fetched_at,
            scorer=result.scorer,
            count=len(result.items),
            intro=None,
        )
        body = deps.render_bundle_fn(result.items, meta)
        filename = f"my-feed-{run_id}.md"
        return Response(
            content=body,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/runs/{run_id}/items/{item_id:path}/markdown")
    async def download_single(run_id: str, item_id: str) -> Response:
        # ``:path`` so IDs with ``/`` (GitHub owner/repo) match; clients should
        # still send percent-encoded segments when building URLs.
        result = deps.run_store.get_run(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="run not found")
        scored = next((s for s in result.items if s.item.id == item_id), None)
        if scored is None:
            raise HTTPException(status_code=404, detail="item not found")
        meta = RenderMeta(
            generated_at=result.fetched_at,
            scorer=result.scorer,
            count=1,
            intro=None,
        )
        body = deps.render_single_fn(scored, meta)
        safe = quote(item_id, safe="")
        filename = f"my-feed-{safe}.md"
        return Response(
            content=body,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/favorites", response_class=HTMLResponse)
    async def favorites_page(request: Request) -> HTMLResponse:
        items = deps.favorite_store.list()
        pairs = []
        for item in items:
            fav_id = deps.favorite_store.favorite_id_for(item.id)
            if fav_id is not None:
                pairs.append((fav_id, item))
        return templates.TemplateResponse(
            request,
            "favorites.html",
            {"favorites": pairs, "nav": "favorites"},
        )

    @app.post("/favorites")
    async def add_favorite(
        run_id: str = Form(...),
        item_id: str = Form(...),
        next_url: str = Form("/", alias="next"),
    ) -> RedirectResponse:
        result = deps.run_store.get_run(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="run not found")
        scored = next((s for s in result.items if s.item.id == item_id), None)
        if scored is None:
            raise HTTPException(status_code=404, detail="item not found")
        deps.favorite_store.add(scored.item)
        return RedirectResponse(url=_safe_next_url(next_url), status_code=303)

    @app.delete("/favorites/{favorite_id}")
    async def delete_favorite(favorite_id: str) -> Response:
        deps.favorite_store.remove(favorite_id)
        return Response(status_code=204)

    @app.post("/favorites/{favorite_id}/delete")
    async def delete_favorite_form(
        favorite_id: str,
        next_url: str = Form("/favorites", alias="next"),
    ) -> RedirectResponse:
        deps.favorite_store.remove(favorite_id)
        return RedirectResponse(
            url=_safe_next_url(next_url, default="/favorites"),
            status_code=303,
        )

    return app


# Lazily built so ``from my_feed.web.app import create_app`` (tests) does not
# open SQLite. ``uvicorn my_feed.web.app:app`` still works.
_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
