"""Tests for summarizer backend resolution (M4-H)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from my_feed.config import AppConfig, SummarizerConfig, load_config


@pytest.fixture
def clear_backend_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("SUMMARIZER_BACKEND", raising=False)
    yield


def test_get_backend_default_is_gemini(clear_backend_env: None) -> None:
    assert SummarizerConfig().get_backend() == "gemini"


def test_get_backend_from_config(clear_backend_env: None) -> None:
    assert SummarizerConfig(backend="ollama").get_backend() == "ollama"


def test_get_backend_env_overrides_config(
    monkeypatch: pytest.MonkeyPatch,
    clear_backend_env: None,
) -> None:
    cfg = SummarizerConfig(backend="gemini")
    monkeypatch.setenv("SUMMARIZER_BACKEND", "ollama")
    assert cfg.get_backend() == "ollama"


def test_get_backend_invalid_falls_back_to_gemini(
    monkeypatch: pytest.MonkeyPatch,
    clear_backend_env: None,
) -> None:
    monkeypatch.setenv("SUMMARIZER_BACKEND", "chatgpt")
    assert SummarizerConfig(backend="nope").get_backend() == "gemini"


def test_load_config_parses_ollama_section(tmp_path, clear_backend_env: None) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        """
[summarizer]
enabled = true
backend = "ollama"
ollama_model = "gemma4:e4b"

[summarizer.ollama]
base_url = "http://127.0.0.1:11434"
timeout = 90
""",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert isinstance(cfg, AppConfig)
    assert cfg.summarizer.enabled is True
    assert cfg.summarizer.get_backend() == "ollama"
    assert cfg.summarizer.ollama_model == "gemma4:e4b"
    assert cfg.summarizer.ollama.base_url == "http://127.0.0.1:11434"
    assert cfg.summarizer.ollama.timeout == 90.0
