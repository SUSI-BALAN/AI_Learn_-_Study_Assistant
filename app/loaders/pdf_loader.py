"""PDF extraction with one-based page metadata."""

from pathlib import Path

import pymupdf

from app.loaders.base import DocumentLoadError, DocumentRecord, clean_text, metadata_for, require_records, validate_document_path


def load_pdf(path: str | Path) -> list[DocumentRecord]:
    resolved = validate_document_path(path, ".pdf")
    try:
        with pymupdf.open(resolved) as document:
            records = []
            for index, page in enumerate(document):
                text = clean_text(page.get_text())
                if text:
                    records.append(
                        DocumentRecord(text, metadata_for(resolved, "pdf", page_number=index + 1))
                    )
    except (pymupdf.FileDataError, RuntimeError, OSError) as exc:
        raise DocumentLoadError(f"Could not read PDF {resolved.name}: the file may be corrupted.") from exc
    return require_records(records, resolved)
