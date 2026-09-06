"""Format source metadata without inventing unavailable locations."""

from app.loaders.base import MetadataValue


def format_citation(metadata: dict[str, MetadataValue]) -> str:
    source = str(metadata.get("file_name", "Unknown source"))
    if "page_number" in metadata:
        return f"{source} — Page {metadata['page_number']}"
    if "slide_number" in metadata:
        return f"{source} — Slide {metadata['slide_number']}"
    if "section" in metadata:
        return f"{source} — Section: {metadata['section']}"
    return source
