#!/usr/bin/env python3
"""
Vector Search for Mindfulness Practice
Adapted from lisa_brain unified search system

Enables semantic search across knowledge base for computational mindfulness practice.
"""

import json
import hashlib
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Set
from dataclasses import dataclass
import re

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class MindfulSearchResult:
    """Search result for mindfulness practice"""
    file_path: Path
    file_title: str
    title: str  # paragraph title
    content: str  # paragraph content
    section: str
    context: str
    para_index: int
    vector_score: float
    string_score: float
    combined_score: float
    matching_snippets: List[str]
    semantic_themes: List[str]


@dataclass
class SearchStats:
    """Performance statistics"""
    query: str
    total_results: int
    search_time_ms: float
    cache_hit: bool


class MindfulVectorSearch:
    """Vector search engine for computational mindfulness"""
    
    def __init__(self, 
                 docs_dir: Optional[Path] = None,
                 cache_dir: Optional[Path] = None,
                 model_name: str = "all-MiniLM-L6-v2"):
        
        self.model_name = model_name
        self.model = None  # Lazy load
        
        # Directories
        self.docs_dir = docs_dir or Path(__file__).parent.parent.parent
        self.cache_dir = cache_dir or Path(__file__).parent / "search_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Index storage
        self.documents = []
        self.embeddings = None
        self.content_hash = None
    
    def _get_model(self):
        """Lazy load sentence transformer"""
        if self.model is None:
            print(f"🧠 Loading sentence transformer: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def _compute_content_hash(self) -> str:
        """Compute hash of all markdown content for change detection"""
        md_files = list(self.docs_dir.rglob("*.md"))
        if not md_files:
            return ""
        
        combined = ""
        for file in sorted(md_files):
            try:
                combined += file.read_text() + "\n"
            except:
                continue
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _load_cache(self) -> bool:
        """Load embeddings and documents from cache if unchanged"""
        cache_file = self.cache_dir / f"embeddings_{self.model_name.replace('/', '_')}.pkl"
        hash_file = self.cache_dir / "content_hash.txt"
        
        if not cache_file.exists() or not hash_file.exists():
            return False
        
        try:
            # Check if content has changed
            current_hash = self._compute_content_hash()
            cached_hash = hash_file.read_text().strip()
            
            if current_hash != cached_hash:
                print("📝 Content changed, rebuilding index...")
                return False
            
            # Load from cache
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.embeddings = cache_data['embeddings']
            self.documents = cache_data['documents']
            self.content_hash = cached_hash
            
            print(f"⚡ Loaded {len(self.documents)} documents from cache")
            return True
            
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            return False
    
    def _build_index(self):
        """Build vector search index at paragraph level"""
        print("🔍 Building paragraph-level search index...")
        start_time = time.time()
        
        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        self.documents = []
        
        for file_path in md_files:
            try:
                content = file_path.read_text()
                
                # Extract file title from first heading or filename
                lines = content.split('\n')
                file_title = None
                for line in lines[:10]:
                    if line.startswith('# '):
                        file_title = line[2:].strip()
                        break
                if not file_title:
                    file_title = file_path.stem.replace('-', ' ').replace('_', ' ').title()
                
                # Split into paragraphs and sections
                paragraphs = self._extract_paragraphs(content)
                
                for para_idx, paragraph_data in enumerate(paragraphs):
                    if len(paragraph_data['text'].strip()) > 50:  # Skip very short paragraphs
                        doc = {
                            'file_path': file_path,
                            'file_title': file_title,
                            'title': paragraph_data['title'],
                            'content': paragraph_data['text'],
                            'context': paragraph_data['context'],
                            'section': paragraph_data['section'],
                            'para_index': para_idx,
                            'themes': self._extract_themes(paragraph_data['text']),
                            'word_count': len(paragraph_data['text'].split())
                        }
                        self.documents.append(doc)
                
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
                continue
        
        # Generate embeddings
        if self.documents:
            texts = [f"{doc['title']}\n\n{doc['content']}" for doc in self.documents]
            model = self._get_model()
            print(f"🚀 Encoding {len(texts)} documents...")
            self.embeddings = model.encode(texts, show_progress_bar=True, convert_to_tensor=False)
            
            # Cache results
            cache_data = {
                'embeddings': self.embeddings,
                'documents': self.documents
            }
            
            cache_file = self.cache_dir / f"embeddings_{self.model_name.replace('/', '_')}.pkl"
            hash_file = self.cache_dir / "content_hash.txt"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.content_hash = self._compute_content_hash()
            hash_file.write_text(self.content_hash)
        
        build_time = time.time() - start_time
        print(f"✅ Built index in {build_time:.2f}s ({len(self.documents)} documents)")
    
    def _extract_paragraphs(self, content: str) -> List[Dict]:
        """Extract paragraphs with context and section information"""
        lines = content.split('\n')
        paragraphs = []
        
        current_section = "Introduction"
        current_paragraph = []
        
        for line in lines:
            # Track current section
            if line.startswith('#'):
                if line.startswith('##'):
                    current_section = line[2:].strip()
                elif line.startswith('# '):
                    current_section = line[2:].strip()
            
            # Check if line starts a new paragraph (non-empty after empty lines)
            elif line.strip() and (not current_paragraph or 
                                 not any(p.strip() for p in current_paragraph[-3:])):
                # Save previous paragraph if it exists
                if current_paragraph:
                    para_text = '\n'.join(current_paragraph).strip()
                    if para_text and len(para_text) > 20:
                        paragraphs.append({
                            'text': para_text,
                            'title': f"{current_section} - Para {len(paragraphs) + 1}",
                            'section': current_section,
                            'context': f"From {current_section}"
                        })
                
                # Start new paragraph
                current_paragraph = [line]
            
            # Continue current paragraph
            elif line.strip():
                current_paragraph.append(line)
            
            # Empty line - could end paragraph
            elif current_paragraph:
                current_paragraph.append(line)
        
        # Add final paragraph
        if current_paragraph:
            para_text = '\n'.join(current_paragraph).strip()
            if para_text and len(para_text) > 20:
                paragraphs.append({
                    'text': para_text,
                    'title': f"{current_section} - Para {len(paragraphs) + 1}",
                    'section': current_section,
                    'context': f"From {current_section}"
                })
        
        return paragraphs
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract semantic themes from content"""
        themes = set()
        
        # Look for section headers
        for line in content.split('\n'):
            if line.startswith('##'):
                theme = line[2:].strip().lower()
                # Clean up theme
                theme = re.sub(r'[^a-zA-Z\s]', '', theme).strip()
                if theme and len(theme) > 3:
                    themes.add(theme)
        
        # Look for emphasized concepts (words in **bold** or *italic*)
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', content)
        italic_matches = re.findall(r'\*([^*]+)\*', content)
        
        for match in bold_matches + italic_matches:
            clean_match = re.sub(r'[^a-zA-Z\s]', '', match).strip().lower()
            if clean_match and len(clean_match) > 3:
                themes.add(clean_match)
        
        # Look for key conceptual phrases
        key_phrases = re.findall(r'\b(?:process|pattern|system|approach|method|technique|concept|principle)\w*\b', 
                                content.lower())
        for phrase in key_phrases:
            if len(phrase) > 3:
                themes.add(phrase)
        
        return list(themes)[:8]  # Limit to top 8 themes
    
    def ensure_index_built(self):
        """Ensure search index is built"""
        if self.embeddings is None:
            if not self._load_cache():
                self._build_index()
    
    def _compute_string_score(self, query: str, content: str) -> float:
        """Compute string matching score"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Exact phrase match gets high score
        if query_lower in content_lower:
            return len(query) / len(content) * 100
        
        # Word-based matching
        query_words = query_lower.split()
        content_words = content_lower.split()
        
        matches = sum(1 for word in query_words if word in content_words)
        if matches > 0:
            return matches / len(query_words) * 10
        
        return 0.0
    
    def _extract_snippets(self, query: str, content: str, max_snippets: int = 3) -> List[str]:
        """Extract relevant snippets around query matches"""
        query_lower = query.lower()
        
        snippets = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Get context around the match
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context_lines = lines[start:end]
                
                snippet = ' '.join(context_lines).strip()
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
                if len(snippets) >= max_snippets:
                    break
        
        return snippets
    
    def search(self, 
               query: str,
               top_k: int = 5,
               min_score: float = 0.1) -> Tuple[List[MindfulSearchResult], SearchStats]:
        """
        Perform mindful vector search
        
        Args:
            query: Search query (can be concept, feeling, or question)
            top_k: Number of results to return  
            min_score: Minimum combined score threshold
        """
        start_time = time.time()
        
        # Ensure index is built
        self.ensure_index_built()
        
        if not self.documents or self.embeddings is None:
            return [], SearchStats(query, 0, 0, False)
        
        # Encode query
        model = self._get_model()
        query_embedding = model.encode([query], convert_to_tensor=False)
        
        # Compute vector similarities (cosine similarity)
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Create results with hybrid scoring
        results = []
        for i, doc in enumerate(self.documents):
            vector_score = float(similarities[i])
            string_score = self._compute_string_score(query, doc['content'])
            
            # Weighted combination (favor vector similarity for semantic search)
            combined_score = (vector_score * 0.7) + (string_score * 0.3)
            
            if combined_score >= min_score:
                snippets = self._extract_snippets(query, doc['content'])
                
                result = MindfulSearchResult(
                    file_path=doc['file_path'],
                    file_title=doc['file_title'],
                    title=doc['title'], 
                    content=doc['content'],
                    section=doc['section'],
                    context=doc['context'],
                    para_index=doc['para_index'],
                    vector_score=vector_score,
                    string_score=string_score,
                    combined_score=combined_score,
                    matching_snippets=snippets,
                    semantic_themes=doc['themes']
                )
                results.append(result)
        
        # Sort by combined score and take top results
        results.sort(key=lambda x: x.combined_score, reverse=True)
        top_results = results[:top_k]
        
        search_time = (time.time() - start_time) * 1000
        stats = SearchStats(
            query=query,
            total_results=len(top_results),
            search_time_ms=search_time,
            cache_hit=self.content_hash is not None
        )
        
        return top_results, stats


if __name__ == "__main__":
    # Demo usage
    print("🧘 Mindful Vector Search Demo")
    
    search_engine = MindfulVectorSearch()
    
    # Test queries
    test_queries = [
        "attention and awareness",
        "processing patterns", 
        "computational breath",
        "pattern detection",
        "evidence requirements"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching: '{query}'")
        results, stats = search_engine.search(query, top_k=3)
        
        print(f"📊 Found {stats.total_results} results in {stats.search_time_ms:.1f}ms")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.section} - Paragraph {result.para_index}")
            print(f"   📁 {result.file_title}")
            print(f"   📍 {result.file_path.name}")
            print(f"   📈 Score: {result.combined_score:.3f} (vector: {result.vector_score:.3f}, string: {result.string_score:.3f})")
            print(f"   📝 Content: {result.content[:150]}...")
            if result.semantic_themes:
                print(f"   🏷️  Themes: {', '.join(result.semantic_themes[:3])}")