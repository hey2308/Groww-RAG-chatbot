"""
Phase 1.3.1 - Web Scraping Implementation
Data Validation Module for Scraped Fund Information
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapedDataValidator:
    """
    Validates scraped fund data for quality and completeness.
    """
    
    def __init__(self):
        """
        Initialize validator with validation rules and schemas.
        """
        self.validation_rules = self._initialize_validation_rules()
        self.data_schema = self._initialize_data_schema()
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'warnings': 0,
            'errors': []
        }
        
        logger.info("Scraped data validator initialized")
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """
        Initialize validation rules for different data types.
        """
        return {
            'fund_name': {
                'required': True,
                'min_length': 5,
                'max_length': 200,
                'pattern': r'^[A-Za-z0-9\s\-]+$',
                'forbidden_words': ['test', 'demo', 'example']
            },
            'expense_ratio': {
                'required': False,
                'type': 'percentage',
                'min_value': 0.0,
                'max_value': 5.0,
                'pattern': r'^\d+\.?\d*%?$'
            },
            'exit_load': {
                'required': False,
                'type': 'percentage_or_text',
                'allowed_values': ['0%', '1%', 'Not available'],
                'pattern': r'^(0|1)%?$|Not available$'
            },
            'min_sip': {
                'required': False,
                'type': 'currency',
                'min_value': 100,
                'max_value': 100000,
                'pattern': r'^₹\d+(?:,\d{3})*(?:\.\d{2})?$|^Not available$'
            },
            'nav': {
                'required': False,
                'type': 'currency',
                'min_value': 1,
                'max_value': 10000,
                'pattern': r'^₹\d+(?:,\d{3})*(?:\.\d{2})?$|^Not available$'
            },
            'riskometer': {
                'required': False,
                'type': 'enum',
                'allowed_values': [
                    'Low', 'Moderately Low', 'Moderate', 'Moderately High', 'High', 'Very High',
                    'Not available'
                ]
            },
            'benchmark': {
                'required': False,
                'type': 'text',
                'min_length': 3,
                'max_length': 100,
                'pattern': r'^[A-Za-z0-9\s\-\.]+$'
            },
            'returns': {
                'required': False,
                'type': 'percentage_map',
                'periods': ['1Y', '3Y', '5Y'],
                'min_value': -50.0,
                'max_value': 100.0
            },
            'source_url': {
                'required': True,
                'type': 'url',
                'pattern': r'^https?://[^\s/$.?#].[^\s]*$',
                'allowed_domains': ['groww.in']
            }
        }
    
    def _initialize_data_schema(self) -> Dict[str, List[str]]:
        """
        Initialize data schema for validation.
        """
        return {
            'required_fields': ['fund_name', 'source_url', 'scraped_at'],
            'financial_fields': ['expense_ratio', 'exit_load', 'min_sip', 'nav'],
            'performance_fields': ['returns'],
            'risk_fields': ['riskometer', 'benchmark'],
            'classification_fields': ['fund_type', 'category'],
            'optional_fields': ['asset_allocation', 'fund_details']
        }
    
    def validate_fund_data(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete fund data against schema and rules.
        """
        logger.info(f"Validating fund data: {fund_data.get('fund_name', 'Unknown')}")
        
        validation_result = {
            'fund_name': fund_data.get('fund_name', 'Unknown'),
            'validation_timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'field_validations': {},
            'validation_score': 0.0,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Validate required fields first
            required_validation = self._validate_required_fields(fund_data)
            validation_result['field_validations']['required_fields'] = required_validation
            
            # Validate each field type
            for field_name, validation_rule in self.validation_rules.items():
                if field_name in fund_data:
                    field_result = self._validate_field(
                        field_name, 
                        fund_data[field_name], 
                        validation_rule
                    )
                    validation_result['field_validations'][field_name] = field_result
            
            # Validate complex fields
            if 'returns' in fund_data:
                returns_validation = self._validate_returns(fund_data['returns'])
                validation_result['field_validations']['returns'] = returns_validation
            
            if 'asset_allocation' in fund_data:
                allocation_validation = self._validate_asset_allocation(fund_data['asset_allocation'])
                validation_result['field_validations']['asset_allocation'] = allocation_validation
            
            # Calculate overall validation score
            validation_result['validation_score'] = self._calculate_validation_score(
                validation_result['field_validations']
            )
            
            # Determine overall status
            validation_result['overall_status'] = self._determine_overall_status(
                validation_result['field_validations'],
                validation_result['validation_score']
            )
            
            # Generate recommendations
            validation_result['recommendations'] = self._generate_recommendations(
                validation_result['field_validations']
            )
            
            # Update stats
            self._update_validation_stats(validation_result)
            
            logger.info(f"Validation completed. Score: {validation_result['validation_score']:.1f}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating fund data: {e}")
            return {
                'fund_name': fund_data.get('fund_name', 'Unknown'),
                'validation_timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e),
                'validation_score': 0.0
            }
    
    def _validate_required_fields(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate required fields are present and valid.
        """
        result = {
            'status': 'passed',
            'missing_fields': [],
            'invalid_fields': [],
            'score': 100.0
        }
        
        required_fields = self.data_schema['required_fields']
        
        for field in required_fields:
            if field not in fund_data or not fund_data[field]:
                result['missing_fields'].append(field)
                result['status'] = 'failed'
            elif field == 'source_url' and not self._validate_url(fund_data[field]):
                result['invalid_fields'].append(field)
                result['status'] = 'failed'
            elif field == 'scraped_at' and not self._validate_timestamp(fund_data[field]):
                result['invalid_fields'].append(field)
                result['status'] = 'failed'
        
        # Calculate score
        total_required = len(required_fields)
        valid_count = total_required - len(result['missing_fields']) - len(result['invalid_fields'])
        result['score'] = (valid_count / total_required) * 100 if total_required > 0 else 0
        
        return result
    
    def _validate_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual field against its rule.
        """
        result = {
            'field_name': field_name,
            'value': value,
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'score': 100.0
        }
        
        try:
            # Check if value is "Not available"
            if str(value).strip() == "Not available":
                if rule.get('required', False):
                    result['status'] = 'failed'
                    result['errors'].append(f'{field_name} is required but marked as "Not available"')
                    result['score'] = 0.0
                else:
                    result['warnings'].append(f'{field_name} is not available (acceptable for optional field)')
                return result
            
            # Type-specific validation
            field_type = rule.get('type', 'text')
            
            if field_type == 'percentage':
                result = self._validate_percentage_field(field_name, value, rule)
            elif field_type == 'currency':
                result = self._validate_currency_field(field_name, value, rule)
            elif field_type == 'enum':
                result = self._validate_enum_field(field_name, value, rule)
            elif field_type == 'url':
                result = self._validate_url_field(field_name, value, rule)
            elif field_type == 'percentage_map':
                # This is handled separately in _validate_returns
                pass
            else:  # text or other types
                result = self._validate_text_field(field_name, value, rule)
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f'Validation error: {e}')
            result['score'] = 0.0
        
        return result
    
    def _validate_percentage_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate percentage field.
        """
        result = {'status': 'passed', 'errors': [], 'warnings': [], 'score': 100.0}
        
        value_str = str(value).strip()
        
        # Check pattern
        pattern = rule.get('pattern', r'^\d+\.?\d*%?$')
        if not re.match(pattern, value_str):
            result['status'] = 'failed'
            result['errors'].append(f'{field_name} does not match percentage pattern')
            result['score'] = 0.0
            return result
        
        # Extract numeric value
        numeric_match = re.search(r'(\d+\.?\d*)', value_str)
        if numeric_match:
            numeric_value = float(numeric_match.group(1))
            
            # Check range
            min_val = rule.get('min_value', 0.0)
            max_val = rule.get('max_value', 100.0)
            
            if numeric_value < min_val or numeric_value > max_val:
                result['status'] = 'failed'
                result['errors'].append(f'{field_name} value {numeric_value} is outside range {min_val}-{max_val}')
                result['score'] = 50.0
        
        return result
    
    def _validate_currency_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate currency field.
        """
        result = {'status': 'passed', 'errors': [], 'warnings': [], 'score': 100.0}
        
        value_str = str(value).strip()
        
        # Check pattern
        pattern = rule.get('pattern', r'^₹\d+(?:,\d{3})*(?:\.\d{2})?$')
        if not re.match(pattern, value_str):
            result['status'] = 'failed'
            result['errors'].append(f'{field_name} does not match currency pattern')
            result['score'] = 0.0
            return result
        
        # Extract numeric value
        numeric_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', value_str.replace('₹', ''))
        if numeric_match:
            numeric_value = float(numeric_match.group(1).replace(',', ''))
            
            # Check range
            min_val = rule.get('min_value', 0)
            max_val = rule.get('max_value', 1000000)
            
            if numeric_value < min_val or numeric_value > max_val:
                result['status'] = 'warning'
                result['warnings'].append(f'{field_name} value {numeric_value} seems unusual for range {min_val}-{max_val}')
                result['score'] = 75.0
        
        return result
    
    def _validate_enum_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate enum field.
        """
        result = {'status': 'passed', 'errors': [], 'warnings': [], 'score': 100.0}
        
        value_str = str(value).strip()
        allowed_values = rule.get('allowed_values', [])
        
        if value_str not in allowed_values:
            result['status'] = 'failed'
            result['errors'].append(f'{field_name} value "{value_str}" not in allowed values: {allowed_values}')
            result['score'] = 0.0
        
        return result
    
    def _validate_url_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate URL field.
        """
        result = {'status': 'passed', 'errors': [], 'warnings': [], 'score': 100.0}
        
        url_str = str(value).strip()
        
        # Check pattern
        pattern = rule.get('pattern', r'^https?://[^\s/$.?#].[^\s]*$')
        if not re.match(pattern, url_str):
            result['status'] = 'failed'
            result['errors'].append(f'{field_name} is not a valid URL')
            result['score'] = 0.0
            return result
        
        # Check allowed domains
        allowed_domains = rule.get('allowed_domains', [])
        if allowed_domains:
            from urllib.parse import urlparse
            parsed_url = urlparse(url_str)
            domain = parsed_url.netloc.lower()
            
            if domain not in allowed_domains:
                result['status'] = 'warning'
                result['warnings'].append(f'{field_name} domain "{domain}" is not in allowed list: {allowed_domains}')
                result['score'] = 75.0
        
        return result
    
    def _validate_text_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate text field.
        """
        result = {'status': 'passed', 'errors': [], 'warnings': [], 'score': 100.0}
        
        value_str = str(value).strip()
        
        # Check length
        min_length = rule.get('min_length', 0)
        max_length = rule.get('max_length', 1000)
        
        if len(value_str) < min_length:
            result['status'] = 'failed'
            result['errors'].append(f'{field_name} is too short (min: {min_length})')
            result['score'] = 0.0
        elif len(value_str) > max_length:
            result['status'] = 'warning'
            result['warnings'].append(f'{field_name} is quite long (max: {max_length})')
            result['score'] = 75.0
        
        # Check pattern
        pattern = rule.get('pattern')
        if pattern and not re.match(pattern, value_str):
            result['status'] = 'warning'
            result['warnings'].append(f'{field_name} contains unusual characters')
            result['score'] = 75.0
        
        # Check forbidden words
        forbidden_words = rule.get('forbidden_words', [])
        value_lower = value_str.lower()
        for word in forbidden_words:
            if word in value_lower:
                result['status'] = 'warning'
                result['warnings'].append(f'{field_name} contains potentially problematic word: {word}')
                result['score'] = 50.0
                break
        
        return result
    
    def _validate_returns(self, returns_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate returns data structure.
        """
        result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'score': 100.0,
            'period_validations': {}
        }
        
        if not isinstance(returns_data, dict):
            result['status'] = 'failed'
            result['errors'].append('Returns data is not a dictionary')
            result['score'] = 0.0
            return result
        
        expected_periods = ['1Y', '3Y', '5Y']
        
        for period in expected_periods:
            if period in returns_data:
                period_result = self._validate_percentage_field(
                    f'returns_{period}',
                    returns_data[period],
                    {'type': 'percentage', 'min_value': -50.0, 'max_value': 100.0}
                )
                result['period_validations'][period] = period_result
            else:
                result['period_validations'][period] = {
                    'status': 'warning',
                    'warnings': [f'Return data for {period} period is missing'],
                    'score': 75.0
                }
        
        # Calculate overall returns score
        period_scores = [
            val.get('score', 0) for val in result['period_validations'].values()
        ]
        if period_scores:
            result['score'] = sum(period_scores) / len(period_scores)
        else:
            result['score'] = 0.0
        
        return result
    
    def _validate_asset_allocation(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate asset allocation data.
        """
        result = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'score': 100.0,
            'allocation_validations': {}
        }
        
        if not isinstance(allocation_data, dict):
            result['status'] = 'failed'
            result['errors'].append('Asset allocation data is not a dictionary')
            result['score'] = 0.0
            return result
        
        expected_assets = ['equity', 'debt', 'cash', 'others']
        total_percentage = 0.0
        
        for asset in expected_assets:
            if asset in allocation_data:
                asset_value = allocation_data[asset]
                if str(asset_value).strip() != "Not available":
                    # Try to extract percentage
                    percentage_match = re.search(r'(\d+\.?\d*)%?', str(asset_value))
                    if percentage_match:
                        percentage = float(percentage_match.group(1))
                        total_percentage += percentage
                        
                        result['allocation_validations'][asset] = {
                            'status': 'passed',
                            'percentage': percentage,
                            'score': 100.0
                        }
                    else:
                        result['allocation_validations'][asset] = {
                            'status': 'warning',
                            'warnings': [f'Could not parse percentage for {asset}'],
                            'score': 75.0
                        }
                else:
                    result['allocation_validations'][asset] = {
                        'status': 'passed',
                        'percentage': 0.0,
                        'score': 100.0
                    }
            else:
                result['allocation_validations'][asset] = {
                    'status': 'warning',
                    'warnings': [f'Asset {asset} is missing from allocation'],
                    'score': 75.0
                }
        
        # Check if allocation percentages sum to ~100%
        if total_percentage > 0:
            if abs(total_percentage - 100.0) > 5.0:  # Allow 5% tolerance
                result['status'] = 'warning'
                result['warnings'].append(f'Asset allocation totals {total_percentage:.1f}% (expected ~100%)')
                result['score'] = 75.0
        
        return result
    
    def _validate_url(self, url: str) -> bool:
        """
        Basic URL validation.
        """
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, str(url).strip()))
    
    def _validate_timestamp(self, timestamp: str) -> bool:
        """
        Basic timestamp validation.
        """
        try:
            # Try to parse common timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(timestamp, fmt)
                    return True
                except ValueError:
                    continue
            
            return False
        except:
            return False
    
    def _calculate_validation_score(self, field_validations: Dict[str, Any]) -> float:
        """
        Calculate overall validation score from field validations.
        """
        total_score = 0.0
        total_fields = 0
        
        for field_name, validation in field_validations.items():
            if isinstance(validation, dict) and 'score' in validation:
                total_score += validation['score']
                total_fields += 1
        
        return total_score / total_fields if total_fields > 0 else 0.0
    
    def _determine_overall_status(self, field_validations: Dict[str, Any], score: float) -> str:
        """
        Determine overall validation status.
        """
        # Check for any failed validations
        for field_name, validation in field_validations.items():
            if isinstance(validation, dict) and validation.get('status') == 'failed':
                return 'failed'
        
        # Check for errors
        if score < 50.0:
            return 'failed'
        elif score < 80.0:
            return 'warning'
        else:
            return 'passed'
    
    def _generate_recommendations(self, field_validations: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on validation results.
        """
        recommendations = []
        
        for field_name, validation in field_validations.items():
            if not isinstance(validation, dict):
                continue
            
            if validation.get('status') == 'failed':
                recommendations.append(f'Fix validation errors for {field_name}')
            elif validation.get('warnings'):
                for warning in validation.get('warnings', []):
                    recommendations.append(f'Address warning: {warning}')
        
        # Add general recommendations
        if not recommendations:
            recommendations.append('Data validation passed successfully')
        
        return recommendations
    
    def _update_validation_stats(self, validation_result: Dict[str, Any]):
        """
        Update validation statistics.
        """
        self.validation_stats['total_validations'] += 1
        
        if validation_result.get('overall_status') == 'passed':
            self.validation_stats['passed_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
        
        # Count warnings and errors
        for field_validation in validation_result.get('field_validations', {}).values():
            if isinstance(field_validation, dict):
                if field_validation.get('warnings'):
                    self.validation_stats['warnings'] += len(field_validation['warnings'])
                if field_validation.get('errors'):
                    self.validation_stats['errors'].extend(field_validation['errors'])
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        """
        stats = self.validation_stats.copy()
        
        # Calculate success rate
        if stats['total_validations'] > 0:
            stats['success_rate'] = (stats['passed_validations'] / stats['total_validations']) * 100
        else:
            stats['success_rate'] = 0.0
        
        stats['validator_version'] = '1.0'
        stats['last_updated'] = datetime.now().isoformat()
        
        return stats
    
    def reset_stats(self):
        """
        Reset validation statistics.
        """
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'warnings': 0,
            'errors': []
        }
        logger.info("Validation statistics reset")

# Global validator instance
scraped_data_validator = ScrapedDataValidator()

if __name__ == "__main__":
    # Test validator with sample data
    test_data = {
        'fund_name': 'HDFC Large Cap Fund Direct Growth',
        'source_url': 'https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth',
        'scraped_at': '2024-01-01 12:00:00',
        'expense_ratio': '1.25%',
        'exit_load': '0%',
        'min_sip': '₹500',
        'nav': '₹125.67',
        'returns': {
            '1Y': '12.5%',
            '3Y': '15.2%',
            '5Y': '14.8%'
        },
        'riskometer': 'Moderately High',
        'benchmark': 'Nifty 50 TRI',
        'asset_allocation': {
            'equity': '85.2%',
            'debt': '10.5%',
            'cash': '4.3%'
        }
    }
    
    print("Testing Scraped Data Validator...")
    
    # Validate test data
    result = scraped_data_validator.validate_fund_data(test_data)
    
    print(f"\nValidation Result:")
    print(f"Overall Status: {result.get('overall_status', 'unknown')}")
    print(f"Validation Score: {result.get('validation_score', 0):.1f}")
    print(f"Fund Name: {result.get('fund_name', 'N/A')}")
    
    # Show field validations
    field_validations = result.get('field_validations', {})
    for field, validation in field_validations.items():
        status = validation.get('status', 'unknown')
        score = validation.get('score', 0)
        print(f"{field}: {status} (score: {score:.1f})")
        
        if validation.get('errors'):
            for error in validation['errors']:
                print(f"  Error: {error}")
        
        if validation.get('warnings'):
            for warning in validation['warnings']:
                print(f"  Warning: {warning}")
    
    # Show recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Show stats
    stats = scraped_data_validator.get_validation_stats()
    print(f"\nValidator Stats:")
    print(f"Total Validations: {stats['total_validations']}")
    print(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
