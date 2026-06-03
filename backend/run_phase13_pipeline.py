"""
Phase 1.3 pipeline entry point (delegates to scheduled orchestrator).
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pipeline.phase13_orchestrator import Phase13Orchestrator


def run_complete_pipeline() -> bool:
    result = Phase13Orchestrator().run(force_scrape=True)
    return result.success


if __name__ == "__main__":
    success = run_complete_pipeline()
    print("Pipeline completed successfully!" if success else "Pipeline failed!")
    sys.exit(0 if success else 1)
