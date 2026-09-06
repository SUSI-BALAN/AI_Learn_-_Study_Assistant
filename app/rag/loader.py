"""Allowlisted file-type detection and normalized loader dispatch."""

from pathlib import Path
from typing import Callable

from app.loaders.base import DocumentLoadError, DocumentRecord
from app.loaders.docx_loader import load_docx
from app.loaders.markdown_loader import load_markdown
from app.loaders.pdf_loader import load_pdf
from app.loaders.pptx_loader import load_pptx
from app.loaders.txt_loader import load_txt

Loader = Callable[[str | Path], list[DocumentRecord]]

LOADERS: dict[str, Loader] = {
    ".pdf": load_pdf,
    ".txt": load_txt,
    ".md": load_markdown,
    ".docx": load_docx,
    ".pptx": load_pptx,
}


def load_document(path: str | Path) -> list[DocumentRecord]:
    candidate = Path(path)
    loader = LOADERS.get(candidate.suffix.casefold())
    if loader is None:
        supported = ", ".join(sorted(LOADERS))
        raise DocumentLoadError(f"Unsupported document type '{candidate.suffix or '(none)'}'. Supported: {supported}")
    return loader(candidate)


def supported_extensions() -> tuple[str, ...]:
    return tuple(LOADERS)
