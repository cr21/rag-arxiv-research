"""Stubs for the `docling` package (optional extra)."""

from typing import Any

class PdfFormatOption:
    def __init__(self, *, pipeline_options: Any = None) -> None: ...

class _Document:
    texts: Any
    def export_to_text(self) -> str: ...

class _ConversionResult:
    document: _Document

class DocumentConverter:
    def __init__(self, *, format_options: dict[Any, Any] | None = None) -> None: ...
    def convert(
        self,
        path: str,
        *,
        max_num_pages: int | None = None,
        max_file_size: int | None = None,
    ) -> _ConversionResult: ...
