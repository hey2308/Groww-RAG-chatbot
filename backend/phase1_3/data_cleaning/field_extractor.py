"""
Phase 1.3.2 - Data Cleaning and Preprocessing
Field Extraction Module for Structured Data Processing
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from text_cleaner import text_cleaner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractionRule:
    """
    Rule for extracting specific field types.
    """
    field_name: str
    patterns: List[str]
    data_type: str
    required: bool = False
    validation_func: Optional[str] = None
    default_value: str = "Not available"

class FieldExtractor:
    """
    Advanced field extractor for structured fund data.
    Handles various data types with validation and normalization.
    """
    
    def __init__(self):
        """
        Initialize field extractor with extraction rules.
        """
        self.extraction_rules = self._initialize_extraction_rules()
        self.text_cleaner = text_cleaner
        self.extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'field_stats': {}
        }
        
        logger.info("Field extractor initialized")
    
    def _initialize_extraction_rules(self) -> Dict[str, ExtractionRule]:
        """
        Initialize rules for extracting different field types.
        """
        return {
            'fund_name': ExtractionRule(
                field_name='fund_name',
                patterns=[
                    r'<h1[^>]*>([^<]+)</h1>',
                    r'<title[^>]*>([^<]+)</title>',
                    r'fund\s*name[:\s]*([^\n]+)',
                    r'scheme\s*name[:\s]*([^\n]+)'
                ],
                data_type='text',
                required=True,
                validation_func='validate_fund_name'
            ),
            
            'fund_type': ExtractionRule(
                field_name='fund_type',
                patterns=[
                    r'(direct|regular)\s*(growth|dividend)',
                    r'type[:\s]*([^\n]+)',
                    r'plan[:\s]*([^\n]+)'
                ],
                data_type='enum',
                validation_func='validate_fund_type',
                default_value='Not available'
            ),
            
            'category': ExtractionRule(
                field_name='category',
                patterns=[
                    r'(large|mid|small)\s*cap',
                    r'equity',
                    r'focused',
                    r'elss',
                    r'hybrid',
                    r'debt',
                    r'category[:\s]*([^\n]+)'
                ],
                data_type='enum',
                validation_func='validate_category',
                default_value='Not available'
            ),
            
            'expense_ratio': ExtractionRule(
                field_name='expense_ratio',
                patterns=[
                    r'expense\s*ratio[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                    r'([0-9]+\.?[0-9]*)\s*%?',
                    r' TER[:\s]*([0-9]+\.?[0-9]*)\s*%?'
                ],
                data_type='percentage',
                required=False,
                validation_func='validate_percentage',
                default_value='Not available'
            ),
            
            'exit_load': ExtractionRule(
                field_name='exit_load',
                patterns=[
                    r'exit\s*load[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                    r'([0-9]+\.?[0-9]*)\s*%?',
                    r'no\s*exit\s*load',
                    r'nil\s*exit\s*load'
                ],
                data_type='percentage_or_text',
                required=False,
                validation_func='validate_exit_load',
                default_value='Not available'
            ),
            
            'min_sip': ExtractionRule(
                field_name='min_sip',
                patterns=[
                    r'min(?:imum)?\s*sip[:\s]*₹?\s*([0-9,]+)',
                    r'sip[:\s]*₹?\s*([0-9,]+)',
                    r'₹?\s*([0-9,]+)',
                    r'([0-9,]+)'
                ],
                data_type='currency',
                required=False,
                validation_func='validate_currency',
                default_value='Not available'
            ),
            
            'nav': ExtractionRule(
                field_name='nav',
                patterns=[
                    r'nav[:\s]*₹?\s*([0-9,]+)',
                    r'net\s*asset\s*value[:\s]*₹?\s*([0-9,]+)',
                    r'₹?\s*([0-9,]+)',
                    r'([0-9,]+)'
                ],
                data_type='currency',
                required=False,
                validation_func='validate_currency',
                default_value='Not available'
            ),
            
            'returns': ExtractionRule(
                field_name='returns',
                patterns={
                    '1Y': [
                        r'1\s*year[:\s]*return[:\s]*([0-9-]+\.?[0-9]*)\s*%?',
                        r'1Y[:\s]*([0-9-]+\.?[0-9]*)\s*%?'
                    ],
                    '3Y': [
                        r'3\s*year[:\s]*return[:\s]*([0-9-]+\.?[0-9]*)\s*%?',
                        r'3Y[:\s]*([0-9-]+\.?[0-9]*)\s*%?'
                    ],
                    '5Y': [
                        r'5\s*year[:\s]*return[:\s]*([0-9-]+\.?[0-9]*)\s*%?',
                        r'5Y[:\s]*([0-9-]+\.?[0-9]*)\s*%?'
                    ]
                },
                data_type='percentage_map',
                required=False,
                validation_func='validate_returns',
                default_value={'1Y': 'Not available', '3Y': 'Not available', '5Y': 'Not available'}
            ),
            
            'riskometer': ExtractionRule(
                field_name='riskometer',
                patterns=[
                    r'risk\s*ometer[:\s]*([a-z\s]+)',
                    r'risk\s*level[:\s]*([a-z\s]+)',
                    r'([a-z\s]+)'
                ],
                data_type='enum',
                required=False,
                validation_func='validate_riskometer',
                default_value='Not available'
            ),
            
            'benchmark': ExtractionRule(
                field_name='benchmark',
                patterns=[
                    r'benchmark[:\s]*([^\n]+)',
                    r'index[:\s]*([^\n]+)',
                    r'compared\s*to[:\s]*([^\n]+)'
                ],
                data_type='text',
                required=False,
                validation_func='validate_text',
                default_value='Not available'
            ),
            
            'asset_allocation': ExtractionRule(
                field_name='asset_allocation',
                patterns={
                    'equity': [
                        r'equity[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                        r'equity[:\s]*₹?\s*([0-9,]+)'
                    ],
                    'debt': [
                        r'debt[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                        r'debt[:\s]*₹?\s*([0-9,]+)'
                    ],
                    'cash': [
                        r'cash[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                        r'cash[:\s]*₹?\s*([0-9,]+)'
                    ],
                    'others': [
                        r'others?[:\s]*([0-9]+\.?[0-9]*)\s*%?',
                        r'others?[:\s]*₹?\s*([0-9,]+)'
                    ]
                },
                data_type='allocation_map',
                required=False,
                validation_func='validate_allocation',
                default_value={'equity': 'Not available', 'debt': 'Not available', 'cash': 'Not available', 'others': 'Not available'}
            )
        }
    
    def extract_from_text(self, text: str, url: str = None) -> Dict[str, Any]:
        """
        Extract all fields from text content.
        """
        logger.info(f"Extracting fields from text (length: {len(text)})")
        
        extraction_result = {
            'source_url': url,
            'extraction_timestamp': self._get_timestamp(),
            'raw_text_length': len(text),
            'extracted_fields': {},
            'extraction_confidence': 0.0,
            'extraction_errors': [],
            'validation_status': 'pending'
        }
        
        try:
            # Clean text first
            cleaned_text = self.text_cleaner._normalize_text(text)
            
            # Extract each field
            for field_name, rule in self.extraction_rules.items():
                try:
                    if field_name == 'returns':
                        extracted_value = self._extract_returns(cleaned_text, rule)
                    elif field_name == 'asset_allocation':
                        extracted_value = self._extract_allocation(cleaned_text, rule)
                    else:
                        extracted_value = self._extract_single_field(cleaned_text, rule)
                    
                    extraction_result['extracted_fields'][field_name] = extracted_value
                    
                except Exception as e:
                    logger.error(f"Error extracting {field_name}: {e}")
                    extraction_result['extraction_errors'].append(f'{field_name}: {str(e)}')
                    extraction_result['extracted_fields'][field_name] = rule.default_value
            
            # Calculate extraction confidence
            extraction_result['extraction_confidence'] = self._calculate_extraction_confidence(
                extraction_result['extracted_fields']
            )
            
            # Validate extracted fields
            validation_result = self._validate_extracted_fields(extraction_result['extracted_fields'])
            extraction_result['validation_status'] = validation_result['overall_status']
            extraction_result['validation_errors'] = validation_result['errors']
            
            # Update stats
            self._update_extraction_stats(extraction_result)
            
            logger.info(f"Field extraction completed. Confidence: {extraction_result['extraction_confidence']:.1f}")
            
        except Exception as e:
            logger.error(f"Critical error in field extraction: {e}")
            extraction_result['extraction_errors'].append(f'Critical: {str(e)}')
            extraction_result['validation_status'] = 'error'
        
        return extraction_result
    
    def _extract_single_field(self, text: str, rule: ExtractionRule) -> Any:
        """
        Extract a single field using its rule.
        """
        for pattern in rule.patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                
                # Clean and validate the extracted value
                cleaned_value = self._clean_extracted_value(value, rule)
                
                if self._validate_extracted_value(cleaned_value, rule):
                    return cleaned_value
        
        return rule.default_value
    
    def _extract_returns(self, text: str, rule: ExtractionRule) -> Dict[str, str]:
        """
        Extract returns data for multiple periods.
        """
        returns_data = {}
        patterns = rule.patterns
        
        for period, period_patterns in patterns.items():
            for pattern in period_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    cleaned_value = self._clean_extracted_value(f"{value}%", rule)
                    
                    if self._validate_extracted_value(cleaned_value, rule):
                        returns_data[period] = cleaned_value
                        break
            
            if period not in returns_data:
                returns_data[period] = rule.default_value
        
        return returns_data
    
    def _extract_allocation(self, text: str, rule: ExtractionRule) -> Dict[str, str]:
        """
        Extract asset allocation data.
        """
        allocation_data = {}
        patterns = rule.patterns
        total_percentage = 0.0
        
        for asset_type, asset_patterns in patterns.items():
            for pattern in asset_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    
                    # Extract percentage if present
                    if '%' in text[match.start():match.end()]:
                        percentage_match = re.search(r'([0-9]+\.?[0-9]*)', value)
                        if percentage_match:
                            percentage_value = float(percentage_match.group(1))
                            allocation_data[asset_type] = f"{percentage_value}%"
                            total_percentage += percentage_value
                            break
                    else:
                        # Handle currency values
                        currency_value = self._clean_extracted_value(value, rule)
                        allocation_data[asset_type] = currency_value
                        break
            
            if asset_type not in allocation_data:
                allocation_data[asset_type] = rule.default_value
        
        # Validate allocation totals
        if total_percentage > 0 and total_percentage < 200:  # Allow some tolerance
            # Normalize to 100% if close
            if abs(total_percentage - 100.0) <= 5.0:
                # Scale down proportionally
                scale_factor = 100.0 / total_percentage
                for asset_type in allocation_data:
                    if '%' in allocation_data[asset_type]:
                        percentage_value = float(allocation_data[asset_type].replace('%', ''))
                        allocation_data[asset_type] = f"{percentage_value * scale_factor:.1f}%"
        
        return allocation_data
    
    def _clean_extracted_value(self, value: str, rule: ExtractionRule) -> str:
        """
        Clean extracted value based on data type.
        """
        if not value:
            return rule.default_value
        
        cleaned_value = value.strip()
        
        # Type-specific cleaning
        if rule.data_type == 'percentage':
            # Extract numeric part and add % if missing
            percentage_match = re.search(r'([0-9]+\.?[0-9]*)', cleaned_value)
            if percentage_match:
                cleaned_value = f"{percentage_match.group(1)}%"
        
        elif rule.data_type == 'currency':
            # Extract numeric part and add ₹ if missing
            currency_match = re.search(r'([0-9,]+)', cleaned_value.replace('₹', ''))
            if currency_match:
                cleaned_value = f"₹{currency_match.group(1)}"
        
        elif rule.data_type == 'text':
            # General text cleaning
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            cleaned_value = cleaned_value.strip()
        
        elif rule.data_type in ['enum', 'percentage_or_text']:
            # Enum or mixed type - just normalize
            cleaned_value = cleaned_value.title().strip()
        
        return cleaned_value
    
    def _validate_extracted_value(self, value: str, rule: ExtractionRule) -> bool:
        """
        Validate extracted value against rule constraints.
        """
        if not value or value == rule.default_value:
            return not rule.required
        
        # Type-specific validation
        if rule.validation_func:
            return getattr(self, rule.validation_func)(value)
        
        return True
    
    def validate_fund_name(self, value: str) -> bool:
        """Validate fund name."""
        return len(value) >= 3 and len(value) <= 200
    
    def validate_fund_type(self, value: str) -> bool:
        """Validate fund type."""
        valid_types = ['Direct Growth', 'Regular Growth', 'Direct Dividend', 'Regular Dividend']
        return value in valid_types or value == "Not available"
    
    def validate_category(self, value: str) -> bool:
        """Validate fund category."""
        valid_categories = ['Large Cap', 'Mid Cap', 'Small Cap', 'Equity', 'Focused', 'ELSS', 'Hybrid', 'Debt']
        return value in valid_categories or value == "Not available"
    
    def validate_percentage(self, value: str) -> bool:
        """Validate percentage value."""
        if value == "Not available":
            return True
        
        percentage_match = re.search(r'([0-9]+\.?[0-9]*)%', value)
        if percentage_match:
            percentage_value = float(percentage_match.group(1))
            return 0 <= percentage_value <= 100
        
        return False
    
    def validate_exit_load(self, value: str) -> bool:
        """Validate exit load."""
        if value == "Not available":
            return True
        
        if value.lower() in ['no exit load', 'nil exit load', '0%']:
            return True
        
        percentage_match = re.search(r'([0-9]+\.?[0-9]*)%', value)
        if percentage_match:
            percentage_value = float(percentage_match.group(1))
            return 0 <= percentage_value <= 10  # Exit loads usually don't exceed 10%
        
        return False
    
    def validate_currency(self, value: str) -> bool:
        """Validate currency value."""
        if value == "Not available":
            return True
        
        currency_match = re.search(r'₹?\s*([0-9,]+)', value)
        if currency_match:
            currency_value = float(currency_match.group(1).replace(',', ''))
            return 100 <= currency_value <= 1000000  # Reasonable upper limit
        
        return False
    
    def validate_returns(self, value: Dict[str, str]) -> bool:
        """Validate returns data."""
        for period, return_value in value.items():
            if return_value != "Not available":
                percentage_match = re.search(r'([0-9-]+\.?[0-9]*)%', return_value)
                if percentage_match:
                    return_value_float = float(percentage_match.group(1))
                    if not (-100 <= return_value_float <= 200):  # Allow for extreme cases
                        return False
                else:
                    return False
        return True
    
    def validate_riskometer(self, value: str) -> bool:
        """Validate riskometer."""
        valid_risks = ['Low', 'Moderately Low', 'Moderate', 'Moderately High', 'High', 'Very High']
        return value in valid_risks or value == "Not available"
    
    def validate_text(self, value: str) -> bool:
        """Validate text field."""
        return len(value) >= 3 and len(value) <= 500
    
    def validate_allocation(self, value: Dict[str, str]) -> bool:
        """Validate asset allocation."""
        total_percentage = 0.0
        
        for asset_type, allocation_value in value.items():
            if allocation_value != "Not available":
                percentage_match = re.search(r'([0-9]+\.?[0-9]*)%', allocation_value)
                if percentage_match:
                    total_percentage += float(percentage_match.group(1))
        
        # Allow some tolerance for rounding errors
        return abs(total_percentage - 100.0) <= 5.0 or total_percentage == 0.0
    
    def _calculate_extraction_confidence(self, extracted_fields: Dict[str, Any]) -> float:
        """
        Calculate confidence score for extraction.
        """
        total_fields = len(self.extraction_rules)
        extracted_count = 0
        confidence_score = 0.0
        
        for field_name, rule in self.extraction_rules.items():
            if field_name in extracted_fields:
                value = extracted_fields[field_name]
                
                if value != rule.default_value:
                    extracted_count += 1
                    
                    # Higher confidence for required fields
                    if rule.required:
                        confidence_score += 30
                    else:
                        confidence_score += 20
                else:
                    # Penalize missing optional fields
                    confidence_score -= 5
        
        # Calculate final confidence
        if total_fields > 0:
            base_confidence = (extracted_count / total_fields) * 100
            final_confidence = min(100.0, base_confidence + confidence_score)
        else:
            final_confidence = 0.0
        
        return round(final_confidence, 1)
    
    def _validate_extracted_fields(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all extracted fields.
        """
        validation_result = {
            'overall_status': 'passed',
            'errors': [],
            'field_validations': {}
        }
        
        for field_name, value in extracted_fields.items():
            rule = self.extraction_rules.get(field_name)
            if rule:
                if field_name == 'returns':
                    validation = self.validate_returns(value)
                elif field_name == 'asset_allocation':
                    validation = self.validate_allocation(value)
                else:
                    validation = self._validate_single_field(field_name, value, rule)
                
                validation_result['field_validations'][field_name] = {
                    'status': 'passed' if validation else 'failed',
                    'value': value
                }
                
                if not validation:
                    validation_result['overall_status'] = 'failed'
                    validation_result['errors'].append(f'{field_name} validation failed')
        
        return validation_result
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _update_extraction_stats(self, extraction_result: Dict[str, Any]):
        """Update extraction statistics."""
        self.extraction_stats['total_extractions'] += 1
        
        if extraction_result['validation_status'] == 'passed':
            self.extraction_stats['successful_extractions'] += 1
        else:
            self.extraction_stats['failed_extractions'] += 1
        
        # Update field-specific stats
        for field_name in extraction_result['extracted_fields'].keys():
            if field_name not in self.extraction_stats['field_stats']:
                self.extraction_stats['field_stats'][field_name] = 0
            self.extraction_stats['field_stats'][field_name] += 1
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        stats = self.extraction_stats.copy()
        
        if stats['total_extractions'] > 0:
            stats['success_rate'] = (
                stats['successful_extractions'] / stats['total_extractions']
            ) * 100
        else:
            stats['success_rate'] = 0.0
        
        stats['extractor_version'] = '1.0'
        stats['supported_fields'] = list(self.extraction_rules.keys())
        
        return stats
    
    def reset_stats(self):
        """Reset extraction statistics."""
        self.extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'field_stats': {}
        }
        logger.info("Extraction statistics reset")

