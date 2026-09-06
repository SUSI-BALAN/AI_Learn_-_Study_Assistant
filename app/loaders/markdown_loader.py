"""Markdown extraction that retains ATX heading context."""

from pathlib import Path

from app.loaders.base import DocumentLoadError, DocumentRecord, clean_text, metadata_for, require_records, validate_document_path


def load_markdown(path: str | Path) -> list[DocumentRecord]:
    resolved = validate_document_path(path, ".md")
    try:
        text = resolved.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError(f"Could not decode Markdown text in {resolved.name}.") from exc
    records: list[DocumentRecord] = []
    heading = ""
    section_lines: list[str] = []

    def append_section() -> None:
        cleaned = clean_text("\n".join(section_lines))
        if cleaned:
            extra = {"section": heading} if heading else {}
            records.append(DocumentRecord(cleaned, metadata_for(resolved, "md", **extra)))

    for line in text.splitlines():
        stripped = line.lstrip()
        marker_length = len(stripped) - len(stripped.lstrip("#"))
        is_heading = 1 <= marker_length <= 6 and stripped[marker_length:].startswith(" ")
        if is_heading:
            append_section()
            heading = stripped[marker_length:].strip()
            section_lines = [heading]
        else:
            section_lines.append(line)
    append_section()
    return require_records(records, resolved)
