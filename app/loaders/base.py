"""Shared document-loader data model and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

MetadataValue: TypeAlias = str | int


class DocumentLoadError(ValueError):
    """A safe, user-facing document extraction failure."""


@dataclass(frozen=True)
class DocumentRecord:
    """A source-aware unit of extracted document text."""

    text: str
    metadata: dict[str, MetadataValue]


def validate_document_path(path: str | Path, expected_extension: str) -> Path:
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise DocumentLoadError(f"Document not found: {candidate}") from exc
    if not resolved.is_file():
        raise DocumentLoadError(f"Not a file: {candidate}")
    if resolved.suffix.casefold() != expected_extension:
        raise DocumentLoadError(f"Expected a {expected_extension} document: {candidate.name}")
    return resolved


def clean_text(text: str) -> str:
    lines = (line.strip() for line in text.replace("\x00", "").splitlines())
    return "\n".join(line for line in lines if line).strip()


def metadata_for(path: Path, file_type: str, **values: MetadataValue) -> dict[str, MetadataValue]:
    return {"file_name": path.name, "file_type": file_type, **values}


def require_records(records: list[DocumentRecord], path: Path) -> list[DocumentRecord]:
    if not records:
        raise DocumentLoadError(f"No readable text was found in {path.name}.")
    return records