# Global field extractor instance
field_extractor = FieldExtractor()

if __name__ == "__main__":
    # Test field extractor
    print("🔍 Testing Field Extractor")
    print("=" * 50)
    
    test_text = """
    HDFC Large Cap Fund Direct Growth
    
    Fund Type: Direct Growth
    Category: Large Cap
    
    Expense Ratio: 1.25%
    Exit Load: 0%
    Minimum SIP: ₹500
    
    1 Year Return: 12.5%
    3 Year Return: 15.2%
    5 Year Return: 14.8%
    
    Riskometer: Moderately High
    Benchmark: Nifty 50 TRI
    
    Asset Allocation:
    Equity: 85.2%
    Debt: 10.5%
    Cash: 4.3%
    """
    
    # Test extraction
    result = field_extractor.extract_from_text(test_text, "https://groww.in/test")
    
    print(f"Extraction Result:")
    print(f"Overall Status: {result['validation_status']}")
    print(f"Confidence: {result['extraction_confidence']:.1f}")
    print(f"Fields Extracted: {len(result['extracted_fields'])}")
    
    # Show extracted fields
    for field_name, value in result['extracted_fields'].items():
        print(f"{field_name}: {value}")
    
    # Show validation details
    if result['validation_errors']:
        print(f"\nValidation Errors:")
        for error in result['validation_errors']:
            print(f"  • {error}")
    
    # Show stats
    stats = field_extractor.get_extraction_stats()
    print(f"\nExtractor Stats:")
    print(f"Total Extractions: {stats['total_extractions']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"Supported Fields: {stats['supported_fields']}")
    
    print("\n✅ Field extractor testing completed")
