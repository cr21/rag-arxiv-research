"""Stubs for the `docling` package (optional extra)."""

from pydantic import BaseModel

class PdfPipelineOptions(BaseModel):
    do_table_structure: bool = ...
    do_ocr: bool = ...
