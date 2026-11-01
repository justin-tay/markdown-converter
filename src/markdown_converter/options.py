"""Choices that shape each Converted Document, taken from the command line."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversionOptions:
    front_matter: bool = True
    min_image_size: int | None = None
    pdf_page_images: bool = False
