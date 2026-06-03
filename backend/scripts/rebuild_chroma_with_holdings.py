"""
Rebuild vector store with enriched holding analysis and sector allocation data
for all 5 HDFC mutual funds.
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.vector_store import VectorStore, _text_to_vector


# Fund holdings data with sector allocation
FUND_HOLDINGS_DATA = {
    "HDFC Large Cap Fund Direct Growth": {
        "fund_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "holdings": [
            {"name": "ICICI Bank Ltd.", "sector": "Financial", "allocation": "9.15%"},
            {"name": "HDFC Bank Ltd.", "sector": "Financial", "allocation": "7.84%"},
            {"name": "Bharti Airtel Ltd.", "sector": "Communication", "allocation": "5.90%"},
            {"name": "Reliance Industries Ltd.", "sector": "Energy", "allocation": "5.61%"},
            {"name": "Kak Mahindra Bank Ltd.", "sector": "Financial", "allocation": "5.47%"},
            {"name": "Titan Company Ltd.", "sector": "Consumer Discretionary", "allocation": "4.74%"},
            {"name": "Infosys Ltd.", "sector": "Technology", "allocation": "3.01%"},
            {"name": "Bajaj Auto Ltd.", "sector": "Automobile", "allocation": "2.95%"},
            {"name": "Hindustan Unilever Ltd.", "sector": "Consumer Staples", "allocation": "2.60%"},
            {"name": "State Bank of India", "sector": "Financial", "allocation": "2.43%"},
        ],
        "sector_allocation": {
            "Financial": "28.92%",
            "Communication": "5.90%",
            "Energy": "5.61%",
            "Technology": "3.01%",
            "Automobile": "2.95%",
            "Consumer Staples": "2.60%",
            "Healthcare": "1.50%",
            "Construction": "1.38%",
            "Capital Goods": "1.41%",
            "Metals & Mining": "0.24%",
            "Insurance": "0.19%",
            "Services": "0.10%",
        }
    },
    "HDFC Equity Fund Direct Growth": {
        "fund_url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "holdings": [
            {"name": "ICICI Bank Ltd.", "sector": "Financial", "allocation": "8.69%"},
            {"name": "Axis Bank Ltd.", "sector": "Financial", "allocation": "6.83%"},
            {"name": "HDFC Bank Ltd.", "sector": "Financial", "allocation": "6.81%"},
            {"name": "State Bank of India", "sector": "Financial", "allocation": "4.74%"},
            {"name": "SBI Life Insurance Company Ltd.", "sector": "Insurance", "allocation": "3.79%"},
            {"name": "Larsen & Toubro Ltd.", "sector": "Construction", "allocation": "3.35%"},
            {"name": "Bharti Airtel Ltd.", "sector": "Communication", "allocation": "3.10%"},
            {"name": "HCL Technologies Ltd.", "sector": "Technology", "allocation": "2.54%"},
            {"name": "Infosys Ltd.", "sector": "Technology", "allocation": "1.57%"},
            {"name": "Cipla Ltd.", "sector": "Healthcare", "allocation": "2.74%"},
        ],
        "sector_allocation": {
            "Financial": "27.03%",
            "Insurance": "3.79%",
            "Construction": "3.35%",
            "Technology": "4.11%",
            "Communication": "3.10%",
            "Healthcare": "2.74%",
            "Automobile": "1.06%",
            "Consumer Staples": "0.76%",
            "Energy": "0.79%",
            "Services": "0.71%",
        }
    },
    "HDFC Focused Fund Direct Growth": {
        "fund_url": "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "holdings": [
            {"name": "ICICI Bank Ltd.", "sector": "Financial", "allocation": "9.02%"},
            {"name": "HDFC Bank Ltd.", "sector": "Financial", "allocation": "8.41%"},
            {"name": "Axis Bank Ltd.", "sector": "Financial", "allocation": "7.27%"},
            {"name": "State Bank of India", "sector": "Financial", "allocation": "5.76%"},
            {"name": "HCL Technologies Ltd.", "sector": "Technology", "allocation": "3.89%"},
            {"name": "Cipla Ltd.", "sector": "Healthcare", "allocation": "3.49%"},
            {"name": "Eternal Ltd.", "sector": "Services", "allocation": "3.53%"},
            {"name": "Bharti Airtel Ltd.", "sector": "Communication", "allocation": "3.69%"},
            {"name": "Tata Steel Ltd.", "sector": "Metals & Mining", "allocation": "2.58%"},
            {"name": "SBI Life Insurance Company Ltd.", "sector": "Insurance", "allocation": "3.58%"},
        ],
        "sector_allocation": {
            "Financial": "35.92%",
            "Technology": "3.89%",
            "Communication": "3.69%",
            "Healthcare": "3.49%",
            "Insurance": "3.58%",
            "Services": "3.53%",
            "Metals & Mining": "2.58%",
            "Automobile": "1.67%",
        }
    },
    "HDFC ELSS Tax Saver Fund Direct Plan Growth": {
        "fund_url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "holdings": [
            {"name": "ICICI Bank Ltd.", "sector": "Financial", "allocation": "8.93%"},
            {"name": "HDFC Bank Ltd.", "sector": "Financial", "allocation": "8.23%"},
            {"name": "Axis Bank Ltd.", "sector": "Financial", "allocation": "7.22%"},
            {"name": "State Bank of India", "sector": "Financial", "allocation": "4.81%"},
            {"name": "Maruti Suzuki India Ltd.", "sector": "Automobile", "allocation": "4.71%"},
            {"name": "Bharti Airtel Ltd.", "sector": "Communication", "allocation": "4.59%"},
            {"name": "Kotak Mahindra Bank Ltd.", "sector": "Financial", "allocation": "4.31%"},
            {"name": "SBI Life Insurance Company Ltd.", "sector": "Insurance", "allocation": "3.51%"},
            {"name": "Reliance Industries Ltd.", "sector": "Energy", "allocation": "3.06%"},
            {"name": "HCL Technologies Ltd.", "sector": "Technology", "allocation": "2.76%"},
        ],
        "sector_allocation": {
            "Financial": "29.03%",
            "Automobile": "4.71%",
            "Communication": "4.59%",
            "Insurance": "3.51%",
            "Energy": "3.06%",
            "Technology": "2.76%",
            "Healthcare": "1.35%",
            "Consumer Staples": "1.84%",
            "Services": "1.79%",
        }
    },
    "HDFC Mid Cap Fund Direct Growth": {
        "fund_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "holdings": [
            {"name": "Max Financial Services Ltd.", "sector": "Financial", "allocation": "4.37%"},
            {"name": "AU Small Finance Bank Ltd.", "sector": "Financial", "allocation": "4.24%"},
            {"name": "The Federal Bank Ltd.", "sector": "Financial", "allocation": "3.87%"},
            {"name": "Glenmark Pharmaceuticals Ltd.", "sector": "Healthcare", "allocation": "3.41%"},
            {"name": "Indian Bank", "sector": "Financial", "allocation": "3.31%"},
            {"name": "Balkrishna Industries Ltd.", "sector": "Automobile", "allocation": "3.25%"},
            {"name": "Fortis Healthcare Ltd.", "sector": "Healthcare", "allocation": "3.16%"},
            {"name": "Vishal Mega Mart Ltd.", "sector": "Services", "allocation": "2.92%"},
            {"name": "Ipca Laboratories Ltd.", "sector": "Healthcare", "allocation": "2.92%"},
            {"name": "Cummins India Ltd.", "sector": "Capital Goods", "allocation": "2.50%"},
        ],
        "sector_allocation": {
            "Financial": "15.79%",
            "Healthcare": "9.49%",
            "Automobile": "3.25%",
            "Services": "2.92%",
            "Capital Goods": "2.50%",
            "Consumer Staples": "2.48%",
            "Technology": "1.97%",
            "Communication": "1.86%",
            "Energy": "2.20%",
            "Chemicals": "1.03%",
        }
    },
}


def compute_sector_allocation_from_holdings(holdings: list) -> dict:
    """Compute sector allocation percentages from holdings list."""
    sector_totals = {}
    total = 0.0
    
    for h in holdings:
        sector = h.get("sector", "Unknown")
        allocation_str = h.get("allocation", "0%").replace("%", "")
        try:
            allocation = float(allocation_str)
        except ValueError:
            allocation = 0.0
        sector_totals[sector] = sector_totals.get(sector, 0.0) + allocation
        total += allocation
    
    if total == 0:
        return {}
    
    return {sector: f"{(value / total) * 100:.2f}%" for sector, value in sector_totals.items()}


def create_enriched_chunks(fund_name: str, fund_data: dict) -> list:
    """Create enriched chunks with holding analysis and sector allocation."""
    holdings = fund_data.get("holdings", [])
    sector_alloc = fund_data.get("sector_allocation", {})
    fund_url = fund_data.get("fund_url", "")
    
    # Create holding analysis chunk
    holding_lines = []
    for h in holdings[:10]:
        name = h.get("name", "")
        sector = h.get("sector", "")
        alloc = h.get("allocation", "")
        holding_lines.append(f"{name} | {sector} | Equity | {alloc}")
    
    holding_text = "\n".join(holding_lines)
    
    # Create sector allocation chunk
    sector_lines = []
    for sector, pct in sector_alloc.items():
        sector_lines.append(f"{sector}: {pct}")
    
    sector_text = "\n".join(sector_lines)
    
    chunks = []
    
    # Holdings chunk
    if holdings:
        chunks.append({
            "chunk_id": f"holdings_{fund_name.lower().replace(' ', '_')}",
            "chunk_type": "metric",
            "content": f"HDFC {fund_name} Holdings Analysis:\n{holding_text}",
            "token_count": len(holding_text.split()),
            "priority": "high",
            "fund_metadata": {
                "fund_name": fund_name,
                "fund_type": "Direct Growth",
                "category": fund_data.get("holdings", [{}])[0].get("sector", ""),
                "risk_level": "Very High",
                "source_url": fund_url,
            }
        })
    
    # Sector allocation chunk
    if sector_alloc:
        chunks.append({
            "chunk_id": f"sector_{fund_name.lower().replace(' ', '_')}",
            "chunk_type": "metric",
            "content": f"HDFC {fund_name} Equity Sector Allocation:\n{sector_text}",
            "token_count": len(sector_text.split()),
            "priority": "high",
            "fund_metadata": {
                "fund_name": fund_name,
                "fund_type": "Direct Growth",
                "category": "Equity",
                "risk_level": "Very High",
                "source_url": fund_url,
            }
        })
    
    return chunks


def load_existing_chunks() -> list:
    """Load existing chunks from the latest chunked data file."""
    chunk_paths = [
        Path("backend/backend/phase1_3/text_chunking"),
        Path("phase1_3/text_chunking"),
        Path("../backend/phase1_3/text_chunking"),
        Path("backend/phase1_3/text_chunking"),
    ]
    
    for base in chunk_paths:
        if not base.exists():
            continue
        files = sorted(base.glob("chunked_data_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            print(f"Loading existing chunks from: {files[0]}")
            try:
                data = json.loads(files[0].read_text(encoding="utf-8"))
                all_chunks = []
                for fund_entry in data:
                    for chunk in fund_entry.get("chunks", []):
                        fund_meta = chunk.get("fund_metadata", {})
                        all_chunks.append({
                            "chunk_id": chunk.get("chunk_id", ""),
                            "chunk_type": chunk.get("chunk_type", ""),
                            "content": chunk.get("content", ""),
                            "token_count": chunk.get("token_count", 0),
                            "priority": chunk.get("priority", "medium"),
                            "fund_metadata": fund_meta,
                        })
                print(f"Loaded {len(all_chunks)} existing chunks")
                return all_chunks
            except Exception as e:
                print(f"Failed to load existing chunks: {e}")
    return []


def rebuild_vector_store():
    """Rebuild vector store with enriched data."""
    print("=" * 70)
    print("Rebuilding Vector Store with Holding Analysis & Sector Allocation")
    print("=" * 70)

    # Initialize vector store
    store = VectorStore(persist_directory="./vector_store")
    store.collection.reset()  # Clear existing data
    
    all_documents = []
    all_metadatas = []
    all_ids = []
    
    # Load existing chunks first (basic fund info, metrics, performance)
    existing_chunks = load_existing_chunks()
    for chunk in existing_chunks:
        if chunk.get("content") and chunk.get("chunk_id"):
            all_documents.append(chunk["content"])
            all_metadatas.append(chunk.get("fund_metadata", {}))
            all_ids.append(chunk["chunk_id"])
    
    print(f"Added {len(existing_chunks)} existing chunks to batch")
    
    # Now add enriched holdings and sector allocation chunks
    for fund_name, fund_data in FUND_HOLDINGS_DATA.items():
        print(f"\nProcessing: {fund_name}")
        
        chunks = create_enriched_chunks(fund_name, fund_data)
        
        for chunk in chunks:
            all_documents.append(chunk["content"])
            all_metadatas.append(chunk["fund_metadata"])
            all_ids.append(chunk["chunk_id"])
        
        print(f"  Created {len(chunks)} enriched chunks")
    
    # Add all documents to vector store
    if all_documents:
        try:
            print(f"\nAdding {len(all_documents)} documents to vector store...")
            store.collection.add(
                documents=all_documents,
                metadatas=all_metadatas,
                ids=all_ids,
            )
            print(f"Successfully added {len(all_documents)} documents")
        except Exception as e:
            print(f"ERROR adding documents: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    # Verify
    count = store.collection.count()
    print(f"\nVector store now has {count} documents")
    print("=" * 70)
    print("Vector store rebuild completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    rebuild_vector_store()
