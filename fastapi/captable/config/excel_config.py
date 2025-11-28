"""
Excel Configuration

Excel-specific configuration settings.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ExcelConfig(BaseModel):
    """Excel generation configuration."""

    # Default formatting
    default_font_size: int = Field(default=10, description="Default font size")
    default_bg_color: str = Field(
        default="#869A78", description="Default background color")
    font_pt_sans: str = Field(
        default="PT Sans", description="PT Sans font name")
    font_century_gothic: str = Field(
        default="Century Gothic", description="Century Gothic font name")

    # Sheet settings
    padding_offset: int = Field(
        default=1, description="Padding offset for tables")
    auto_calc_mode: bool = Field(
        default=True, description="Auto calculation mode")

    # Performance
    batch_write_size: int = Field(
        default=100, description="Batch write size for cells")
    enable_formula_caching: bool = Field(
        default=True, description="Enable formula caching")

    # Table settings
    default_table_style: str = Field(
        default="Table Style Medium 2", description="Default table style")

    class Config:
        frozen = True


_excel_config: ExcelConfig = ExcelConfig()


def get_excel_config() -> ExcelConfig:
    """Get Excel configuration (singleton)."""
    return _excel_config


def update_excel_config(**kwargs: Any) -> ExcelConfig:
    """Update Excel configuration."""
    global _excel_config
    _excel_config = _excel_config.model_copy(update=kwargs)
    return _excel_config
