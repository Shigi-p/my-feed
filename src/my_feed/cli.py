"""CLI entrypoint for my-feed (M1: config-driven real or fake pipeline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from my_feed.config import load_config
from my_feed.models import RenderMeta
from my_feed.output import render_bundle
from my_feed.pipeline import run_pipeline
from my_feed.scoring import list_scorers
from my_feed.sources import list_sources

app = typer.Typer(help="my-feed: tech catch-up feed", no_args_is_help=True)


@app.command("run")
def run_cmd(
    top: Annotated[int | None, typer.Option("--top", help="Number of items")] = None,
    scorer: Annotated[str | None, typer.Option("--scorer", help="Score strategy name")] = None,
    config_path: Annotated[Path, typer.Option("--config", help="Path to config.toml")] = Path("config.toml"),
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON")] = False,
    out: Annotated[Path | None, typer.Option("--out", help="Write JSON to file")] = None,
    out_md: Annotated[Path | None, typer.Option("--out-md", help="Write Gemini-ready markdown")] = None,
) -> None:
    """Fetch → score → top N (sources/scorer from config.toml or flags)."""
    config = load_config(config_path)
    if top is not None:
        config = config.model_copy(update={"top_n": top})
    if scorer is not None:
        config = config.model_copy(update={"default_scorer": scorer})

    result = run_pipeline(config)

    if as_json or out is not None:
        payload = result.model_dump(mode="json")
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if out is not None:
            out.write_text(text + "\n", encoding="utf-8")
            typer.echo(f"wrote {out}")
        if as_json:
            typer.echo(text)
        elif out is None:
            pass
    else:
        typer.echo(f"status={result.status.value} scorer={result.scorer} count={len(result.items)}")
        if result.source_errors:
            typer.echo(f"source_errors={result.source_errors}")
        typer.echo("")
        typer.echo(f"{'rank':<4} {'score':>8}  {'source':<16}  title")
        for i, scored in enumerate(result.items, start=1):
            typer.echo(f"{i:<4} {scored.score:>8.2f}  {scored.item.source.value:<16}  {scored.item.title}")

    if out_md is not None:
        meta = RenderMeta(
            generated_at=result.fetched_at,
            scorer=result.scorer,
            count=len(result.items),
            intro=None,
        )
        out_md.write_text(render_bundle(result.items, meta), encoding="utf-8")
        typer.echo(f"wrote {out_md}")

    if result.status.value == "error":
        raise typer.Exit(code=1)


@app.command("sources")
def sources_cmd() -> None:
    """List registered source adapters."""
    for name in list_sources():
        typer.echo(name.value)


@app.command("scorers")
def scorers_cmd() -> None:
    """List registered score strategies."""
    for name in list_scorers():
        typer.echo(name)


@app.command("serve")
def serve_cmd(
    host: Annotated[str, typer.Option("--host", help="Bind address")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port")] = 8000,
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Config path (default: config.local.toml if present)"),
    ] = None,
    db_path: Annotated[
        Path | None,
        typer.Option("--db", help="SQLite path (default: data/my_feed.db)"),
    ] = None,
) -> None:
    """Start the local FastAPI UI (SQLite history; sources from config)."""
    import uvicorn

    from my_feed.web.app import create_app
    from my_feed.web.deps import create_default_web_deps

    deps = create_default_web_deps(config_path=config_path, db_path=db_path)
    app = create_app(deps)
    typer.echo(f"my feed UI → http://{host}:{port}/  (local only)")
    typer.echo(f"config={deps.config_path}  db={deps.db_path}")
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
