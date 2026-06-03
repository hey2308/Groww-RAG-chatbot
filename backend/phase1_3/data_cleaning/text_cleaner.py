"""
Phase 1.3.2 - Data Cleaning and Preprocessing
Text Cleaning Module for HTML Content Normalization
"""

import logging
import re
import unicodedata
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Advanced text cleaning for scraped HTML content.
    Handles HTML cleaning, text normalization, and content extraction.
    """
    
    def __init__(self):
        """
        Initialize text cleaner with cleaning rules and patterns.
        """
        self.cleaning_rules = self._initialize_cleaning_rules()
        self.html_patterns = self._initialize_html_patterns()
        self.text_patterns = self._initialize_text_patterns()
        
        logger.info("Text cleaner initialized")
    
    def _initialize_cleaning_rules(self) -> Dict[str, Any]:
        """
        Initialize cleaning rules for different content types.
        """
        return {
            'html_elements': {
                'remove_tags': [
                    'script', 'style', 'nav', 'header', 'footer', 
                    'aside', 'iframe', 'noscript', 'meta'
                ],
                'keep_attributes': ['href', 'src', 'alt', 'title'],
                'empty_threshold': 10  # Remove elements with less than 10 chars
            },
            'text_normalization': {
                'whitespace_normalization': True,
                'unicode_normalization': True,
                'case_handling': 'preserve',  # preserve original case
                'punctuation_handling': 'normalize'
            },
            'content_filters': {
                'min_text_length': 10,
                'max_repeating_chars': 3,
                'remove_special_chars': True,
                'normalize_numbers': True
            }
        }
    
    def _initialize_html_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize regex patterns for HTML cleaning.
        """
        return {
            'html_comments': r'<!--.*?-->',
            'html_entities': r'&[a-zA-Z0-9#]+;',
            'whitespace': r'\s+',
            'line_breaks': r'[\r\n]+',
            'extra_spaces': r' {2,}',
            'non_printable': r'[^\x20-\x7E]',
            'repeating_chars': r'(.)\1{3,}',
            'url_patterns': r'https?://[^\s<>"\'\)]+',
            'email_patterns': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
    
    def _initialize_text_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize regex patterns for text cleaning.
        """
        return {
            'currency_symbols': r'[₹$Rs$INR]',
            'percentage_symbols': r'%',
            'number_formats': r'\d+(?:,\d{3})*(?:\.\d{2})?',
            'date_formats': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            'special_chars': r'[^\w\s\-.,%₹()]',
            'multiple_spaces': r' {2,}',
            'repeating_words': r'\b(\w+)(?:\s+\1){2,}\b',
            'junk_text': r'^(?:Loading|Please wait|404|Error|Access denied).*'
        }
    
    def clean_html_content(self, soup: BeautifulSoup, url: str = None) -> Dict[str, Any]:
        """
        Clean HTML content by removing unwanted elements and normalizing structure.
        """
        logger.info(f"Cleaning HTML content for: {url or 'unknown'}")
        
        if soup is None:
            logger.error("clean_html_content received None soup object")
            return {
                'original_length': 0,
                'cleaned_length': 0,
                'error': 'soup is None',
                'cleaning_score': 0.0
            }
        
        cleaning_result = {
            'original_length': len(str(soup)),
            'cleaned_length': 0,
            'removed_elements': [],
            'cleaning_actions': [],
            'cleaned_content': None,
            'cleaning_score': 0.0
        }
        
        try:
            # Step 1: Remove unwanted HTML elements
            cleaned_soup = self._remove_unwanted_elements(soup)
            cleaning_result['removed_elements'] = self._get_removed_elements_info(soup, cleaned_soup)
            
            # Step 2: Clean attributes
            cleaned_soup = self._clean_attributes(cleaned_soup)
            cleaning_result['cleaning_actions'].append('attributes_cleaned')
            
            # Step 3: Extract and clean text content
            text_content = self._extract_text_content(cleaned_soup)
            cleaned_text = self._clean_text_content(text_content)
            
            # Step 4: Normalize text
            normalized_text = self._normalize_text(cleaned_text)
            
            cleaning_result['cleaned_content'] = normalized_text
            cleaning_result['cleaned_length'] = len(normalized_text)
            cleaning_result['cleaning_score'] = self._calculate_cleaning_score(cleaning_result)
            
            logger.info(f"HTML cleaning completed. Score: {cleaning_result['cleaning_score']:.1f}")
            return cleaning_result
            
        except Exception as e:
            logger.error(f"Error cleaning HTML content: {e}")
            return {
                'original_length': len(str(soup)),
                'cleaned_length': 0,
                'error': str(e),
                'cleaning_score': 0.0
            }
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Remove unwanted HTML elements from soup.
        """
        unwanted_tags = self.cleaning_rules['html_elements']['remove_tags']
        
        for tag in unwanted_tags:
            elements = soup.find_all(tag)
            for element in elements:
                element.decompose()
        
        return soup
    
    def _clean_attributes(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Clean HTML attributes, keeping only essential ones.
        """
        keep_attributes = self.cleaning_rules['html_elements']['keep_attributes']
        
        for tag in soup.find_all(True):
            if tag.attrs:
                # Keep only specified attributes
                cleaned_attrs = {}
                for attr, value in tag.attrs.items():
                    if attr.lower() in keep_attributes:
                        cleaned_attrs[attr] = value
                
                tag.attrs = cleaned_attrs
        
        return soup
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract text content from cleaned HTML.
        """
        # Remove script and style content that might remain
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        return text
    
    def _clean_text_content(self, text: str) -> str:
        """
        Clean text content using various patterns.
        """
        if not text:
            return ""
        
        # Apply text cleaning patterns
        cleaned_text = text
        
        # Remove HTML comments
        cleaned_text = re.sub(self.html_patterns['html_comments'], '', cleaned_text)
        
        # Remove HTML entities
        cleaned_text = re.sub(self.html_patterns['html_entities'], ' ', cleaned_text)
        
        # Remove junk text patterns
        cleaned_text = re.sub(self.text_patterns['junk_text'], '', cleaned_text)
        
        # Remove email addresses (privacy protection)
        cleaned_text = re.sub(self.html_patterns['email_patterns'], '[EMAIL]', cleaned_text)
        
        # Remove URLs (might be navigation links)
        cleaned_text = re.sub(self.html_patterns['url_patterns'], '[URL]', cleaned_text)
        
        return cleaned_text.strip()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text content.
        """
        if not text:
            return ""
        
        normalized_text = text
        
        # Unicode normalization
        if self.cleaning_rules['text_normalization']['unicode_normalization']:
            normalized_text = unicodedata.normalize('NFKC', normalized_text)
        
        # Whitespace normalization
        if self.cleaning_rules['text_normalization']['whitespace_normalization']:
            # Replace multiple spaces with single space
            normalized_text = re.sub(self.html_patterns['multiple_spaces'], ' ', normalized_text)
            # Normalize line breaks
            normalized_text = re.sub(self.html_patterns['line_breaks'], ' ', normalized_text)
        
        # Remove repeating characters
        if self.cleaning_rules['content_filters']['remove_special_chars']:
            # Remove excessive repeating characters
            normalized_text = re.sub(self.html_patterns['repeating_chars'], r'\1', normalized_text)
        
        # Remove repeating words
        normalized_text = re.sub(self.text_patterns['repeating_words'], r'\1', normalized_text)
        
        return normalized_text.strip()
    
    def _get_removed_elements_info(self, original_soup: BeautifulSoup, cleaned_soup: BeautifulSoup) -> List[str]:
        """
        Get information about removed elements.
        """
        removed_info = []
        unwanted_tags = self.cleaning_rules['html_elements']['remove_tags']
        
        for tag in unwanted_tags:
            original_count = len(original_soup.find_all(tag))
            cleaned_count = len(cleaned_soup.find_all(tag))
            
            if original_count > cleaned_count:
                removed_info.append(f"Removed {original_count - cleaned_count} {tag} elements")
        
        return removed_info
    
    def _calculate_cleaning_score(self, cleaning_result: Dict[str, Any]) -> float:
        """
        Calculate cleaning quality score.
        """
        original_length = cleaning_result.get('original_length', 0)
        cleaned_length = cleaning_result.get('cleaned_length', 0)
        
        if original_length == 0:
            return 0.0
        
        # Calculate reduction percentage (should be reasonable)
        reduction_percentage = ((original_length - cleaned_length) / original_length) * 100
        
        # Score based on reasonable reduction (10-50% is good)
        if 10 <= reduction_percentage <= 50:
            score = 100.0 - (abs(reduction_percentage - 30) * 2)  # Peak at 30% reduction
        elif reduction_percentage < 10:
            score = 70.0  # Not enough cleaning
        else:
            score = 50.0  # Too much cleaning
        
        return max(0.0, min(100.0, score))
    
    def clean_fund_data(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean all text fields in fund data.
        """
        logger.info(f"Cleaning fund data: {fund_data.get('fund_name', 'Unknown')}")
        
        cleaned_data = fund_data.copy()
        cleaning_summary = {
            'fields_cleaned': 0,
            'cleaning_actions': [],
            'overall_score': 0.0
        }
        
        # Text fields that need cleaning
        text_fields = [
            'fund_name', 'fund_type', 'category', 'riskometer', 'benchmark',
            'expense_ratio', 'exit_load', 'nav', 'min_sip'
        ]
        
        for field in text_fields:
            if field in cleaned_data and cleaned_data[field]:
                original_value = str(cleaned_data[field])
                
                # Skip if already "Not available"
                if original_value == "Not available":
                    continue
                
                # Apply text cleaning
                cleaned_value = self._apply_field_cleaning(field, original_value)
                cleaned_data[field] = cleaned_value
                
                if original_value != cleaned_value:
                    cleaning_summary['fields_cleaned'] += 1
                    cleaning_summary['cleaning_actions'].append(f"Cleaned {field}")
        
        # Clean complex fields
        if 'returns' in cleaned_data and isinstance(cleaned_data['returns'], dict):
            cleaned_returns = {}
            for period, value in cleaned_data['returns'].items():
                if value != "Not available":
                    cleaned_returns[period] = self._apply_field_cleaning(f"returns_{period}", value)
                else:
                    cleaned_returns[period] = value
            
            cleaned_data['returns'] = cleaned_returns
        
        if 'asset_allocation' in cleaned_data and isinstance(cleaned_data['asset_allocation'], dict):
            cleaned_allocation = {}
            for asset_type, value in cleaned_data['asset_allocation'].items():
                if value != "Not available":
                    cleaned_allocation[asset_type] = self._apply_field_cleaning(f"allocation_{asset_type}", value)
                else:
                    cleaned_allocation[asset_type] = value
            
            cleaned_data['asset_allocation'] = cleaned_allocation
        
        # Clean fund details
        if 'fund_details' in cleaned_data and isinstance(cleaned_data['fund_details'], dict):
            cleaned_details = {}
            for detail_key, value in cleaned_data['fund_details'].items():
                if isinstance(value, str) and value != "Not available":
                    cleaned_details[detail_key] = self._apply_field_cleaning(f"detail_{detail_key}", value)
                else:
                    cleaned_details[detail_key] = value
            
            cleaned_data['fund_details'] = cleaned_details
        
        # Calculate overall cleaning score
        cleaning_summary['overall_score'] = self._calculate_overall_cleaning_score(cleaning_summary)
        
        logger.info(f"Fund data cleaning completed. Fields cleaned: {cleaning_summary['fields_cleaned']}")
        
        return cleaned_data
    
    def _apply_field_cleaning(self, field_name: str, value: str) -> str:
        """
        Apply field-specific cleaning rules.
        """
        if not value or value == "Not available":
            return value
        
        cleaned_value = value.strip()
        
        # Field-specific cleaning
        if 'name' in field_name.lower():
            # Fund names should preserve case but normalize spacing
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            cleaned_value = re.sub(r'\s*-\s*', ' - ', cleaned_value)
        
        elif 'ratio' in field_name.lower() or 'return' in field_name.lower():
            # Percentages: normalize format
            percentage_match = re.search(r'(\d+\.?\d*)\s*%?', cleaned_value)
            if percentage_match:
                cleaned_value = f"{percentage_match.group(1)}%"
        
        elif 'sip' in field_name.lower() or 'nav' in field_name.lower() or 'aum' in field_name.lower():
            # Currency: normalize format
            currency_match = re.search(r'[₹$Rs$INR]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', cleaned_value)
            if currency_match:
                cleaned_value = f"₹{currency_match.group(1)}"
        
        elif 'riskometer' in field_name.lower() or 'category' in field_name.lower():
            # Categories: normalize case and spacing
            cleaned_value = cleaned_value.title().strip()
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
        
        # General text cleaning
        cleaned_value = self._normalize_text(cleaned_value)
        
        # Remove special characters but keep essential ones
        cleaned_value = re.sub(self.text_patterns['special_chars'], '', cleaned_value)
        
        return cleaned_value.strip()
    
    def _calculate_overall_cleaning_score(self, cleaning_summary: Dict[str, Any]) -> float:
        """
        Calculate overall cleaning score.
        """
        fields_cleaned = cleaning_summary.get('fields_cleaned', 0)
        total_text_fields = 12  # Approximate number of text fields
        
        if total_text_fields == 0:
            return 0.0
        
        # Score based on proportion of fields cleaned
        cleaning_ratio = (fields_cleaned / total_text_fields) * 100
        
        # Optimal cleaning is around 20-40% of fields
        if 20 <= cleaning_ratio <= 40:
            score = 100.0
        elif cleaning_ratio < 20:
            score = 70.0  # Not enough cleaning
        else:
            score = 60.0  # Too much cleaning
        
        return score
    
    def validate_cleaned_data(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate cleaned data for quality and consistency.
        """
        validation_result = {
            'validation_timestamp': None,
            'overall_status': 'passed',
            'field_validations': {},
            'validation_score': 0.0,
            'issues': []
        }
        
        try:
            # Check for empty critical fields
            critical_fields = ['fund_name', 'source_url']
            for field in critical_fields:
                if field not in cleaned_data or not cleaned_data[field]:
                    validation_result['issues'].append(f'Critical field {field} is missing')
                    validation_result['overall_status'] = 'failed'
            
            # Check for data consistency
            if 'returns' in cleaned_data:
                returns_validation = self._validate_returns_consistency(cleaned_data['returns'])
                validation_result['field_validations']['returns'] = returns_validation
            
            # Check for reasonable data ranges
            range_validation = self._validate_data_ranges(cleaned_data)
            validation_result['field_validations'].update(range_validation)
            
            # Calculate validation score
            validation_result['validation_score'] = self._calculate_validation_score(validation_result)
            
            validation_result['validation_timestamp'] = self._get_timestamp()
            
        except Exception as e:
            logger.error(f"Error validating cleaned data: {e}")
            validation_result['overall_status'] = 'error'
            validation_result['error'] = str(e)
        
        return validation_result
    
    def _validate_returns_consistency(self, returns_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate returns data for consistency.
        """
        validation = {
            'status': 'passed',
            'issues': [],
            'consistency_score': 100.0
        }
        
        if not isinstance(returns_data, dict):
            validation['status'] = 'failed'
            validation['issues'].append('Returns data is not a dictionary')
            return validation
        
        # Check for consistent percentage format
        for period, value in returns_data.items():
            if value != "Not available":
                if not re.match(r'^\d+\.?\d*%?$', value):
                    validation['issues'].append(f'Return {period} has inconsistent format: {value}')
                    validation['status'] = 'warning'
        
        # Check for reasonable return ranges
        for period, value in returns_data.items():
            if value != "Not available":
                percentage_match = re.search(r'(\d+\.?\d*)', value)
                if percentage_match:
                    return_value = float(percentage_match.group(1))
                    if abs(return_value) > 100:  # Returns over 100% are suspicious
                        validation['issues'].append(f'Return {period} seems unrealistic: {value}')
                        validation['status'] = 'warning'
        
        if validation['issues']:
            validation['consistency_score'] = max(0, 100 - len(validation['issues']) * 20)
        
        return validation
    
    def _validate_data_ranges(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data ranges for reasonableness.
        """
        validations = {}
        
        # Validate expense ratio
        if 'expense_ratio' in data and data['expense_ratio'] != "Not available":
            ratio_match = re.search(r'(\d+\.?\d*)', data['expense_ratio'])
            if ratio_match:
                ratio_value = float(ratio_match.group(1))
                if ratio_value < 0 or ratio_value > 10:
                    validations['expense_ratio'] = {
                        'status': 'warning',
                        'message': f'Expense ratio {ratio_value}% seems unusual'
                    }
                else:
                    validations['expense_ratio'] = {'status': 'passed'}
        
        # Validate SIP amount
        if 'min_sip' in data and data['min_sip'] != "Not available":
            sip_match = re.search(r'(\d+(?:,\d{3})*)', data['min_sip'].replace('₹', ''))
            if sip_match:
                sip_value = float(sip_match.group(1).replace(',', ''))
                if sip_value < 100 or sip_value > 50000:
                    validations['min_sip'] = {
                        'status': 'warning',
                        'message': f'SIP amount {sip_value} seems unusual'
                    }
                else:
                    validations['min_sip'] = {'status': 'passed'}
        
        return validations
    
    def _calculate_validation_score(self, validation_result: Dict[str, Any]) -> float:
        """
        Calculate overall validation score.
        """
        if validation_result.get('overall_status') == 'failed':
            return 0.0
        
        issues_count = len(validation_result.get('issues', []))
        field_validations = validation_result.get('field_validations', {})
        
        # Calculate scores from field validations
        validation_scores = []
        for field_name, validation in field_validations.items():
            if isinstance(validation, dict):
                if 'consistency_score' in validation:
                    validation_scores.append(validation['consistency_score'])
                elif 'status' in validation:
                    score = 100 if validation['status'] == 'passed' else 50
                    validation_scores.append(score)
        
        # Calculate overall score
        if validation_scores:
            avg_field_score = sum(validation_scores) / len(validation_scores)
        else:
            avg_field_score = 100.0
        
        # Penalize for issues
        final_score = avg_field_score - (issues_count * 10)
        
        return max(0.0, min(100.0, final_score))
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp.
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """
        Get text cleaner statistics.
        """
        return {
            'cleaning_rules_count': len(self.cleaning_rules),
            'html_patterns_count': len(self.html_patterns),
            'text_patterns_count': len(self.text_patterns),
            'cleaner_version': '1.0',
            'supported_fields': [
                'fund_name', 'fund_type', 'category', 'riskometer', 'benchmark',
                'expense_ratio', 'exit_load', 'nav', 'min_sip', 'returns',
                'asset_allocation', 'fund_details'
            ]
        }

# Global text cleaner instance
text_cleaner = TextCleaner()

if __name__ == "__main__":
    # Test text cleaner
    print("🧹 Testing Text Cleaner")
    print("=" * 50)
    
    # Test HTML cleaning
    test_html = """
    <html>
        <head><title>  HDFC Large Cap Fund  </title></head>
        <body>
            <script>var test = 'script';</script>
            <style>.test {color: red;}</style>
            <h1>  HDFC Large Cap Fund Direct Growth  </h1>
            <div>Expense Ratio:  1.25%  </div>
            <div>Min SIP:  ₹500  </div>
            <div>1Y Return: 12.5%   </div>
            <div>Contact: test@example.com</div>
            <nav>Navigation menu</nav>
        </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(test_html, 'html.parser')
    
    # Test HTML cleaning
    result = text_cleaner.clean_html_content(soup, "https://test.com")
    
    print(f"HTML Cleaning Result:")
    print(f"Original Length: {result['original_length']}")
    print(f"Cleaned Length: {result['cleaned_length']}")
    print(f"Cleaning Score: {result['cleaning_score']:.1f}")
    print(f"Removed Elements: {result['removed_elements']}")
    print(f"Cleaned Content: {result['cleaned_content'][:100]}...")
    
    # Test fund data cleaning
    test_fund_data = {
        'fund_name': '  HDFC Large Cap Fund Direct Growth  ',
        'expense_ratio': '  1.25%  ',
        'min_sip': ' ₹500  ',
        'returns': {
            '1Y': ' 12.5%   ',
            '3Y': '15.2%',
            '5Y': ' 14.8%   '
        },
        'asset_allocation': {
            'equity': ' 85.2%  ',
            'debt': ' 10.5%  '
        }
    }
    
    cleaned_fund_data = text_cleaner.clean_fund_data(test_fund_data)
    
    print(f"\nFund Data Cleaning Result:")
    print(f"Fund Name: '{cleaned_fund_data['fund_name']}'")
    print(f"Expense Ratio: '{cleaned_fund_data['expense_ratio']}'")
    print(f"Min SIP: '{cleaned_fund_data['min_sip']}'")
    print(f"Returns: {cleaned_fund_data['returns']}")
    print(f"Asset Allocation: {cleaned_fund_data['asset_allocation']}")
    
    # Test validation
    validation = text_cleaner.validate_cleaned_data(cleaned_fund_data)
    print(f"\nValidation Result:")
    print(f"Overall Status: {validation['overall_status']}")
    print(f"Validation Score: {validation['validation_score']:.1f}")
    
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  • {issue}")
    
    # Show stats
    stats = text_cleaner.get_cleaning_stats()
    print(f"\nCleaner Stats:")
    print(f"Rules Count: {stats['cleaning_rules_count']}")
    print(f"Patterns Count: {stats['html_patterns_count']}")
    print(f"Supported Fields: {stats['supported_fields']}")
    
    print("\n✅ Text cleaner testing completed")
