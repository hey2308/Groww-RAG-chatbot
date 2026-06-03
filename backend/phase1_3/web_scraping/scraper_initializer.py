"""
Phase 1.3.1 - Web Scraping Implementation
Scraper Initializer and Configuration Management
"""

import logging
import time
import random
from typing import Dict, List, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from bs4 import BeautifulSoup
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """
    Configuration for web scraper with rate limiting and user agents.
    """
    base_delay: float = 2.0
    max_retries: int = 3
    timeout: int = 30
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]

class EnhancedScraper:
    """
    Enhanced web scraper with rate limiting, user agent rotation, and Selenium fallback.
    """
    
    def __init__(self, config: ScraperConfig = None):
        """
        Initialize scraper with configuration.
        """
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.driver = None
        self.request_count = 0
        self.last_request_time = 0
        
        logger.info("Enhanced scraper initialized")
        logger.info(f"Configuration: delay={self.config.base_delay}s, retries={self.config.max_retries}")
    
    def initialize_scraper(self) -> bool:
        """
        Initialize scraper components and test connectivity.
        """
        try:
            logger.info("Initializing enhanced web scraper...")
            
            # Test basic connectivity
            test_response = self.session.get(
                settings.groww_base_url,
                timeout=10,
                headers={'User-Agent': self._get_random_user_agent()}
            )
            
            if test_response.status_code == 200:
                logger.info("✅ Basic connectivity test passed")
                return True
            else:
                logger.error(f"❌ Connectivity test failed: {test_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Scraper initialization failed: {e}")
            return False
    
    def setup_selenium_driver(self) -> bool:
        """
        Setup Selenium WebDriver with optimized options.
        """
        try:
            logger.info("Setting up Selenium WebDriver...")
            
            options = Options()
            
            # Performance optimizations
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            # NOTE: Do NOT disable JavaScript — Groww is a React SPA and
            # requires JS to render NAV, expense ratio, and all fund data.

            # Anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # User agent
            options.add_argument(f'--user-agent={self._get_random_user_agent()}')

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)
            
            logger.info("✅ Selenium WebDriver setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium setup failed: {e}")
            return False
    
    def _get_random_user_agent(self) -> str:
        """
        Get random user agent from configuration.
        """
        return random.choice(self.config.user_agents)
    
    def _apply_rate_limiting(self):
        """
        Apply rate limiting between requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.config.base_delay:
            sleep_time = self.config.base_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """
        Scrape URL using requests (primary method).
        """
        self._apply_rate_limiting()
        
        try:
            logger.info(f"Scraping with requests: {url}")
            
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, timeout=self.config.timeout, headers=headers)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'success': True,
                'method': 'requests',
                'status_code': response.status_code,
                'content': soup,
                'url': url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'request_id': self.request_count
            }
            
        except Exception as e:
            logger.warning(f"❌ Requests scraping failed: {e}")
            return {
                'success': False,
                'method': 'requests',
                'error': str(e),
                'url': url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'request_id': self.request_count
            }
    
    def scrape_with_selenium(self, url: str) -> Dict[str, Any]:
        """
        Scrape URL using Selenium (fallback method).
        """
        if not self.driver:
            if not self.setup_selenium_driver():
                return self._create_error_result(url, 'selenium', 'Failed to setup driver')
        
        self._apply_rate_limiting()
        
        try:
            logger.info(f"Scraping with Selenium: {url}")
            
            # Navigate to URL
            self.driver.get(url)

            # Wait for the React app to render fund data.
            # Groww renders key metrics into elements that contain ₹ or % signs.
            # We wait up to 15 seconds for any element containing a ₹ sign to appear.
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: '₹' in d.page_source or 'NAV' in d.page_source
                )
            except TimeoutException:
                logger.warning("Timed out waiting for fund data; proceeding with available content")

            # Extra wait to let lazy-loaded sections finish rendering
            time.sleep(4)

            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            return {
                'success': True,
                'method': 'selenium',
                'status_code': 200,  # Selenium doesn't provide status codes easily
                'content': soup,
                'url': url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'request_id': self.request_count
            }
            
        except TimeoutException as e:
            logger.warning(f"❌ Selenium timeout: {e}")
            return self._create_error_result(url, 'selenium', f'Timeout: {e}')
        except WebDriverException as e:
            logger.warning(f"❌ Selenium WebDriver error: {e}")
            return self._create_error_result(url, 'selenium', f'WebDriver error: {e}')
        except Exception as e:
            logger.warning(f"❌ Selenium scraping failed: {e}")
            return self._create_error_result(url, 'selenium', str(e))
    
    def _create_error_result(self, url: str, method: str, error: str) -> Dict[str, Any]:
        """
        Create standardized error result.
        """
        return {
            'success': False,
            'method': method,
            'error': error,
            'url': url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'request_id': self.request_count
        }
    
    def scrape_with_retry(self, url: str) -> Dict[str, Any]:
        """
        Scrape URL with retry logic and fallback.
        """
        logger.info(f"Starting scrape with retry for: {url}")
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # First attempt with requests (faster)
                if attempt == 0:
                    result = self.scrape_with_requests(url)
                    if result['success']:
                        logger.info(f"✅ Requests scraping successful on attempt {attempt + 1}")
                        return result
                    else:
                        last_error = result.get('error', 'Unknown error')
                        logger.warning(f"⚠️ Requests attempt {attempt + 1} failed: {last_error}")
                
                # Fallback to Selenium for subsequent attempts or if requests fails
                else:
                    result = self.scrape_with_selenium(url)
                    if result['success']:
                        logger.info(f"✅ Selenium scraping successful on attempt {attempt + 1}")
                        return result
                    else:
                        last_error = result.get('error', 'Unknown error')
                        logger.warning(f"⚠️ Selenium attempt {attempt + 1} failed: {last_error}")
                
                # Exponential backoff
                if attempt < self.config.max_retries - 1:
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {backoff_time:.2f}s...")
                    time.sleep(backoff_time)
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Attempt {attempt + 1} failed with exception: {e}")
        
        # All attempts failed
        logger.error(f"❌ All {self.config.max_retries} attempts failed for: {url}")
        return self._create_error_result(url, 'mixed', f'All attempts failed. Last error: {last_error}')
    
    def validate_scraping_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate scraping result for quality and completeness.
        """
        if not result.get('success', False):
            return False
        
        content = result.get('content')
        if not content:
            logger.warning("❌ Scraping result has no content")
            return False
        
        # Check for common error indicators
        if isinstance(content, BeautifulSoup):
            text = content.get_text().lower()
            error_indicators = [
                '404 not found',
                'page not found',
                'access denied',
                'rate limit',
                'captcha',
                'bot detection'
            ]
            
            for indicator in error_indicators:
                if indicator in text:
                    logger.warning(f"❌ Error indicator found in content: {indicator}")
                    return False
            
            # Check minimum content length
            if len(text) < 100:
                logger.warning("❌ Content too short (less than 100 characters)")
                return False
        
        return True
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics and performance metrics.
        """
        return {
            'total_requests': self.request_count,
            'last_request_time': self.last_request_time,
            'config': {
                'base_delay': self.config.base_delay,
                'max_retries': self.config.max_retries,
                'timeout': self.config.timeout
            },
            'selenium_available': self.driver is not None
        }
    
    def cleanup(self):
        """
        Cleanup resources and close connections.
        """
        try:
            if self.driver:
                self.driver.quit()
                logger.info("✅ Selenium WebDriver closed")
            
            if self.session:
                self.session.close()
                logger.info("✅ Requests session closed")
                
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

# Global scraper instance
enhanced_scraper = EnhancedScraper()

if __name__ == "__main__":
    # Test the enhanced scraper
    scraper = EnhancedScraper()
    
    try:
        # Initialize scraper
        if scraper.initialize_scraper():
            print("✅ Scraper initialization successful")
            
            # Test scraping
            test_url = settings.fund_urls[0] if settings.fund_urls else "https://groww.in"
            result = scraper.scrape_with_retry(test_url)
            
            print(f"\nScraping Result:")
            print(f"Success: {result.get('success', False)}")
            print(f"Method: {result.get('method', 'unknown')}")
            print(f"URL: {result.get('url', 'unknown')}")
            
            if result.get('success'):
                content = result.get('content')
                if content and hasattr(content, 'title'):
                    print(f"Title: {content.title.string if content.title else 'No title'}")
                print(f"Content length: {len(str(content))} characters")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Show stats
            stats = scraper.get_scraping_stats()
            print(f"\nScraping Stats:")
            print(f"Total requests: {stats['total_requests']}")
            print(f"Selenium available: {stats['selenium_available']}")
        
        else:
            print("❌ Scraper initialization failed")
            
    finally:
        scraper.cleanup()
