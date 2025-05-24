#!/usr/bin/env python3
"""Integration test script for the semantic search system.

This script tests the end-to-end functionality by:
1. Creating sample documents
2. Running the indexing flow
3. Testing various query types
4. Cleaning up test files

Usage:
    python test_integration.py

Must be run from the directory containing the semantic_search package.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add current directory to Python path to find the semantic_search package
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from semantic_search.flow import run_full_index, run_test_query
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Make sure you're running this script from: {current_dir}")
    print("Expected directory structure:")
    print("├── semantic_search/")
    print("│   ├── __init__.py")
    print("│   ├── flow.py")
    print("│   └── ...")
    print("└── test_integration.py  <- You are here")
    sys.exit(1)


def create_test_documents(test_dir: Path) -> None:
    """Create sample markdown documents for testing."""
    
    # Create directory structure
    (test_dir / "projects").mkdir(parents=True)
    (test_dir / "daily").mkdir(parents=True)
    
    # Sample business documents
    docs = {
        "projects/markers-helper.md": """# Markers Helper Project

## Overview
Building a tool to help designers manage design tokens and markers.

## Target Customer
- UI/UX designers
- Design system maintainers
- Frontend developers working with design tokens

## Timeline
Started: 2024-01-15
Expected completion: 2024-03-30

## Current Status
- ✅ Market research completed
- ✅ MVP wireframes done
- 🔄 Development in progress
- ⏳ User testing planned
""",
        
        "projects/semantic-search.md": """# Semantic Search System

## Purpose
Index and search business documents using semantic embeddings.

## Technology Stack
- Python
- FAISS for vector search  
- Ollama for local LLM
- PocketFlow for orchestration

## Recent Progress
- Completed storage layer implementation
- Built file processing utilities
- Integrated embedding generation
""",
        
        "daily/2024-01-20.md": """# Daily Notes - January 20, 2024

## Completed Today
- Reviewed Markers Helper user feedback
- Fixed embedding generation bug in semantic search
- Planned Q1 marketing strategy

## Next Actions
- Schedule user interviews for next week
- Deploy semantic search to production
- Review financial projections

## Ideas
- Consider adding AI-powered suggestions to Markers Helper
- Explore partnership with design tool companies
""",
        
        "daily/2024-01-21.md": """# Daily Notes - January 21, 2024

## Morning Standup
- Markers Helper: 60% complete, on track for March launch
- Semantic Search: Ready for internal testing
- Cash runway: 8 months remaining at current burn rate

## Meetings
- User interview with Sarah (UX Designer at TechCorp)
  - Loves the concept of automated design token management
  - Wants integration with Figma and Sketch
  - Willing to pay $29/month for team plan

## Financial Notes
- Monthly expenses: $12,000
- Revenue target for Q2: $15,000 MRR
- Fundraising timeline: Start in Q2 if growth is strong
""",
        
        "strategies/go-to-market.md": """# Go-to-Market Strategy

## Target Segments
1. **Individual Designers** ($9/month)
   - Freelancers
   - Solo practitioners
   - Students

2. **Design Teams** ($29/month per seat)
   - Startups with 2-10 designers
   - Design agencies
   - Corporate design teams

## Distribution Channels
- Product Hunt launch
- Design community partnerships
- Content marketing (design system blogs)
- Conference sponsorships

## Success Metrics
- 1,000 free trial signups in month 1
- 15% trial-to-paid conversion rate
- $50,000 ARR by end of Q2
"""
    }
    
    # Write all test documents
    for path, content in docs.items():
        file_path = test_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    print(f"✅ Created {len(docs)} test documents in {test_dir}")


def run_integration_test():
    """Run the complete integration test."""
    
    print("🚀 Starting Semantic Search Integration Test")
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_business_os"
        test_dir.mkdir()
        
        # Create sample documents
        create_test_documents(test_dir)
        
        # Configure system for testing
        config = {
            "root_path": str(test_dir),
            "file_extensions": [".md", ".txt"],
            "embedding_model": "nomic-embed-text",
            "llm_provider": "ollama",
            "index_path": str(test_dir / "test_index.pkl"),
            "metadata_path": str(test_dir / "test_metadata.db"),
            "output_format": "chat"
        }
        
        print(f"📁 Test directory: {test_dir}")
        
        # Test 1: Run indexing
        print("\n📚 Testing indexing flow...")
        shared = {"config": config}
        
        try:
            run_full_index(shared)
            files_count = len(shared.get("indexing", {}).get("filtered_files", []))
            chunks_count = len(shared.get("indexing", {}).get("chunks", []))
            print(f"✅ Indexing successful: {files_count} files, {chunks_count} chunks")
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            return False
        
        # Test 2: Simple semantic search
        print("\n🔍 Testing semantic search...")
        test_queries = [
            "What is the target customer for Markers Helper?",
            "What technology stack is used for semantic search?",
            "What are the monthly expenses?",
            "What was completed on January 20th?",
            "Tell me about the go-to-market strategy"
        ]
        
        for query in test_queries:
            try:
                result = run_test_query(query, config)
                print(f"✅ Query: '{query[:30]}...' -> {len(result)} chars response")
            except Exception as e:
                print(f"❌ Query failed: '{query}' -> {e}")
        
        # Test 3: Temporal queries  
        print("\n📅 Testing temporal queries...")
        temporal_queries = [
            "What happened yesterday?",
            "Summarize the last 7 days",
            "What was I working on recently?"
        ]
        
        for query in temporal_queries:
            try:
                result = run_test_query(query, config)
                print(f"✅ Temporal query: '{query}' -> {len(result)} chars response")
            except Exception as e:
                print(f"❌ Temporal query failed: '{query}' -> {e}")
        
        print("\n🎉 Integration test completed!")
        return True


if __name__ == "__main__":
    success = run_integration_test()
    exit(0 if success else 1)