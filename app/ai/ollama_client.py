"""Single service boundary for all Ollama HTTP communication."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """A user-recoverable Ollama communication error."""


@dataclass(frozen=True)
class OllamaHealth:
    reachable: bool
    model_available: bool
    detail: str = ""
    active_model: str = ""
    using_fallback: bool = False


class OllamaClient:
    def __init__(
        self, host: str, model: str, fallback_model: str = "", timeout: float = 30.0
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.last_model_used = ""

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.host}{path}", data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OllamaError(str(exc)) from exc

    def health(self) -> OllamaHealth:
        try:
            payload = self._request("/api/tags")
        except OllamaError as exc:
            return OllamaHealth(False, False, str(exc))
        names = {item.get("name", "") for item in payload.get("models", [])}
        primary_available = _model_available(self.model, names)
        fallback_available = bool(self.fallback_model) and _model_available(self.fallback_model, names)
        if primary_available:
            return OllamaHealth(True, True, active_model=self.model)
        if fallback_available:
            detail = f"Primary model '{self.model}' unavailable; using '{self.fallback_model}'."
            return OllamaHealth(True, True, detail, self.fallback_model, True)
        detail = f"Install the primary model with: ollama pull {self.model}"
        return OllamaHealth(True, False, detail)

    def chat(
        self, messages: list[dict[str, str]], options: dict[str, Any] | None = None
    ) -> str:
        failures: list[str] = []
        for model in dict.fromkeys(filter(None, (self.model, self.fallback_model))):
            try:
                payload = self._request(
                    "/api/chat",
                    {
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": options or {"temperature": 0.2, "num_predict": 384},
                    },
                )
                content = payload.get("message", {}).get("content", "").strip()
                if content:
                    self.last_model_used = model
                    return content
                failures.append(f"{model}: empty response")
            except OllamaError as exc:
                failures.append(f"{model}: {exc}")
        raise OllamaError("; ".join(failures) or "No Ollama model is configured.")


def _model_available(requested: str, available_names: set[str]) -> bool:
    requested_base = requested.split(":", 1)[0]
    return any(name == requested or name.split(":", 1)[0] == requested_base for name in available_names)
