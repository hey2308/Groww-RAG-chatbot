"""
Phase 1.3 - Data Processing Pipeline
Package initialization for Phase 1.3 submodules.
"""

from .web_scraping import (
    scraper_initializer,
    html_parser,
    data_validator,
    main_scraper
)

__version__ = "1.0.0"
__all__ = [
    "scraper_initializer",
    "html_parser", 
    "data_validator",
    "main_scraper"
]
