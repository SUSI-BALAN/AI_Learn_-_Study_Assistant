"""DOCX paragraph extraction with heading/section metadata."""

from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from app.loaders.base import DocumentLoadError, DocumentRecord, clean_text, metadata_for, require_records, validate_document_path


def load_docx(path: str | Path) -> list[DocumentRecord]:
    resolved = validate_document_path(path, ".docx")
    try:
        document = Document(resolved)
    except (PackageNotFoundError, BadZipFile, ValueError, KeyError) as exc:
        raise DocumentLoadError(f"Could not read DOCX {resolved.name}: the file may be corrupted.") from exc

    records: list[DocumentRecord] = []
    section = ""
    section_lines: list[str] = []

    def append_section() -> None:
        text = clean_text("\n".join(section_lines))
        if text:
            extra = {"section": section} if section else {}
            records.append(DocumentRecord(text, metadata_for(resolved, "docx", **extra)))

    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)
        if not text:
            continue
        style_name = paragraph.style.name if paragraph.style is not None else ""
        if style_name.casefold().startswith("heading"):
            append_section()
            section = text
            section_lines = [text]
        else:
            section_lines.append(text)
    append_section()
    return require_records(records, resolved)
