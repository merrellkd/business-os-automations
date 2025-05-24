
# Create main.py at the root of your semantic_search package

#!/usr/bin/env python3
"""Main entry point for the semantic search system."""

import sys
import logging
from pathlib import Path


# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from interfaces.cli import cli

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    logger.info("Starting Semantic Search System")
    
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()