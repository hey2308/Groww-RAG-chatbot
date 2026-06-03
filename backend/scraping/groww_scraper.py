import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from typing import Dict, List, Any
import time
import logging
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrowwScraper:
    def __init__(self):
        """
        Initialize the Groww scraper with configuration.
        """
        self.base_url = settings.groww_base_url
        self.delay = settings.scraping_delay
        self.max_retries = settings.max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def setup_selenium_driver(self):
        """
        Setup Selenium WebDriver for dynamic content.
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            logger.error(f"Error setting up Selenium driver: {e}")
            raise
    
    def scrape_fund_page(self, fund_url: str) -> Dict[str, Any]:
        """
        Scrape individual fund page for key information.
        """
        logger.info(f"Scraping fund page: {fund_url}")
        
        for attempt in range(self.max_retries):
            try:
                # First try with requests (faster)
                response = self.session.get(fund_url, timeout=30)
                if response.status_code == 200:
                    return self._parse_fund_data(response.text, fund_url)
                
                # If requests fails, try with Selenium
                driver = self.setup_selenium_driver()
                try:
                    driver.get(fund_url)
                    time.sleep(3)  # Wait for page load
                    
                    # Wait for specific elements
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    page_source = driver.page_source
                    fund_data = self._parse_fund_data(page_source, fund_url)
                    driver.quit()
                    return fund_data
                    
                except Exception as selenium_error:
                    logger.warning(f"Selenium attempt {attempt + 1} failed: {selenium_error}")
                    if 'driver' in locals():
                        driver.quit()
                    
            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed: {e}")
                
            if attempt < self.max_retries - 1:
                time.sleep(self.delay * (attempt + 1))  # Exponential backoff
        
        logger.error(f"Failed to scrape {fund_url} after {self.max_retries} attempts")
        return {}
    
    def _parse_fund_data(self, html_content: str, fund_url: str) -> Dict[str, Any]:
        """
        Parse fund data from HTML content.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            fund_data = {
                'source_url': fund_url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'fund_name': self._extract_fund_name(soup),
                'expense_ratio': self._extract_expense_ratio(soup),
                'exit_load': self._extract_exit_load(soup),
                'min_sip': self._extract_min_sip(soup),
                'riskometer': self._extract_riskometer(soup),
                'benchmark': self._extract_benchmark(soup),
                'nav': self._extract_nav(soup),
                'returns': self._extract_returns(soup),
                'asset_allocation': self._extract_asset_allocation(soup),
                'fund_type': self._extract_fund_type(soup),
                'category': self._extract_category(soup)
            }
            
            logger.info(f"Successfully parsed data for {fund_data.get('fund_name', 'Unknown Fund')}")
            return fund_data
            
        except Exception as e:
            logger.error(f"Error parsing fund data: {e}")
            return {'source_url': fund_url, 'error': str(e)}
    
    def _extract_fund_name(self, soup: BeautifulSoup) -> str:
        """Extract fund name from page."""
        selectors = [
            'h1[data-testid="fundName"]',
            '.fund-name',
            'h1',
            '[class*="fund-name"]',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Unknown Fund"
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> str:
        """Extract expense ratio."""
        selectors = [
            '[data-testid="expenseRatio"]',
            '.expense-ratio',
            '[class*="expense"]',
            'td:contains("Expense")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Extract percentage if present
                if '%' in text:
                    return text
        return "Not available"
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> str:
        """Extract exit load."""
        selectors = [
            '[data-testid="exitLoad"]',
            '.exit-load',
            '[class*="exit"]',
            'td:contains("Exit")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_min_sip(self, soup: BeautifulSoup) -> str:
        """Extract minimum SIP amount."""
        selectors = [
            '[data-testid="minSip"]',
            '.min-sip',
            '[class*="sip"]',
            'td:contains("SIP")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_riskometer(self, soup: BeautifulSoup) -> str:
        """Extract riskometer classification."""
        selectors = [
            '[data-testid="riskometer"]',
            '.riskometer',
            '[class*="risk"]',
            'td:contains("Risk")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_benchmark(self, soup: BeautifulSoup) -> str:
        """Extract benchmark index."""
        selectors = [
            '[data-testid="benchmark"]',
            '.benchmark',
            '[class*="benchmark"]',
            'td:contains("Benchmark")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_nav(self, soup: BeautifulSoup) -> str:
        """Extract NAV value."""
        selectors = [
            '[data-testid="nav"]',
            '.nav-value',
            '[class*="nav"]',
            'td:contains("NAV")'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_returns(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract return data."""
        returns = {}
        
        # Look for return periods (1Y, 3Y, 5Y)
        periods = ['1Y', '3Y', '5Y']
        for period in periods:
            selector = f'[data-testid="return{period}"], .return-{period.lower()}, td:contains("{period}")'
            element = soup.select_one(selector)
            if element:
                returns[period] = element.get_text(strip=True)
        
        return returns if returns else {"1Y": "Not available", "3Y": "Not available", "5Y": "Not available"}
    
    def _extract_asset_allocation(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract asset allocation data."""
        allocation = {}
        
        # Look for common asset classes
        asset_classes = ['equity', 'debt', 'cash', 'others']
        for asset_class in asset_classes:
            selector = f'[data-testid="{asset_class}"], .{asset_class}-allocation, td:contains("{asset_class.title()}")'
            element = soup.select_one(selector)
            if element:
                allocation[asset_class] = element.get_text(strip=True)
        
        return allocation if allocation else {"equity": "Not available", "debt": "Not available"}
    
    def _extract_fund_type(self, soup: BeautifulSoup) -> str:
        """Extract fund type (Direct, Regular, etc.)."""
        selectors = [
            '[data-testid="fundType"]',
            '.fund-type',
            '[class*="fund-type"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract fund category."""
        selectors = [
            '[data-testid="category"]',
            '.category',
            '[class*="category"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return "Not available"
    
    def scrape_all_funds(self) -> List[Dict[str, Any]]:
        """
        Scrape all configured fund URLs.
        """
        all_fund_data = []
        
        for fund_url in settings.fund_urls:
            logger.info(f"Processing fund: {fund_url}")
            fund_data = self.scrape_fund_page(fund_url)
            
            if fund_data and 'error' not in fund_data:
                all_fund_data.append(fund_data)
            else:
                logger.error(f"Failed to scrape fund: {fund_url}")
            
            # Respect rate limiting
            time.sleep(self.delay)
        
        logger.info(f"Successfully scraped {len(all_fund_data)} funds")
        return all_fund_data
    
    def test_scraper(self) -> bool:
        """
        Test scraper functionality.
        """
        try:
            if not settings.fund_urls:
                logger.error("No fund URLs configured")
                return False
            
            test_url = settings.fund_urls[0]
            test_data = self.scrape_fund_page(test_url)
            
            if test_data and 'fund_name' in test_data:
                logger.info("Scraper test successful")
                return True
            else:
                logger.error("Scraper test failed - no data extracted")
                return False
                
        except Exception as e:
            logger.error(f"Scraper test failed: {e}")
            return False

# Initialize global scraper
groww_scraper = GrowwScraper()

if __name__ == "__main__":
    # Test scraper
    groww_scraper.test_scraper()
