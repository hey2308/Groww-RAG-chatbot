import logging
from typing import List, Dict, Any
from database.vector_store import _text_to_vector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, chroma_manager):
        """
        Initialize data processor with ChromaDB manager.
        """
        self.chroma_manager = chroma_manager
        logger.info("Data processor initialized with embedding model")
    
    def process_fund_data(self, fund_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean fund data for storage.
        """
        processed_data = []
        
        for fund_data in fund_data_list:
            try:
                # Clean and validate data
                cleaned_data = self._clean_fund_data(fund_data)
                
                # Create text chunks for RAG
                text_chunks = self._create_text_chunks(cleaned_data)
                
                # Generate embeddings
                embeddings = self._generate_embeddings([chunk['text'] for chunk in text_chunks])
                
                # Prepare for storage
                for i, chunk in enumerate(text_chunks):
                    processed_item = {
                        'id': f"{cleaned_data['fund_name'].replace(' ', '_').lower()}_{i}",
                        'text': chunk['text'],
                        'metadata': {
                            'fund_name': cleaned_data['fund_name'],
                            'source_url': cleaned_data['source_url'],
                            'scraped_at': cleaned_data['scraped_at'],
                            'chunk_type': chunk['type'],
                            'fund_category': cleaned_data.get('category', 'Unknown'),
                            'fund_type': cleaned_data.get('fund_type', 'Unknown')
                        },
                        'embedding': embeddings[i] if embeddings else None
                    }
                    processed_data.append(processed_item)
                
                logger.info(f"Processed {len(text_chunks)} chunks for {cleaned_data['fund_name']}")
                
            except Exception as e:
                logger.error(f"Error processing fund data: {e}")
                continue
        
        return processed_data
    
    def _clean_fund_data(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate fund data.
        """
        cleaned = fund_data.copy()
        
        # Clean numeric fields
        numeric_fields = ['expense_ratio', 'min_sip', 'nav']
        for field in numeric_fields:
            if field in cleaned:
                cleaned[field] = self._clean_numeric_field(cleaned[field])
        
        # Clean text fields
        text_fields = ['fund_name', 'riskometer', 'benchmark', 'fund_type', 'category']
        for field in text_fields:
            if field in cleaned:
                cleaned[field] = self._clean_text_field(cleaned[field])
        
        # Validate required fields
        required_fields = ['fund_name', 'source_url', 'scraped_at']
        for field in required_fields:
            if field not in cleaned or not cleaned[field]:
                raise ValueError(f"Required field '{field}' is missing or empty")
        
        return cleaned
    
    def _clean_numeric_field(self, value: str) -> str:
        """
        Clean numeric field and extract relevant information.
        """
        if not value or value == "Not available":
            return "Not available"
        
        # Remove common prefixes and extract numbers
        import re
        
        # Handle percentage values
        if '%' in value:
            match = re.search(r'(\d+\.?\d*)\s*%?', value)
            if match:
                return f"{match.group(1)}%"
        
        # Handle currency values
        if '₹' in value or 'Rs' in value or 'INR' in value:
            match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', value.replace(',', ''))
            if match:
                return f"₹{match.group(1)}"
        
        # Handle plain numbers
        match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', value.replace(',', ''))
        if match:
            return match.group(1)
        
        return value.strip()
    
    def _clean_text_field(self, value: str) -> str:
        """
        Clean text field.
        """
        if not value:
            return "Not available"
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(value.split())
        
        # Remove special characters that might cause issues
        import re
        cleaned = re.sub(r'[^\w\s\-.,%₹]', '', cleaned)
        
        return cleaned.strip()
    
    def _create_text_chunks(self, fund_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create text chunks from fund data for RAG.
        """
        chunks = []
        
        # Basic information chunk
        basic_info = f"""
        Fund Name: {fund_data.get('fund_name', 'Unknown')}
        Category: {fund_data.get('category', 'Unknown')}
        Type: {fund_data.get('fund_type', 'Unknown')}
        Expense Ratio: {fund_data.get('expense_ratio', 'Not available')}
        Exit Load: {fund_data.get('exit_load', 'Not available')}
        Minimum SIP: {fund_data.get('min_sip', 'Not available')}
        Riskometer: {fund_data.get('riskometer', 'Not available')}
        Benchmark: {fund_data.get('benchmark', 'Not available')}
        NAV: {fund_data.get('nav', 'Not available')}
        """
        
        chunks.append({
            'text': basic_info.strip(),
            'type': 'basic_info'
        })
        
        # Returns chunk
        returns = fund_data.get('returns', {})
        if returns:
            returns_text = f"""
            Returns for {fund_data.get('fund_name', 'Unknown')}:
            1 Year: {returns.get('1Y', 'Not available')}
            3 Years: {returns.get('3Y', 'Not available')}
            5 Years: {returns.get('5Y', 'Not available')}
            """
            
            chunks.append({
                'text': returns_text.strip(),
                'type': 'returns'
            })
        
        # Asset allocation chunk
        allocation = fund_data.get('asset_allocation', {})
        if allocation:
            allocation_text = f"""
            Asset Allocation for {fund_data.get('fund_name', 'Unknown')}:
            Equity: {allocation.get('equity', 'Not available')}
            Debt: {allocation.get('debt', 'Not available')}
            Cash: {allocation.get('cash', 'Not available')}
            Others: {allocation.get('others', 'Not available')}
            """
            
            chunks.append({
                'text': allocation_text.strip(),
                'type': 'asset_allocation'
            })
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        """
        try:
            embeddings = [_text_to_vector(text) for text in texts]
            logger.info(f"Generated embeddings for {len(texts)} text chunks")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def store_processed_data(self, processed_data: List[Dict[str, Any]]) -> bool:
        """
        Store processed data in ChromaDB.
        """
        try:
            if not processed_data:
                logger.warning("No processed data to store")
                return False
            
            # Prepare data for ChromaDB
            documents = [item['text'] for item in processed_data]
            metadatas = [item['metadata'] for item in processed_data]
            ids = [item['id'] for item in processed_data]
            
            # Store in ChromaDB
            self.chroma_manager.add_documents(documents, metadatas, ids)
            
            logger.info(f"Successfully stored {len(documents)} documents in ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error storing processed data: {e}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        """
        try:
            stats = self.chroma_manager.get_collection_stats()
            return {
                "processing_status": "active",
                "embedding_model": "all-MiniLM-L6-v2",
                "chroma_stats": stats
            }
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"processing_status": "error", "error": str(e)}
    
    def test_processor(self) -> bool:
        """
        Test data processor functionality.
        """
        try:
            # Create test data
            test_fund_data = {
                'fund_name': 'Test Fund',
                'source_url': 'https://test.com',
                'scraped_at': '2024-01-01',
                'expense_ratio': '1.5%',
                'exit_load': '0%',
                'min_sip': '₹500',
                'category': 'Large Cap',
                'fund_type': 'Direct Growth'
            }
            
            # Process test data
            processed = self.process_fund_data([test_fund_data])
            
            if processed:
                logger.info("Data processor test successful")
                return True
            else:
                logger.error("Data processor test failed - no processed data")
                return False
                
        except Exception as e:
            logger.error(f"Data processor test failed: {e}")
            return False

# Initialize data processor (will be used with ChromaDB manager)
# data_processor = DataProcessor(chroma_manager)

if __name__ == "__main__":
    from database.chroma_setup import chroma_manager
    processor = DataProcessor(chroma_manager)
    processor.test_processor()
