"""Local FastAPI UI (T-Web). Swap pipeline/store/renderer at M2 via create_app deps."""

from my_feed.web.app import create_app

__all__ = ["create_app"]
