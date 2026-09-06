"""Plain-text document extraction with common encoding fallbacks."""

from pathlib import Path

from app.loaders.base import (
    DocumentLoadError,
    DocumentRecord,
    clean_text,
    metadata_for,
    require_records,
    validate_document_path,
)


def load_txt(path: str | Path) -> list[DocumentRecord]:
    resolved = validate_document_path(path, ".txt")
    raw = resolved.read_bytes()
    text = ""
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if not text and raw:
        raise DocumentLoadError(f"Could not decode text in {resolved.name}.")
    cleaned = clean_text(text)
    records = [DocumentRecord(cleaned, metadata_for(resolved, "txt"))] if cleaned else []
    return require_records(records, resolved)
