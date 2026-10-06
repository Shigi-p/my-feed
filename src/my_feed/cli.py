"""CLI entrypoint for my-feed (C0: fake pipeline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from my_feed.config import load_config
from my_feed.models import RenderMeta
from my_feed.output import render_bundle
from my_feed.pipeline import run_pipeline
from my_feed.scoring import list_scorers
from my_feed.sources import list_sources

app = typer.Typer(help="my-feed: tech catch-up feed (C0 contract hub)", no_args_is_help=True)


@app.command("run")
def run_cmd(
    top: Annotated[Optional[int], typer.Option("--top", help="Number of items")] = None,
    scorer: Annotated[Optional[str], typer.Option("--scorer", help="Score strategy name")] = None,
    config_path: Annotated[Path, typer.Option("--config", help="Path to config.toml")] = Path("config.toml"),
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON")] = False,
    out: Annotated[Optional[Path], typer.Option("--out", help="Write JSON to file")] = None,
    out_md: Annotated[Optional[Path], typer.Option("--out-md", help="Write stub markdown")] = None,
) -> None:
    """Fetch → score → top N (Fake sources/scorer in C0)."""
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
            typer.echo(
                f"{i:<4} {scored.score:>8.2f}  {scored.item.source.value:<16}  {scored.item.title}"
            )

    if out_md is not None:
        meta = RenderMeta(
            generated_at=result.fetched_at,
            scorer=result.scorer,
            count=len(result.items),
            intro="C0 stub markdown — replace with T-Md templates later.",
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


if __name__ == "__main__":
    app()
