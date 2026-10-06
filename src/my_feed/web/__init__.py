"""Local FastAPI UI. Defaults (M2): SQLite stores + resolved config via create_app()."""

from my_feed.web.app import create_app

__all__ = ["create_app"]
