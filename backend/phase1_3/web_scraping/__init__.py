"""
Phase 1.3.1 - Web Scraping Implementation
Package initialization for web scraping components.
"""

from .scraper_initializer import enhanced_scraper, ScraperConfig
from .html_parser import groww_parser, GrowwHTMLParser
from .data_validator import scraped_data_validator, ScrapedDataValidator
from .main_scraper import web_scraping_impl, WebScrapingImplementation

__version__ = "1.0.0"
__all__ = [
    "enhanced_scraper",
    "ScraperConfig",
    "groww_parser", 
    "GrowwHTMLParser",
    "scraped_data_validator",
    "ScrapedDataValidator",
    "web_scraping_impl",
    "WebScrapingImplementation"
]
