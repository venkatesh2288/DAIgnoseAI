import os
import pickle
import json
from typing import List, Dict
import logging
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class VectorStore:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        self.documents = []  # Store document metadata
        self.vectors = None  # Store TF-IDF vectors
        self.vector_store_path = 'data/vector_store'
        self.is_fitted = False
        
        # Create directory if it doesn't exist
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def add_document(self, content: str, file_id: int, filename: str):
        """Add a document to the vector store"""
        try:
            # Split content into chunks for better retrieval
            chunks = self._split_into_chunks(content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 50:  # Only add substantial chunks
                    # Store metadata
                    doc_metadata = {
                        'file_id': file_id,
                        'filename': filename,
                        'chunk_id': i,
                        'content': chunk
                    }
                    self.documents.append(doc_metadata)
            
            # Rebuild vectorizer with all documents
            self._rebuild_vectors()
            
            # Save updated index
            self._save_index()
            logging.info(f"Added {len(chunks)} chunks from file {filename} to vector store")
            
        except Exception as e:
            logging.error(f"Error adding document to vector store: {str(e)}")
    
    def search_similar_content(self, query: str, file_id: int = None, top_k: int = 3) -> str:
        """Search for similar content in the vector store"""
        try:
            if not self.documents or not self.is_fitted:
                return "No documents available for search."
            
            # Transform query using the fitted vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-top_k*2:][::-1]  # Get more than needed for filtering
            
            relevant_chunks = []
            seen_chunks = set()
            
            for idx in top_indices:
                if idx < len(self.documents) and similarities[idx] > 0.1:  # Minimum similarity threshold
                    doc = self.documents[idx]
                    
                    # Filter by file_id if specified
                    if file_id and doc['file_id'] != file_id:
                        continue
                    
                    # Avoid duplicate chunks
                    chunk_key = (doc['file_id'], doc['chunk_id'])
                    if chunk_key in seen_chunks:
                        continue
                    
                    seen_chunks.add(chunk_key)
                    relevant_chunks.append({
                        'content': doc['content'],
                        'score': float(similarities[idx]),
                        'filename': doc['filename']
                    })
                    
                    if len(relevant_chunks) >= top_k:
                        break
            
            if not relevant_chunks:
                return "No relevant content found."
            
            # Format results
            context_parts = []
            for chunk in relevant_chunks:
                context_parts.append(f"From {chunk['filename']} (relevance: {chunk['score']:.2f}):\n{chunk['content']}")
            
            return "\n\n---\n\n".join(context_parts)
            
        except Exception as e:
            logging.error(f"Error searching vector store: {str(e)}")
            return f"Error retrieving relevant content: {str(e)}"
    
    def delete_document(self, file_id: int):
        """Delete all chunks related to a specific file"""
        try:
            # Remove documents with matching file_id
            original_count = len(self.documents)
            self.documents = [doc for doc in self.documents if doc['file_id'] != file_id]
            removed_count = original_count - len(self.documents)
            
            if removed_count > 0:
                # Rebuild vectors
                self._rebuild_vectors()
                
                # Save updated index
                self._save_index()
                logging.info(f"Deleted {removed_count} chunks for file_id {file_id}")
            
        except Exception as e:
            logging.error(f"Error deleting document from vector store: {str(e)}")
    
    def _rebuild_vectors(self):
        """Rebuild TF-IDF vectors from all documents"""
        if not self.documents:
            self.vectors = None
            self.is_fitted = False
            return
        
        # Extract all content
        all_content = [doc['content'] for doc in self.documents]
        
        # Fit and transform
        self.vectors = self.vectorizer.fit_transform(all_content)
        self.is_fitted = True
    
    def _split_into_chunks(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split content into overlapping chunks"""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks if chunks else [content]  # Return original if no chunks created
    
    def _save_index(self):
        """Save the vectorizer and metadata to disk"""
        try:
            # Save vectorizer
            vectorizer_path = os.path.join(self.vector_store_path, 'vectorizer.pkl')
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Save vectors
            if self.vectors is not None:
                vectors_path = os.path.join(self.vector_store_path, 'vectors.pkl')
                with open(vectors_path, 'wb') as f:
                    pickle.dump(self.vectors, f)
            
            # Save metadata
            metadata_path = os.path.join(self.vector_store_path, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'documents': self.documents,
                    'is_fitted': self.is_fitted
                }, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving vector store: {str(e)}")
    
    def _load_index(self):
        """Load the vectorizer and metadata from disk"""
        try:
            vectorizer_path = os.path.join(self.vector_store_path, 'vectorizer.pkl')
            vectors_path = os.path.join(self.vector_store_path, 'vectors.pkl')
            metadata_path = os.path.join(self.vector_store_path, 'metadata.json')
            
            if os.path.exists(metadata_path):
                # Load metadata
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
                    self.is_fitted = data.get('is_fitted', False)
                
                # Load vectorizer if available
                if os.path.exists(vectorizer_path) and self.is_fitted:
                    with open(vectorizer_path, 'rb') as f:
                        self.vectorizer = pickle.load(f)
                
                # Load vectors if available
                if os.path.exists(vectors_path) and self.is_fitted:
                    with open(vectors_path, 'rb') as f:
                        self.vectors = pickle.load(f)
                
                logging.info(f"Loaded vector store with {len(self.documents)} documents")
            
        except Exception as e:
            logging.error(f"Error loading vector store: {str(e)}")
            # Initialize empty store if loading fails
            self.documents = []
            self.vectors = None
            self.is_fitted = False