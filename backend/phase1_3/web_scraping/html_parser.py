"""
Phase 1.3.1 - Web Scraping Implementation
HTML Content Parser for Groww Mutual Fund Pages
"""

import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrowwHTMLParser:
    """
    Specialized parser for Groww mutual fund pages.
    Extracts structured data from HTML content.
    """
    
    def __init__(self):
        """
        Initialize parser with field mappings and extraction rules.
        """
        self.field_selectors = self._initialize_field_selectors()
        self.data_schema = self._initialize_data_schema()
        
        logger.info("Groww HTML parser initialized")
    
    def _initialize_field_selectors(self) -> Dict[str, List[str]]:
        """
        CSS selectors kept for legacy compatibility.
        Primary extraction now uses full-page text patterns via _extract_from_page_text().
        """
        return {
            'fund_name': ['h1', 'title'],
            'expense_ratio': ['[data-testid="expenseRatio"]'],
            'exit_load':     ['[data-testid="exitLoad"]'],
            'min_sip':       ['[data-testid="minSip"]'],
            'riskometer':    ['[data-testid="riskometer"]'],
            'benchmark':     ['[data-testid="benchmark"]'],
            'nav':           ['[data-testid="nav"]'],
            'fund_type':     ['[data-testid="fundType"]'],
            'category':      ['[data-testid="category"]'],
            'returns_1y':    ['[data-testid="return1Y"]'],
            'returns_3y':    ['[data-testid="return3Y"]'],
            'returns_5y':    ['[data-testid="return5Y"]'],
        }
    
    def _initialize_data_schema(self) -> Dict[str, Any]:
        """
        Initialize data schema for validation.
        """
        return {
            'required_fields': [
                'fund_name',
                'source_url',
                'scraped_at'
            ],
            'financial_fields': [
                'expense_ratio',
                'exit_load',
                'min_sip',
                'nav'
            ],
            'performance_fields': [
                'returns_1y',
                'returns_3y',
                'returns_5y'
            ],
            'risk_fields': [
                'riskometer',
                'benchmark'
            ],
            'classification_fields': [
                'fund_type',
                'category'
            ]
        }
    
    def parse_fund_page(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Parse fund page and extract structured data.

        Groww is a React SPA — the rendered HTML uses hashed class names and
        no stable data-testid attributes for most fields.  The most reliable
        approach is to extract the full visible text of the page and apply
        regex patterns against it.
        """
        logger.info(f"Parsing fund page: {url}")

        fund_data = {
            'source_url': url,
            'scraped_at': None,  # set by scraper
            'parsing_method': 'text_pattern',
            'extraction_confidence': 0.0
        }

        try:
            # ── 1. Get full visible page text ──────────────────────────────
            page_text = soup.get_text(separator=' ', strip=True)

            # ── 2. Fund name ───────────────────────────────────────────────
            fund_data['fund_name'] = self._extract_fund_name(soup)

            # ── 3. Infer type / category from name / URL ───────────────────
            fund_data['fund_type'] = self._extract_fund_type(soup)
            fund_data['category']  = self._extract_category(soup)

            # ── 4. Financial metrics via text patterns ─────────────────────
            fund_data['nav']           = self._extract_nav_from_text(page_text)
            fund_data['expense_ratio'] = self._extract_expense_ratio_from_text(page_text)
            fund_data['exit_load']     = self._extract_exit_load_from_text(page_text)
            fund_data['min_sip']       = self._extract_min_sip_from_text(page_text)
            fund_data['riskometer']    = self._extract_riskometer_from_text(page_text)
            fund_data['benchmark']     = self._extract_benchmark_from_text(page_text)

            # ── 5. Returns ─────────────────────────────────────────────────
            fund_data['returns'] = self._extract_returns_from_text(page_text)

            # ── 6. Asset allocation & extra details ────────────────────────
            fund_data['asset_allocation'] = self._extract_asset_allocation(soup)
            fund_data['fund_details']     = self._extract_additional_details(soup)

            # ── 7. Confidence & validation ─────────────────────────────────
            fund_data['extraction_confidence'] = self._calculate_extraction_confidence(fund_data)
            fund_data['validation_status']     = self._validate_extracted_data(fund_data)

            logger.info(f"Parsed: {fund_data.get('fund_name', 'Unknown')} "
                        f"(confidence {fund_data['extraction_confidence']:.1f}%)")
            return fund_data

        except Exception as e:
            logger.error(f"Error parsing fund page: {e}")
            return {
                'source_url': url,
                'parsing_method': 'text_pattern',
                'error': str(e),
                'extraction_confidence': 0.0,
                'validation_status': 'failed'
            }

    # ── Text-pattern extractors ────────────────────────────────────────────

    def _extract_nav_from_text(self, text: str) -> str:
        """
        Extract NAV from rendered page text.

        Groww renders NAV as:  NAV: 29 May '26  ₹1,433.27
        or simply as a ₹ value near the word NAV.
        """
        # Pattern 1: NAV label followed by a date then ₹ amount
        m = re.search(
            r'NAV[:\s]*\d{1,2}\s+\w+\s+[\'`]?\d{2,4}[\'`]?\s*₹\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if m:
            return f"₹{m.group(1).replace(',', '')}"

        # Pattern 2: NAV label directly followed by ₹ amount
        m = re.search(
            r'\bNAV\b[^₹\d]{0,30}₹\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if m:
            return f"₹{m.group(1).replace(',', '')}"

        # Pattern 3: ₹ amount near "Net Asset Value"
        m = re.search(
            r'Net\s+Asset\s+Value[^₹\d]{0,30}₹\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if m:
            return f"₹{m.group(1).replace(',', '')}"

        return "Not available"

    def _extract_expense_ratio_from_text(self, text: str) -> str:
        """
        Extract expense ratio from rendered page text.
        Groww shows: Expense ratio  0.79%
        """
        m = re.search(
            r'[Ee]xpense\s+[Rr]atio[^%\d]{0,20}([\d]+\.[\d]+)\s*%',
            text
        )
        if m:
            return f"{m.group(1)}%"
        return "Not available"

    def _extract_exit_load_from_text(self, text: str) -> str:
        """
        Extract exit load from rendered page text.
        Groww shows: Exit load of 1%, if redeemed within 1 year.
        or: Nil  (for ELSS)
        """
        # Nil / no exit load
        if re.search(r'[Ee]xit\s+[Ll]oad[^a-z]{0,30}[Nn]il\b', text):
            return "Nil"
        if re.search(r'[Nn]o\s+[Ee]xit\s+[Ll]oad', text):
            return "Nil"

        # Percentage exit load
        m = re.search(
            r'[Ee]xit\s+[Ll]oad[^%\d]{0,40}([\d]+\.?[\d]*)\s*%',
            text
        )
        if m:
            return f"{m.group(1)}%"

        return "Not available"

    def _extract_min_sip_from_text(self, text: str) -> str:
        """
        Extract minimum SIP from rendered page text.
        Groww shows: Min. for SIP  ₹100
        """
        m = re.search(
            r'[Mm]in(?:imum)?\.?\s+(?:for\s+)?SIP[^₹\d]{0,20}₹\s*([\d,]+)',
            text
        )
        if m:
            return f"₹{m.group(1).replace(',', '')}"

        # Fallback: SIP label near ₹ amount
        m = re.search(
            r'\bSIP\b[^₹\d]{0,20}₹\s*([\d,]+)',
            text
        )
        if m:
            return f"₹{m.group(1).replace(',', '')}"

        return "Not available"

    def _extract_riskometer_from_text(self, text: str) -> str:
        """
        Extract riskometer classification from rendered page text.
        """
        risk_levels = [
            'Very High', 'Moderately High', 'Moderate',
            'Moderately Low', 'Low'
        ]
        for level in risk_levels:
            if re.search(re.escape(level), text, re.IGNORECASE):
                return level
        return "Not available"

    def _extract_benchmark_from_text(self, text: str) -> str:
        """
        Extract benchmark index from rendered page text.
        Groww shows: Benchmark  Nifty 500 TRI
        """
        m = re.search(
            r'[Bb]enchmark[:\s]+([A-Za-z0-9 &]+(?:TRI|Index|50|100|150|200|500)?)',
            text
        )
        if m:
            benchmark = m.group(1).strip()
            # Trim trailing noise words
            benchmark = re.sub(r'\s+(Fund|Direct|Growth|Plan|Regular).*$', '', benchmark)
            if len(benchmark) > 3:
                return benchmark
        return "Not available"

    def _extract_returns_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract 1Y / 3Y / 5Y returns from rendered page text.
        Groww shows annualised returns as: +25.46 %  3Y annualised
        """
        returns: Dict[str, str] = {
            '1Y': 'Not available',
            '3Y': 'Not available',
            '5Y': 'Not available',
        }

        for period in ('1Y', '3Y', '5Y'):
            # Pattern: number% followed by period label
            m = re.search(
                rf'([+-]?[\d]+\.?[\d]*)\s*%\s*{re.escape(period)}\b',
                text, re.IGNORECASE
            )
            if m:
                returns[period] = f"{m.group(1)}%"
                continue

            # Pattern: period label followed by number%
            m = re.search(
                rf'\b{re.escape(period)}\b[^%\d]{{0,20}}([+-]?[\d]+\.?[\d]*)\s*%',
                text, re.IGNORECASE
            )
            if m:
                returns[period] = f"{m.group(1)}%"

        return returns
    
    def _extract_fund_name(self, soup: BeautifulSoup) -> str:
        """
        Extract fund name from page.
        """
        for selector in self.field_selectors['fund_name']:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and len(name) > 3:  # Minimum reasonable length
                    return self._clean_text(name)
        
        # Fallback: extract from title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean title to get fund name
            name = re.sub(r'\s*-\s*Groww.*$', '', title, flags=re.IGNORECASE)
            name = re.sub(r'\s*\|\s*Groww.*$', '', name, flags=re.IGNORECASE)
            return self._clean_text(name)
        
        return "Unknown Fund"
    
    def _extract_fund_type(self, soup: BeautifulSoup) -> str:
        """
        Extract fund type (Direct, Regular, etc.).
        """
        for selector in self.field_selectors['fund_type']:
            element = soup.select_one(selector)
            if element:
                fund_type = element.get_text(strip=True)
                if fund_type:
                    return self._clean_text(fund_type)
        
        # Try to infer from fund name
        fund_name = self._extract_fund_name(soup)
        if 'direct' in fund_name.lower():
            return "Direct Growth"
        elif 'regular' in fund_name.lower():
            return "Regular Growth"
        
        return "Not available"
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """
        Extract fund category.
        """
        for selector in self.field_selectors['category']:
            element = soup.select_one(selector)
            if element:
                category = element.get_text(strip=True)
                if category:
                    return self._clean_text(category)
        
        # Try to infer from fund name
        fund_name = self._extract_fund_name(soup)
        if 'large cap' in fund_name.lower():
            return "Large Cap"
        elif 'mid cap' in fund_name.lower():
            return "Mid Cap"
        elif 'equity' in fund_name.lower():
            return "Equity"
        elif 'focused' in fund_name.lower():
            return "Focused"
        elif 'elss' in fund_name.lower() or 'tax saver' in fund_name.lower():
            return "ELSS"
        
        return "Not available"
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_expense_ratio_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_exit_load(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_exit_load_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_min_sip(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_min_sip_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_nav(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_nav_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_returns(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_returns_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_riskometer(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_riskometer_from_text(soup.get_text(separator=' ', strip=True))

    def _extract_benchmark(self, soup: BeautifulSoup) -> str:
        """Legacy CSS-based extractor — delegates to text pattern."""
        return self._extract_benchmark_from_text(soup.get_text(separator=' ', strip=True))
    
    def _extract_asset_allocation(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract asset allocation data.
        """
        allocation = {}
        
        # Look for allocation tables or sections
        allocation_selectors = [
            '.asset-allocation',
            '[class*="allocation"]',
            '.portfolio-allocation',
            '.fund-allocation'
        ]
        
        for selector in allocation_selectors:
            allocation_section = soup.select_one(selector)
            if allocation_section:
                # Extract allocation percentages
                allocation_items = allocation_section.find_all(['tr', 'div'])
                for item in allocation_items:
                    text = item.get_text(strip=True)
                    if self._contains_allocation_info(text):
                        asset_class, percentage = self._parse_allocation_item(text)
                        if asset_class and percentage:
                            allocation[asset_class] = percentage
                
                if allocation:  # If we found allocation data
                    break
        
        # Default allocation if not found
        if not allocation:
            allocation = {
                'equity': 'Not available',
                'debt': 'Not available',
                'cash': 'Not available',
                'others': 'Not available'
            }
        
        return allocation
    
    def _extract_additional_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract additional fund details including fund manager via text patterns.
        """
        details = {}
        page_text = soup.get_text(separator=' ', strip=True)

        # ── Fund manager via text pattern ──────────────────────────────────
        # Groww renders: Fund Manager  Amar Kalkundrikar, Dhruv Muchhal
        # or:            Fund Managers  Chirag Setalvad
        manager = self._extract_fund_manager_from_text(page_text)
        if manager:
            details['fund_manager'] = manager

        # ── AUM via text pattern ───────────────────────────────────────────
        # Groww renders: Fund size (AUM)  ₹85,357.92 Cr
        m = re.search(
            r'(?:Fund\s+size|AUM)[^₹\d]{0,30}₹\s*([\d,]+\.?\d*)\s*(?:Cr|crore)?',
            page_text, re.IGNORECASE
        )
        if m:
            details['aum'] = f"₹{m.group(1).replace(',', '')} Cr"

        # ── Description fallback via CSS ───────────────────────────────────
        for selector in ['.fund-description', '[class*="description"]', '.about-fund']:
            element = soup.select_one(selector)
            if element:
                desc = element.get_text(strip=True)
                if len(desc) > 50:
                    details['description'] = desc
                    break

        return details

    def _extract_fund_manager_from_text(self, text: str) -> str:
        """
        Extract fund manager name(s) from rendered page text.

        Groww renders:
          Fund Manager   Amar Kalkundrikar, Dhruv Muchhal
          Fund Managers  Chirag Setalvad
        """
        # Pattern: "Fund Manager(s)" label followed by one or more names
        m = re.search(
            r'Fund\s+Managers?\s{1,10}([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)*)',
            text
        )
        if m:
            raw = m.group(1).strip()
            # Stop at common noise words that follow the name section
            raw = re.split(r'\s+(?:Since|since|AUM|Expense|Exit|Min|NAV|Risk|Bench|Fund\s+size)', raw)[0]
            return raw.strip()
        return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,%₹()]', '', text)
        
        # Normalize common variations
        text = re.sub(r'\s*-\s*', ' - ', text)
        text = re.sub(r'\s*\.\s*', '. ', text)
        
        return text.strip()
    
    def _extract_percentage(self, text: str) -> str:
        """
        Extract percentage value from text.
        """
        if not text:
            return "Not available"
        
        # Look for percentage patterns
        percentage_patterns = [
            r'(\d+\.?\d*)\s*%?',
            r'(\d+\.?\d*)\s*percent',
            r'(\d+\.?\d*)\s*p\.?c\.?'
        ]
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                percentage = match.group(1)
                return f"{percentage}%"
        
        return "Not available"
    
    def _extract_currency(self, text: str) -> str:
        """
        Extract currency value from text.
        """
        if not text:
            return "Not available"
        
        # Look for currency patterns
        currency_patterns = [
            r'[₹Rs]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:Rs|INR|₹)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1).replace(',', '')
                return f"₹{amount}"
        
        return "Not available"
    
    def _contains_allocation_info(self, text: str) -> bool:
        """
        Check if text contains allocation information.
        """
        allocation_keywords = ['equity', 'debt', 'cash', 'others', 'allocation', '%']
        text_lower = text.lower()
        
        return any(keyword in text_lower for keyword in allocation_keywords)
    
    def _parse_allocation_item(self, text: str) -> tuple:
        """
        Parse allocation item to get asset class and percentage.
        """
        text_lower = text.lower()
        
        # Identify asset class
        asset_classes = {
            'equity': 'equity',
            'debt': 'debt', 
            'cash': 'cash',
            'others': 'others',
            'other': 'others'
        }
        
        asset_class = None
        for keyword, class_name in asset_classes.items():
            if keyword in text_lower:
                asset_class = class_name
                break
        
        # Extract percentage
        percentage = self._extract_percentage(text)
        
        return (asset_class, percentage)
    
    def _calculate_extraction_confidence(self, fund_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for extracted data.
        """
        total_fields = 0
        extracted_fields = 0
        
        # Count total expected fields
        field_categories = [
            self.data_schema['required_fields'],
            self.data_schema['financial_fields'],
            self.data_schema['performance_fields'],
            self.data_schema['risk_fields'],
            self.data_schema['classification_fields']
        ]
        
        for category in field_categories:
            total_fields += len(category)
        
        # Count successfully extracted fields
        for category in field_categories:
            for field in category:
                if field in fund_data and fund_data[field] != "Not available":
                    extracted_fields += 1
        
        # Calculate confidence percentage
        confidence = (extracted_fields / total_fields) * 100 if total_fields > 0 else 0
        
        return round(confidence, 1)
    
    def _validate_extracted_data(self, fund_data: Dict[str, Any]) -> str:
        """
        Validate extracted data against schema.
        """
        # Check required fields
        for field in self.data_schema['required_fields']:
            if field not in fund_data or not fund_data[field]:
                return "missing_required_fields"
        
        # Check data quality
        confidence = fund_data.get('extraction_confidence', 0)
        if confidence < 50.0:
            return "low_confidence"
        elif confidence < 80.0:
            return "medium_confidence"
        
        return "valid"
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """
        Get parser statistics and configuration.
        """
        return {
            'field_selectors_count': len(self.field_selectors),
            'total_selectors': sum(len(selectors) for selectors in self.field_selectors.values()),
            'schema_categories': list(self.data_schema.keys()),
            'parser_version': '1.0',
            'supported_fields': list(self.field_selectors.keys())
        }

# Global parser instance
groww_parser = GrowwHTMLParser()

if __name__ == "__main__":
    # Test parser with sample HTML
    test_html = """
    <html>
        <head><title>HDFC Large Cap Fund Direct Growth - Groww</title></head>
        <body>
            <h1 data-testid="fundName">HDFC Large Cap Fund Direct Growth</h1>
            <div class="fund-type">Direct Growth</div>
            <div class="category">Large Cap</div>
            <span data-testid="expenseRatio">1.25%</span>
            <span data-testid="exitLoad">0%</span>
            <span data-testid="minSip">₹500</span>
            <span data-testid="nav">₹125.67</span>
            <span data-testid="return1Y">12.5%</span>
            <span data-testid="return3Y">15.2%</span>
            <span data-testid="return5Y">14.8%</span>
            <div data-testid="riskometer">Moderately High</div>
            <div data-testid="benchmark">Nifty 50 TRI</div>
        </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(test_html, 'html.parser')
    parser = GrowwHTMLParser()
    
    print("Testing Groww HTML Parser...")
    
    # Parse test HTML
    result = parser.parse_fund_page(soup, "https://groww.in/test")
    
    print(f"\nParsing Result:")
    print(f"Fund Name: {result.get('fund_name', 'N/A')}")
    print(f"Fund Type: {result.get('fund_type', 'N/A')}")
    print(f"Category: {result.get('category', 'N/A')}")
    print(f"Expense Ratio: {result.get('expense_ratio', 'N/A')}")
    print(f"Exit Load: {result.get('exit_load', 'N/A')}")
    print(f"Min SIP: {result.get('min_sip', 'N/A')}")
    print(f"NAV: {result.get('nav', 'N/A')}")
    print(f"Returns: {result.get('returns', {})}")
    print(f"Riskometer: {result.get('riskometer', 'N/A')}")
    print(f"Benchmark: {result.get('benchmark', 'N/A')}")
    print(f"Extraction Confidence: {result.get('extraction_confidence', 0):.1f}%")
    print(f"Validation Status: {result.get('validation_status', 'unknown')}")
    
    # Show parser stats
    stats = parser.get_parsing_stats()
    print(f"\nParser Stats:")
    print(f"Field Categories: {stats['field_selectors_count']}")
    print(f"Total Selectors: {stats['total_selectors']}")
    print(f"Supported Fields: {stats['supported_fields']}")
