#!/usr/bin/env python3
"""
Quick Vector Search for Mindfulness
Simplified version for frequent use with minimal overhead
"""

from pathlib import Path
from vector_search import MindfulVectorSearch

class QuickMindfulSearch:
    """Lightweight wrapper for frequent mindfulness check-ins"""
    
    def __init__(self):
        self.search_engine = MindfulVectorSearch()
        # Pre-build index once
        self.search_engine.ensure_index_built()
    
    def quick_resonance(self, thought: str) -> str:
        """Get quick vector resonance - raw data only for cost efficiency"""
        results, stats = self.search_engine.search(thought, top_k=1, min_score=0.1)
        
        if results:
            result = results[0]
            return f"Vector resonance: {result.section} (score: {result.combined_score:.2f}) - {result.content[:150]}..."
        else:
            return "No clear vector resonances found."

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        search = QuickMindfulSearch()
        thought = " ".join(sys.argv[1:])
        print(search.quick_resonance(thought))
    else:
        print("Usage: python quick_search.py 'your thought here'")