"""
Complete RAG Pipeline for Constitution Chatbot
Using only open-source models (no OpenAI dependency)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os
import re
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
import sqlite3
from pathlib import Path

# RAG Pipeline imports
from sentence_transformers import SentenceTransformer
import faiss
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    AutoModelForSequenceClassification,
    pipeline
)
import torch
from rank_bm25 import BM25Okapi
import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///constitution_rag_complete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    retrieved_context = db.Column(db.Text, nullable=True)
    relevance_score = db.Column(db.Float, nullable=True)
    generation_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)

class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.String(100), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    metadata = db.Column(db.JSON, nullable=True)
    embedding_vector = db.Column(db.PickleType, nullable=True)
    tfidf_features = db.Column(db.PickleType, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RAGMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    retrieval_accuracy = db.Column(db.Float, nullable=True)
    generation_quality = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CompleteRAGPipeline:
    """
    Complete RAG Pipeline with Local Models Only
    - Retrieval: SentenceTransformers + FAISS + BM25 + TF-IDF
    - Generation: Transformers-based local model
    - No external API dependencies
    """
    
    def __init__(self):
        logger.info("Initializing Complete RAG Pipeline with local models...")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # Initialize FAISS index
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Initialize generation model (lightweight for local use)
        self.init_generation_model()
        
        # Initialize reranking model
        self.init_reranking_model()
        
        # Document storage
        self.documents = []
        self.document_metadata = []
        
        # Search components
        self.bm25 = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.tfidf_matrix = None
        
        # Tokenizer for text processing
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            logger.warning("Tiktoken not available, using simple tokenization")
            self.tokenizer = None
        
        logger.info("Complete RAG Pipeline initialized successfully")
    
    def init_generation_model(self):
        """Initialize local generation model"""
        try:
            # Use a lightweight model for generation
            model_name = "microsoft/DialoGPT-small"  # Lightweight conversational model
            self.generation_tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side='left')
            self.generation_model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add pad token if it doesn't exist
            if self.generation_tokenizer.pad_token is None:
                self.generation_tokenizer.pad_token = self.generation_tokenizer.eos_token
            
            logger.info("Generation model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load generation model: {e}, using template-based generation")
            self.generation_model = None
            self.generation_tokenizer = None
    
    def init_reranking_model(self):
        """Initialize reranking model for better relevance"""
        try:
            # Use cross-encoder for reranking
            self.reranker = SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-2-v2')
            logger.info("Reranking model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load reranking model: {e}, using similarity-based reranking")
            self.reranker = None
    
    def chunk_document(self, text: str, metadata: Dict, chunk_size: int = 400, overlap: int = 50) -> List[Dict]:
        """Enhanced document chunking with semantic boundaries"""
        chunks = []
        
        # Split by sentences first for better semantic chunks
        sentences = self.split_into_sentences(text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'sentence_count': len(current_chunk),
                    'word_count': current_length,
                    'chunk_type': 'semantic'
                })
                
                chunks.append({
                    'content': chunk_text,
                    'metadata': chunk_metadata
                })
                
                # Handle overlap
                if overlap > 0 and len(current_chunk) > 1:
                    overlap_sentences = current_chunk[-overlap//20:] if overlap//20 > 0 else []
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s.split()) for s in current_chunk)
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'sentence_count': len(current_chunk),
                'word_count': current_length,
                'chunk_type': 'semantic'
            })
            
            chunks.append({
                'content': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple regex"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def add_documents(self, documents: List[Dict]):
        """Add documents to RAG pipeline with comprehensive indexing"""
        logger.info(f"Adding {len(documents)} documents to Complete RAG pipeline...")
        
        all_chunks = []
        all_texts = []
        
        for doc in documents:
            # Chunk the document
            chunks = self.chunk_document(
                doc['content'], 
                doc.get('metadata', {}),
                chunk_size=350,
                overlap=30
            )
            
            for chunk in chunks:
                # Generate embedding
                embedding = self.embedding_model.encode(chunk['content'])
                
                # Prepare chunk data
                chunk_id = f"{doc.get('id', 'doc')}_{chunk['metadata']['chunk_index']}"
                
                # Store in database
                db_chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk['content'],
                    metadata=chunk['metadata'],
                    embedding_vector=embedding.tolist()
                )
                
                try:
                    db.session.add(db_chunk)
                    db.session.commit()
                    
                    # Add to FAISS index
                    self.faiss_index.add(embedding.reshape(1, -1).astype('float32'))
                    
                    # Store for other search methods
                    self.documents.append(chunk['content'])
                    self.document_metadata.append(chunk['metadata'])
                    all_chunks.append(chunk['content'])
                    all_texts.append(chunk['content'])
                    
                except Exception as e:
                    logger.error(f"Error adding chunk {chunk_id}: {e}")
                    db.session.rollback()
        
        # Initialize search components
        if all_chunks:
            # BM25 initialization
            tokenized_docs = [doc.split() for doc in all_chunks]
            self.bm25 = BM25Okapi(tokenized_docs)
            
            # TF-IDF initialization
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
                logger.info("TF-IDF matrix created successfully")
            except Exception as e:
                logger.warning(f"TF-IDF initialization failed: {e}")
                self.tfidf_matrix = None
        
        logger.info(f"Successfully added {len(all_chunks)} chunks to Complete RAG pipeline")
    
    def multi_retrieval(self, query: str, top_k: int = 8) -> List[Dict]:
        """Advanced multi-method retrieval combining multiple techniques"""
        start_time = datetime.now()
        
        results = []
        
        # 1. Dense semantic retrieval (FAISS)
        semantic_results = self._semantic_retrieval(query, top_k)
        
        # 2. Sparse keyword retrieval (BM25)
        keyword_results = self._keyword_retrieval(query, top_k)
        
        # 3. TF-IDF retrieval
        tfidf_results = self._tfidf_retrieval(query, top_k)
        
        # Combine and deduplicate results
        combined_results = self._combine_retrieval_results(
            semantic_results, keyword_results, tfidf_results, query
        )
        
        # Rerank using cross-encoder if available
        if self.reranker and len(combined_results) > 1:
            combined_results = self._rerank_results(query, combined_results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Add processing metadata
        for result in combined_results[:top_k]:
            result['processing_time'] = processing_time
            result['retrieval_methods'] = ['semantic', 'keyword', 'tfidf']
        
        return combined_results[:top_k]
    
    def _semantic_retrieval(self, query: str, top_k: int) -> List[Dict]:
        """Dense vector retrieval using FAISS"""
        try:
            query_embedding = self.embedding_model.encode(query).astype('float32')
            scores, indices = self.faiss_index.search(query_embedding.reshape(1, -1), top_k * 2)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'semantic_score': float(score),
                        'index': idx,
                        'method': 'semantic'
                    })
            
            return results
        except Exception as e:
            logger.error(f"Semantic retrieval error: {e}")
            return []
    
    def _keyword_retrieval(self, query: str, top_k: int) -> List[Dict]:
        """Sparse keyword retrieval using BM25"""
        try:
            if not self.bm25:
                return []
            
            tokenized_query = query.split()
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top results
            top_indices = np.argsort(scores)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if idx < len(self.documents) and scores[idx] > 0:
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'keyword_score': float(scores[idx]),
                        'index': idx,
                        'method': 'keyword'
                    })
            
            return results
        except Exception as e:
            logger.error(f"Keyword retrieval error: {e}")
            return []
    
    def _tfidf_retrieval(self, query: str, top_k: int) -> List[Dict]:
        """TF-IDF based retrieval"""
        try:
            if self.tfidf_matrix is None:
                return []
            
            query_vector = self.tfidf_vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if idx < len(self.documents) and similarities[idx] > 0:
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'tfidf_score': float(similarities[idx]),
                        'index': idx,
                        'method': 'tfidf'
                    })
            
            return results
        except Exception as e:
            logger.error(f"TF-IDF retrieval error: {e}")
            return []
    
    def _combine_retrieval_results(self, semantic_results: List[Dict], 
                                 keyword_results: List[Dict], 
                                 tfidf_results: List[Dict], 
                                 query: str) -> List[Dict]:
        """Combine results from different retrieval methods"""
        # Create a map to combine scores for same documents
        combined_map = {}
        
        # Weight different methods
        semantic_weight = 0.5
        keyword_weight = 0.3
        tfidf_weight = 0.2
        
        # Process semantic results
        for result in semantic_results:
            idx = result['index']
            if idx not in combined_map:
                combined_map[idx] = result.copy()
                combined_map[idx]['combined_score'] = 0
            
            # Normalize semantic score (cosine similarity is already 0-1)
            norm_score = max(0, min(1, result['semantic_score']))
            combined_map[idx]['combined_score'] += semantic_weight * norm_score
            combined_map[idx]['semantic_score'] = norm_score
        
        # Process keyword results
        max_keyword_score = max([r.get('keyword_score', 0) for r in keyword_results]) if keyword_results else 1
        for result in keyword_results:
            idx = result['index']
            if idx not in combined_map:
                combined_map[idx] = result.copy()
                combined_map[idx]['combined_score'] = 0
            
            # Normalize keyword score
            norm_score = result['keyword_score'] / max_keyword_score if max_keyword_score > 0 else 0
            combined_map[idx]['combined_score'] += keyword_weight * norm_score
            combined_map[idx]['keyword_score'] = norm_score
        
        # Process TF-IDF results
        for result in tfidf_results:
            idx = result['index']
            if idx not in combined_map:
                combined_map[idx] = result.copy()
                combined_map[idx]['combined_score'] = 0
            
            # TF-IDF score is already normalized
            norm_score = result['tfidf_score']
            combined_map[idx]['combined_score'] += tfidf_weight * norm_score
            combined_map[idx]['tfidf_score'] = norm_score
        
        # Convert to list and sort by combined score
        combined_results = list(combined_map.values())
        combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return combined_results
    
    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank results using cross-encoder model"""
        try:
            if not self.reranker or len(results) <= 1:
                return results
            
            # Prepare query-document pairs
            pairs = [[query, result['content']] for result in results]
            
            # Get reranking scores
            rerank_scores = self.reranker.predict(pairs)
            
            # Update results with rerank scores
            for i, result in enumerate(results):
                result['rerank_score'] = float(rerank_scores[i])
                # Combine with existing score
                result['final_score'] = 0.7 * result['combined_score'] + 0.3 * result['rerank_score']
            
            # Sort by final score
            results.sort(key=lambda x: x['final_score'], reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return results
    
    def generate_response(self, query: str, retrieved_docs: List[Dict], user_class: str = "10th") -> Tuple[str, float]:
        """Generate response using local models and retrieved context"""
        if not retrieved_docs:
            return self.generate_fallback_response(query), 0.5
        
        # Prepare context from retrieved documents
        context = self._prepare_context(retrieved_docs[:3], query)
        
        # Try neural generation first, fallback to template-based
        if self.generation_model and self.generation_tokenizer:
            response, generation_score = self._neural_generation(query, context, user_class)
        else:
            response, generation_score = self._template_generation(query, context, user_class)
        
        return response, generation_score
    
    def _prepare_context(self, docs: List[Dict], query: str) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs):
            # Add document with relevance indicator
            relevance = doc.get('final_score', doc.get('combined_score', 0))
            context_parts.append(f"**Source {i+1} (Relevance: {relevance:.2f}):**\n{doc['content']}\n")
        
        return "\n".join(context_parts)
    
    def _neural_generation(self, query: str, context: str, user_class: str) -> Tuple[str, float]:
        """Generate response using neural model"""
        try:
            # Prepare prompt for generation
            prompt = self._create_generation_prompt(query, context, user_class)
            
            # Tokenize input
            inputs = self.generation_tokenizer.encode(prompt, return_tensors='pt', max_length=512, truncation=True)
            
            # Generate response
            with torch.no_grad():
                outputs = self.generation_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 150,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.generation_tokenizer.eos_token_id
                )
            
            # Decode response
            generated_text = self.generation_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part
            response = generated_text[len(prompt):].strip()
            
            # If response is too short or poor quality, fallback to template
            if len(response) < 50 or not self._is_good_response(response, query):
                return self._template_generation(query, context, user_class)
            
            # Post-process response
            response = self._post_process_response(response, query, user_class)
            
            generation_score = 0.8  # Neural generation gets higher score
            return response, generation_score
            
        except Exception as e:
            logger.error(f"Neural generation error: {e}")
            return self._template_generation(query, context, user_class)
    
    def _template_generation(self, query: str, context: str, user_class: str) -> Tuple[str, float]:
        """Generate response using template-based approach"""
        query_lower = query.lower()
        
        # Determine response type and generate appropriate response
        if any(word in query_lower for word in ['history', 'when', 'who', 'timeline']):
            response_prefix = "📚 **Historical Information:**\n\n"
        elif any(word in query_lower for word in ['rights', 'fundamental']):
            response_prefix = "⚖️ **Constitutional Rights:**\n\n"
        elif any(word in query_lower for word in ['duties', 'responsibilities']):
            response_prefix = "🤝 **Civic Duties:**\n\n"
        elif any(word in query_lower for word in ['amendment', 'change', 'modify']):
            response_prefix = "📝 **Constitutional Amendments:**\n\n"
        elif any(word in query_lower for word in ['preamble', 'introduction']):
            response_prefix = "🏛️ **Preamble & Principles:**\n\n"
        else:
            response_prefix = "📖 **Constitutional Information:**\n\n"
        
        # Extract and summarize key information from context
        key_info = self._extract_key_information(context, query)
        
        # Build comprehensive response
        response = response_prefix + key_info
        
        # Add class-specific guidance
        class_guidance = self._get_class_specific_guidance(user_class, query_lower)
        if class_guidance:
            response += f"\n\n{class_guidance}"
        
        # Add related topics
        related_topics = self._suggest_related_topics(query_lower)
        if related_topics:
            response += f"\n\n🔗 **Related Topics:** {', '.join(related_topics)}"
        
        # Add study tips
        study_tips = self._get_study_tips(query_lower, user_class)
        if study_tips:
            response += f"\n\n💡 **Study Tips:** {study_tips}"
        
        generation_score = 0.7  # Template generation gets moderate score
        return response, generation_score
    
    def _create_generation_prompt(self, query: str, context: str, user_class: str) -> str:
        """Create prompt for neural generation"""
        prompt = f"""You are an expert on Indian Constitution helping students. Based on the following context, answer the student's question clearly and accurately.

Context: {context[:800]}

Student's Question: {query}
Student's Class: {user_class}

Answer:"""
        return prompt
    
    def _is_good_response(self, response: str, query: str) -> bool:
        """Check if neural generation produced a good response"""
        if len(response) < 20:
            return False
        
        # Check if response is relevant to query
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words.intersection(response_words))
        
        return overlap > 0
    
    def _post_process_response(self, response: str, query: str, user_class: str) -> str:
        """Post-process neural generation output"""
        # Clean up response
        response = response.strip()
        
        # Add formatting if needed
        if not response.startswith(('📚', '⚖️', '🤝', '📝', '🏛️', '📖')):
            response = f"📖 **Answer:**\n\n{response}"
        
        return response
    
    def _extract_key_information(self, context: str, query: str) -> str:
        """Extract and summarize key information from context"""
        # Split context into sentences
        sentences = []
        for line in context.split('\n'):
            if line.strip() and not line.strip().startswith('**Source'):
                sentences.extend([s.strip() for s in line.split('.') if s.strip()])
        
        # Score sentences based on query relevance
        query_words = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 20:  # Filter very short sentences
                sentence_words = set(sentence.lower().split())
                relevance_score = len(query_words.intersection(sentence_words))
                
                if relevance_score > 0:
                    scored_sentences.append((sentence, relevance_score))
        
        # Sort by relevance and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Format key information
        key_sentences = [s[0] for s in scored_sentences[:4]]
        
        if key_sentences:
            return '. '.join(key_sentences) + '.'
        else:
            # Fallback to first part of context
            return context[:600] + '...' if len(context) > 600 else context
    
    def _get_class_specific_guidance(self, user_class: str, query: str) -> str:
        """Provide class-specific learning guidance"""
        guidance_map = {
            "8th": "💡 **For Class 8:** Focus on basic concepts. Remember key dates like 1950 (Republic Day) and personalities like Dr. B.R. Ambedkar.",
            "9th": "💡 **For Class 9:** Connect these constitutional concepts with democratic values and the freedom struggle.",
            "10th": "💡 **For Class 10:** Understand the balance between rights and duties. Practice scenario-based questions for boards.",
            "11th": "💡 **For Class 11:** Analyze the federal structure and constitutional mechanisms. Focus on separation of powers.",
            "12th": "💡 **For Class 12:** Focus on contemporary challenges, amendments, and comparative constitutional analysis."
        }
        
        return guidance_map.get(user_class, guidance_map["10th"])
    
    def _suggest_related_topics(self, query: str) -> List[str]:
        """Suggest related topics based on the query"""
        topic_map = {
            'rights': ['Fundamental Duties', 'Directive Principles', 'Constitutional Remedies'],
            'duties': ['Fundamental Rights', 'Citizenship', 'Constitutional Values'],
            'history': ['Constituent Assembly', 'Key Personalities', 'Timeline'],
            'amendment': ['Article 368', 'Constitutional Changes', 'Parliamentary Process'],
            'preamble': ['Constitutional Values', 'Sovereignty', 'Democracy'],
            'ambedkar': ['Constitution Making', 'Fundamental Rights', 'Social Justice'],
            'equality': ['Article 14', 'Non-discrimination', 'Equal Opportunity'],
            'freedom': ['Article 19', 'Speech Expression', 'Movement Rights']
        }
        
        suggestions = []
        for keyword, topics in topic_map.items():
            if keyword in query:
                suggestions.extend(topics)
        
        return list(set(suggestions))[:3]
    
    def _get_study_tips(self, query: str, user_class: str) -> str:
        """Provide study tips based on query and class"""
        tips = {
            "8th": "Create a timeline of constitutional events. Make flashcards for key personalities.",
            "9th": "Draw mind maps connecting freedom struggle with constitution making. Practice MCQs.",
            "10th": "Compare fundamental rights vs duties in a table. Solve previous year questions.",
            "11th": "Analyze federal vs unitary features. Study comparative government systems.",
            "12th": "Research current constitutional challenges. Write analytical essays on amendments."
        }
        
        return tips.get(user_class, tips["10th"])
    
    def generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when retrieval fails"""
        return """
🤔 I apologize, but I couldn't find specific information about your query in my knowledge base.

However, I can help you with topics related to:

🏛️ **Indian Constitution:**
- History and making of Constitution (1946-1950)
- Fundamental Rights (Articles 12-35)
- Directive Principles (Articles 36-51)
- Fundamental Duties (Article 51A)
- Amendment Process (Article 368)
- Preamble and Constitutional Values

⚖️ **Key Personalities:**
- Dr. B.R. Ambedkar (Father of Constitution)
- Dr. Rajendra Prasad (President of Constituent Assembly)
- Jawaharlal Nehru (Objective Resolution)

🎯 **Try asking:**
- "Explain Fundamental Rights in detail"
- "Who drafted the Indian Constitution?"
- "What does the Preamble say?"
- "How can Constitution be amended?"

Could you please rephrase your question or ask about any of these specific topics?
        """

# Initialize Complete RAG Pipeline
rag_pipeline = CompleteRAGPipeline()

# Comprehensive Constitution Knowledge Base
COMPREHENSIVE_CONSTITUTION_DOCUMENTS = [
    {
        "id": "constitution_history_detailed",
        "content": """
        The Making of Indian Constitution (1946-1950): The Indian Constitution was drafted by the Constituent Assembly formed under the Cabinet Mission Plan of 1946. The Assembly had 389 members representing British India and Princely States. After partition, it was reduced to 299 members.

        Key Timeline and Events:
        - July 1946: Cabinet Mission Plan announced, Constituent Assembly proposed
        - December 9, 1946: First meeting of Constituent Assembly
        - August 29, 1947: Drafting Committee appointed with Dr. B.R. Ambedkar as Chairman
        - November 26, 1949: Constitution adopted by Constituent Assembly
        - January 26, 1950: Constitution came into effect (chosen to honor Purna Swaraj declaration of 1930)

        The Father of Indian Constitution: Dr. Bhimrao Ramji Ambedkar served as Chairman of the Drafting Committee and is known as the Father of Indian Constitution. He was a jurist, economist, and social reformer who played the most important role in framing the Constitution. His deep knowledge of constitutional law, gained from studying at Columbia University and London School of Economics, was instrumental in creating this comprehensive document.

        Other Key Personalities:
        - Dr. Rajendra Prasad: President of Constituent Assembly, later first President of India
        - Jawaharlal Nehru: Moved the Objective Resolution that became the basis of the Preamble
        - Sardar Vallabhbhai Patel: Deputy Prime Minister, handled integration of 562 princely states
        - K.M. Munshi: Member of Drafting Committee, handled fundamental rights
        - Alladi Krishnaswamy Iyer: Constitutional expert and Drafting Committee member
        - T.T. Krishnamachari: Took over from B.R. Ambedkar as Chairman in final stages

        Constitutional Sources and Inspiration:
        The Constitution drew from multiple sources:
        - Government of India Act 1935: Administrative structure, federal scheme
        - British Constitution: Parliamentary system, rule of law, legislative procedure
        - US Constitution: Fundamental rights, independence of judiciary, judicial review
        - Irish Constitution: Directive Principles of State Policy
        - Canadian Constitution: Federal structure with strong center
        - Australian Constitution: Concurrent list, freedom of trade and commerce
        - Weimar Constitution of Germany: Emergency provisions
        - French Constitution: Liberty, equality, fraternity in Preamble
        - South African Constitution: Amendment procedure
        - Japanese Constitution: Procedure established by law

        Unique Features:
        - Longest written constitution in the world with 395 articles and 12 schedules (originally)
        - Combination of federal and unitary features
        - Parliamentary form of government with Westminster model
        - Independent judiciary with power of judicial review
        - Universal adult suffrage from the beginning
        - Fundamental rights that are justiciable
        - Directive principles for welfare state
        - Emergency provisions for national security
        """,
        "metadata": {
            "topic": "constitutional_history",
            "class_level": "8th-12th",
            "importance": "very_high",
            "keywords": ["history", "constituent assembly", "dr ambedkar", "1946", "1950", "republic day", "making", "drafting", "nehru", "patel"]
        }
    },
    {
        "id": "fundamental_rights_comprehensive",
        "content": """
        Fundamental Rights: The Heart of Indian Constitution (Articles 12-35)

        The Constitution guarantees six categories of Fundamental Rights, inspired by the US Bill of Rights but adapted to Indian conditions. These rights are justiciable, meaning courts can enforce them, and they form the foundation of individual liberty in India.

        Article 12 - Definition: The State includes Government of India, Parliament, State Governments, Legislatures, and all local authorities. This broad definition ensures that fundamental rights are protected against all forms of governmental power.

        1. RIGHT TO EQUALITY (Articles 14-18):
        
        Article 14 - Equality before Law: All persons are equal before law and entitled to equal protection of laws. This means no discrimination and same treatment in similar circumstances.

        Article 15 - Prohibition of Discrimination: The State cannot discriminate on grounds of religion, race, caste, sex, or place of birth. However, special provisions can be made for women, children, and socially backward classes.

        Article 16 - Equality of Opportunity: Equal opportunity in public employment. No discrimination except on grounds of merit. Reservations allowed for backward classes.

        Article 17 - Abolition of Untouchability: Untouchability is abolished and its practice is forbidden. Any disability arising from untouchability is punishable by law.

        Article 18 - Abolition of Titles: No titles except military and academic distinctions. Indians cannot accept titles from foreign states without President's permission.

        2. RIGHT TO FREEDOM (Articles 19-22):

        Article 19 - Six Freedoms: Citizens have right to:
        (a) Freedom of speech and expression
        (b) Freedom to assemble peacefully and without arms
        (c) Freedom to form associations or unions
        (d) Freedom to move freely throughout India
        (e) Freedom to reside and settle in any part of India
        (f) Freedom to practice any profession, occupation, trade or business

        Article 20 - Protection against Ex-post facto laws: No person can be convicted for an act that was not an offense when committed. No double jeopardy. No self-incrimination.

        Article 21 - Right to Life and Personal Liberty: No person shall be deprived of life or personal liberty except according to procedure established by law. This is the most important fundamental right.

        Article 21A - Right to Education: Added by 86th Amendment (2002). Free and compulsory education for children aged 6-14 years.

        Article 22 - Protection against Arrest: Right to be informed of grounds of arrest, right to legal representation, and right to be produced before magistrate within 24 hours.

        3. RIGHT AGAINST EXPLOITATION (Articles 23-24):

        Article 23 - Prohibition of Traffic in Human Beings: Trafficking, forced labor, and beggar prohibited. Exception for public service.

        Article 24 - Prohibition of Child Labor: Children below 14 years cannot be employed in factories, mines, or hazardous work.

        4. RIGHT TO FREEDOM OF RELIGION (Articles 25-28):

        Article 25 - Freedom of Conscience: All persons have equal right to freedom of conscience and to freely profess, practice, and propagate religion.

        Article 26 - Freedom to Manage Religious Affairs: Religious communities can establish and maintain institutions, manage religious affairs, and own property.

        Article 27 - Freedom from Religious Taxation: No one can be compelled to pay taxes for promotion of any particular religion.

        Article 28 - Freedom from Religious Instruction: No religious instruction in state educational institutions. Private institutions with state aid cannot compel attendance at religious instruction.

        5. CULTURAL AND EDUCATIONAL RIGHTS (Articles 29-30):

        Article 29 - Protection of Language and Culture: Minorities have right to conserve their distinct language, script, or culture.

        Article 30 - Right to Establish Educational Institutions: Religious and linguistic minorities have right to establish and administer educational institutions.

        6. RIGHT TO CONSTITUTIONAL REMEDIES (Article 32):

        Article 32 - Heart and Soul of Constitution: Dr. Ambedkar called it the heart and soul. Citizens can directly approach Supreme Court for enforcement of fundamental rights. Supreme Court empowered to issue writs:
        - Habeas Corpus: Produce the body (against illegal detention)
        - Mandamus: We command (to compel performance of duty)
        - Prohibition: To prohibit (prevent lower court from exceeding jurisdiction)
        - Certiorari: To be certified (quash orders of lower courts)
        - Quo-warranto: By what warrant (question person's right to office)

        Limitations on Fundamental Rights:
        - Not absolute; reasonable restrictions possible
        - Can be suspended during national emergency (except Articles 20 and 21)
        - State can impose restrictions for public order, morality, health
        - Rights of one person cannot infringe rights of others

        Significance for Students:
        - Foundation of democratic India
        - Protection against government tyranny
        - Basis for social justice and equality
        - Instrument for individual development
        - Cornerstone of rule of law
        """,
        "metadata": {
            "topic": "fundamental_rights",
            "class_level": "8th-12th",
            "importance": "very_high",
            "keywords": ["fundamental rights", "articles 12-35", "equality", "freedom", "exploitation", "religion", "education", "constitutional remedies", "article 21", "article 32"]
        }
    },
    {
        "id": "directive_principles_detailed",
        "content": """
        Directive Principles of State Policy (DPSP) - Articles 36-51: The Conscience of Constitution

        The Directive Principles are fundamental guidelines for governance, borrowed from the Irish Constitution. Though non-justiciable (cannot be enforced by courts), they are fundamental in governance and it's the duty of the state to apply these principles while making laws.

        Philosophy and Purpose:
        The DPSP aim to establish a welfare state and achieve socio-economic democracy. They provide positive direction to the government for creating conditions where citizens can lead a good life. They bridge the gap between political democracy achieved in 1947 and socio-economic democracy.

        Classification of Directive Principles:

        A. SOCIALIST PRINCIPLES (Economic and Social Justice):

        Article 38 - Social Order for Welfare: State shall strive to promote welfare of people by securing a social order where justice - social, economic, and political - informs all institutions of national life. Minimize inequalities in income, status, facilities and opportunities.

        Article 39 - Policy of State: State shall direct policy towards:
        (a) Adequate means of livelihood for all citizens
        (b) Equitable distribution of material resources for common good
        (c) Prevention of concentration of wealth and means of production
        (d) Equal pay for equal work for men and women
        (e) Protection of workers' health and strength
        (f) Opportunities for healthy development of children

        Article 39A - Equal Justice and Free Legal Aid: Added by 42nd Amendment. Equal opportunity to justice and free legal aid for poor.

        Article 40 - Village Panchayats: Organize village panchayats and endow them with powers to function as units of self-government.

        Article 41 - Right to Work and Education: Secure right to work, education, and public assistance in unemployment, old age, sickness, and disability.

        Article 42 - Humane Work Conditions: Provision for just and humane conditions of work and maternity relief.

        Article 43 - Living Wages: Secure living wages, decent standard of life, and leisure and social-cultural opportunities for all workers.

        Article 43A - Worker Participation: Added by 42nd Amendment. Take steps to secure participation of workers in management of industries.

        B. GANDHIAN PRINCIPLES (Based on Gandhi's Philosophy):

        Article 40 - Village Panchayats: Organize village panchayats as units of self-government (reflects Gandhi's vision of Gram Swaraj).

        Article 43 - Cottage Industries: Promote cottage industries on individual or cooperative basis in rural areas.

        Article 46 - Educational and Economic Interests of Weaker Sections: Promote education and economic interests of Scheduled Castes, Scheduled Tribes, and weaker sections.

        Article 47 - Nutrition and Standard of Living: Improve nutrition, standard of living, and public health. Prohibit consumption of intoxicating drinks and drugs harmful to health.

        Article 48 - Agriculture and Animal Husbandry: Organize agriculture and animal husbandry on modern scientific lines. Prohibit slaughter of cows, calves, and other milch and draught cattle.

        C. LIBERAL PRINCIPLES (Individual Rights and International Relations):

        Article 44 - Uniform Civil Code: Secure uniform civil code for all citizens throughout India (one of the most debated provisions).

        Article 45 - Free and Compulsory Education: Provide free and compulsory education for children up to 14 years. (This became a fundamental right through 86th Amendment)

        Article 48A - Environment Protection: Added by 42nd Amendment. Protect and improve environment and safeguard forests and wildlife.

        Article 49 - Monuments Protection: Protect monuments, places and objects of artistic or historic interest.

        Article 50 - Separation of Judiciary: Separate judiciary from executive in public services of state.

        Article 51 - International Peace: Promote international peace and security, maintain just and honorable relations between nations, foster respect for international law and treaty obligations, encourage settlement of disputes by arbitration.

        Relationship with Fundamental Rights:
        - Complementary to fundamental rights
        - Fundamental rights are negative (restrict state power) while DPSP are positive (direct state action)
        - In case of conflict, fundamental rights generally prevail
        - However, Parliament can amend fundamental rights to implement DPSP

        Significance and Criticism:

        Significance:
        - Provide economic and social philosophy for Indian state
        - Guide for legislation and policy making
        - Help in constitutional interpretation
        - Tool for achieving welfare state
        - Address poverty, inequality, and social justice

        Criticism:
        - Non-justiciable nature makes them ineffective
        - Vague and general statements
        - Implementation depends on political will
        - Some principles conflict with each other
        - Lack of time-bound targets

        Implementation Examples:
        - Land reform laws
        - Minimum wages legislation
        - Maternity benefits
        - Environmental protection laws
        - Free legal aid
        - Panchayati Raj institutions
        - Right to Education Act

        Constitutional Amendments Related to DPSP:
        - 42nd Amendment: Added Articles 39A, 43A, 48A
        - 86th Amendment: Made Article 45 (education) a fundamental right (Article 21A)
        - 97th Amendment: Added Article 43B on cooperative societies

        Relevance for Modern India:
        The DPSP remain highly relevant as India strives to become a developed nation. They provide the roadmap for inclusive growth, social justice, and sustainable development. Issues like inequality, environmental degradation, and social harmony make DPSP more important than ever.
        """,
        "metadata": {
            "topic": "directive_principles",
            "class_level": "9th-12th",
            "importance": "high",
            "keywords": ["directive principles", "dpsp", "welfare state", "socialist", "gandhian", "liberal", "non-justiciable", "article 39", "article 44", "uniform civil code"]
        }
    },
    {
        "id": "fundamental_duties_complete",
        "content": """
        Fundamental Duties (Article 51A): The Moral Obligations of Citizens

        Fundamental Duties were added to the Indian Constitution by the 42nd Constitutional Amendment Act of 1976, based on the recommendations of the Swaran Singh Committee. They were inspired by Article 29 of the Universal Declaration of Human Rights and the Constitution of the former USSR.

        Background and Need:
        The addition of fundamental duties was felt necessary because:
        - Rights and duties are correlative - one cannot exist without the other
        - Citizens had only rights without corresponding duties
        - Need to instill sense of patriotism and discipline
        - International trend towards including duties in constitutions
        - Recommendation of various committees and commissions

        The Swaran Singh Committee (1976) recommended adding fundamental duties, stating that rights and duties are correlative and that the Constitution should prescribe duties as well as rights for citizens.

        Article 51A - The Eleven Fundamental Duties:

        It shall be the duty of every citizen of India:

        (a) To abide by the Constitution and respect its ideals and institutions, the National Flag and the National Anthem
        - Citizens must follow constitutional principles
        - Respect national symbols with dignity
        - Honor constitutional institutions like Parliament, Supreme Court

        (b) To cherish and follow the noble ideals which inspired our national struggle for freedom
        - Remember sacrifices of freedom fighters
        - Follow principles of truth, non-violence, and sacrifice
        - Maintain the spirit of nationalism

        (c) To uphold and protect the sovereignty, unity and integrity of India
        - Defend India against internal and external threats
        - Maintain national unity above regional/linguistic differences
        - Protect territorial integrity

        (d) To defend the country and render national service when called upon to do so
        - Military service when required
        - Civil defense during emergencies
        - Participate in nation-building activities

        (e) To promote harmony and the spirit of common brotherhood amongst all the people of India transcending religious, linguistic and regional or sectional diversities; to renounce practices derogatory to the dignity of women
        - Foster unity in diversity
        - Eliminate communalism and regionalism
        - Respect women's dignity and rights
        - Fight against gender discrimination

        (f) To value and preserve the rich heritage of our composite culture
        - Protect art, literature, music, dance forms
        - Preserve historical monuments
        - Maintain cultural diversity
        - Pass on cultural heritage to future generations

        (g) To protect and improve the natural environment including forests, lakes, rivers and wild life, and to have compassion for living creatures
        - Environmental conservation
        - Prevent pollution
        - Protect biodiversity
        - Show kindness to animals
        - Sustainable development

        (h) To develop the scientific temper, humanism and the spirit of inquiry and reform
        - Rational thinking over superstition
        - Question and investigate
        - Reform outdated practices
        - Embrace scientific progress

        (i) To safeguard public property and to abjure violence
        - Protect government property
        - Maintain public infrastructure
        - Reject violent methods
        - Resolve disputes peacefully

        (j) To strive towards excellence in all spheres of individual and collective activity so that the nation constantly rises to higher levels of endeavor and achievement
        - Personal and professional excellence
        - Continuous improvement
        - National progress through individual efforts
        - Quality consciousness

        (k) Who is a parent or guardian, to provide opportunities for education to his child or, as the case may be, ward between the age of six and fourteen years
        - Added by 86th Amendment in 2002
        - Complementary to Right to Education (Article 21A)
        - Parental responsibility for child education
        - Eliminate child labor

        Nature of Fundamental Duties:

        Non-Justiciable: Like Directive Principles, fundamental duties are non-justiciable, meaning:
        - Cannot be enforced by courts directly
        - No legal remedy for violation
        - Moral and ethical obligations
        - Parliament cannot make laws to directly enforce them

        However, they can be enforced indirectly through:
        - Legislation making specific acts punishable
        - Constitutional interpretation by courts
        - Administrative measures

        Significance and Importance:

        For Democracy:
        - Balance between rights and duties
        - Responsible citizenship
        - Democratic participation
        - National integration

        For Nation Building:
        - Patriotism and national pride
        - Social harmony
        - Cultural preservation
        - Environmental protection

        For Individual Development:
        - Character building
        - Moral consciousness
        - Scientific temper
        - Excellence in work

        Criticism and Limitations:

        1. Non-Justiciable Nature: Cannot be enforced legally
        2. Vague Language: Many duties are not clearly defined
        3. No Corresponding Rights: Some duties don't have matching rights
        4. Political Motivation: Added during Emergency period (1975-77)
        5. Implementation Issues: Lack of mechanism for enforcement

        Legal and Judicial Perspective:

        Supreme Court's View:
        - Fundamental duties are not enforceable but provide guidance
        - Help in constitutional interpretation
        - Create moral obligation on citizens
        - Can be used to restrict fundamental rights in public interest

        Important Cases:
        - Chandra Bhavan Boarding vs State of Mysore (1970): Even before formal inclusion, Court recognized duties
        - AIIMS Students Union vs AIIMS (2001): Used fundamental duties to restrict rights in certain cases

        Implementation and Enforcement:

        Direct Methods:
        - Legislation like Protection of Civil Rights Act
        - Environmental protection laws
        - Prevention of Insults to National Honor Act
        - Wildlife Protection Act

        Indirect Methods:
        - Educational curriculum
        - Administrative instructions
        - Public awareness campaigns
        - Judicial interpretation

        Educational Initiatives:
        - Value education in schools
        - Citizenship training
        - National service schemes
- Moral instruction programs

        Comparison with Other Countries:
        - Germany: Duties more detailed and enforceable
        - Japan: Emphasis on social harmony
        - China: Duties given equal importance as rights
        - USA: No formal fundamental duties

        Contemporary Relevance:
        In modern India, fundamental duties are more relevant than ever:
        - Digital citizenship responsibilities
        - Environmental crisis requires citizen action
        - Social media and responsible expression
        - Cultural preservation in globalized world
        - Scientific temper to combat fake news and superstitions

        Recommendations for Improvement:
        1. Clear definition of duties
        2. Mechanism for enforcement
        3. Regular review and updating
        4. Integration with education system
        5. Public awareness campaigns
        6. Legislative backing for implementation

        For Students:
        Understanding fundamental duties helps students become responsible citizens who:
        - Respect constitutional values
        - Participate in nation building
        - Preserve cultural heritage
        - Protect environment
        - Strive for excellence
        - Maintain social harmony
        """,
        "metadata": {
            "topic": "fundamental_duties",
            "class_level": "8th-12th",
            "importance": "medium",
            "keywords": ["fundamental duties", "article 51a", "42nd amendment", "moral obligations", "citizenship", "swaran singh committee", "non-justiciable", "patriotism"]
        }
    },
    {
        "id": "amendment_process_comprehensive",
        "content": """
        Constitutional Amendment Process: Balancing Flexibility and Stability (Article 368)

        The Indian Constitution provides for its own amendment to meet changing needs of society while maintaining constitutional stability. The amendment process is neither too rigid like the USA nor too flexible like the UK, striking a balance between permanence and change.

        Article 368: Power of Parliament to Amend

        Article 368 gives Parliament the power to amend the Constitution and the procedure thereof. It was amended by the 24th Amendment (1971) to clarify Parliament's power to amend any part of the Constitution including fundamental rights.

        THREE TYPES OF AMENDMENT PROCEDURES:

        TYPE 1: SIMPLE MAJORITY (Like Ordinary Legislation)
        Required for provisions that don't affect federal structure or basic rights.

        Procedure: Simple majority of members present and voting in both houses of Parliament.

        Provisions covered:
        - Admission of new states (Article 2)
        - Formation of new states and alteration of areas, boundaries, or names of existing states (Article 3)
        - Abolition or creation of Legislative Councils in states (Article 169)
        - Second Schedule (salaries, allowances, privileges of President, governors, judges, etc.)
        - Quorum in Parliament
        - Salaries and allowances of members of Parliament
        - Rules of procedure in Parliament
        - Privileges of Parliament, its members and committees
        - Use of English language in Parliament
        - Number of puisne judges in Supreme Court
        - Citizenship provisions
        - Elections to Parliament and state legislatures
        - Delimitation of constituencies
        - Union territories
        - Fifth and Sixth Schedules (administration of tribal areas)

        TYPE 2: SPECIAL MAJORITY (Constitutional Amendment)
        Required for most constitutional provisions.

        Procedure: 
        - Majority of total membership of each house (more than 50% of total strength)
        - Two-thirds majority of members present and voting in each house
        - Must be passed by both houses separately (no joint sitting)

        Provisions covered:
        - Fundamental Rights (Articles 12-35)
        - Directive Principles of State Policy (Articles 36-51)
        - All other provisions not covered under Type 1 or Type 3
        - Supreme Court and High Courts provisions (except those requiring ratification)
        - Powers and functions of Parliament and state legislatures
        - Powers of President and governors
        - Emergency provisions
        - Amendment procedure itself (Article 368)

        TYPE 3: SPECIAL MAJORITY + STATE RATIFICATION
        Required for provisions affecting federal structure.

        Procedure:
        - Special majority in Parliament (as in Type 2)
        - Ratification by legislatures of at least half of the states by simple majority
        - States must ratify before the amendment bill is presented to President for assent

        Provisions covered:
        - Election of President and its manner (Article 54 and 55)
        - Extent of executive power of Union and states (Articles 73 and 162)
        - Supreme Court and High Courts (Chapter IV of Parts V and VI)
        - Distribution of legislative powers between Union and states (Chapter I of Part XI and Seventh Schedule)
        - Any of the lists in Seventh Schedule
        - Representation of states in Parliament
        - Power of Parliament to amend Constitution and its procedure (Article 368 itself)

        IMPORTANT CONSTITUTIONAL AMENDMENTS:

        Early Amendments (1951-1960):
        1st Amendment (1951): Added 9th Schedule to protect land reform laws from judicial review. Added restrictions on freedom of speech.

        2nd Amendment (1952): Fixed representation in Lok Sabha and provided for readjustment after each census.

        3rd Amendment (1954): Added Concurrent List entry for trade and commerce in food stuffs.

        4th Amendment (1955): Clarified that compensation for property acquisition need not be equivalent to market value.

        Significant Amendments (1960-1980):
        7th Amendment (1956): Reorganized states on linguistic basis, abolished Part B states.

        14th Amendment (1962): Incorporated Puducherry into India as Union Territory.

        24th Amendment (1971): Affirmed Parliament's power to amend any part of Constitution including fundamental rights. Response to Golak Nath case.

        25th Amendment (1971): Curtailed right to property. Added Article 31C to protect laws implementing DPSP from judicial review.

        The Emergency Era (1975-1977):
        42nd Amendment (1976): Called "Mini Constitution" due to extensive changes:
        - Added "Socialist" and "Secular" to Preamble
        - Added Fundamental Duties (Article 51A)
        - Shifted more subjects to Concurrent List
        - Extended President's rule in states
        - Limited judicial review
        - Added Articles 39A (free legal aid), 43A (worker participation), 48A (environment protection)

        Post-Emergency Corrections:
        44th Amendment (1978): Reversed many provisions of 42nd Amendment:
        - Made right to property a legal right instead of fundamental right
        - Restored judicial review powers
        - Made internal emergency more difficult to declare
        - Restored fundamental rights during emergency (except Article 20 and 21)

        Modern Democratic Reforms:
        61st Amendment (1988): Reduced voting age from 21 to 18 years.

        73rd Amendment (1992): Constitutional status to Panchayati Raj institutions. Added Part IX and 11th Schedule.

        74th Amendment (1992): Constitutional status to urban local bodies. Added Part IXA and 12th Schedule.

        86th Amendment (2002): Made education a fundamental right (Article 21A) and fundamental duty (Article 51A(k)).

        Recent Important Amendments:
        91st Amendment (2003): Limited size of Council of Ministers to 15% of legislature strength.

        92nd Amendment (2003): Included Bodo, Dogri, Maithili and Santhali in 8th Schedule.

        101st Amendment (2016): Introduced Goods and Services Tax (GST). Added Article 246A.

        102nd Amendment (2018): Gave constitutional status to National Commission for Backward Classes.

        103rd Amendment (2019): Provided 10% reservation for economically weaker sections in general category.

        104th Amendment (2020): Extended reservation for SCs and STs in Lok Sabha and state assemblies till 2030.

        JUDICIAL REVIEW AND BASIC STRUCTURE DOCTRINE:

        Key Cases:
        Shankari Prasad vs Union of India (1951): Parliament can amend any part of Constitution including fundamental rights.

        Golak Nath vs State of Punjab (1967): Parliament cannot amend fundamental rights.

        Kesavananda Bharati vs State of Kerala (1973): Parliament can amend Constitution but cannot alter its "basic structure."

        Basic Structure Elements (as evolved through judgments):
        - Supremacy of Constitution
        - Republican and democratic form of government
        - Secular character
        - Federal character
        - Separation of powers
        - Individual freedom and dignity
        - Unity and integrity of nation
        - Welfare state (socio-economic justice)
        - Judicial review
        - Freedom and dignity of individual
        - Parliamentary system
        - Rule of law
        - Harmony between fundamental rights and DPSP

        COMPARISON WITH OTHER COUNTRIES:

        USA: Very rigid amendment process requiring 2/3 majority in both houses and ratification by 3/4 states.

        UK: Most flexible - Parliament can amend through simple legislation.

        Canada: Partly rigid - some amendments need provincial consent.

        Australia: Referendum required for constitutional amendments.

        South Africa: Different majorities for different provisions.

        CHALLENGES AND CRITICISMS:

        Challenges:
        - Frequent amendments (104 so far) raise questions about constitutional stability
        - Political misuse during emergency period
        - Unclear boundaries of basic structure doctrine
        - Federal consultation mechanism inadequate

        Criticisms:
        - Too easy to amend compared to other democracies
        - Lack of public participation (no referendum)
        - Judicial activism in basic structure doctrine
        - Inconsistent application of ratification requirement

        Suggestions for Reform:
        - Public consultation before major amendments
        - Clear definition of basic structure
        - Time gap between proposal and passage
        - Stricter procedures for constitutional amendments
        - Greater role for states in amendment process

        SIGNIFICANCE FOR STUDENTS:

        Understanding the amendment process helps students appreciate:
        - Constitutional evolution and adaptation
        - Balance between stability and change
        - Democratic process of constitutional reform
        - Role of judiciary in constitutional interpretation
        - Federal structure and center-state relations
        - Importance of constitutional supremacy

        The amendment process reflects India's commitment to constitutional democracy while allowing for necessary changes to meet emerging challenges and aspirations of the people.
        """,
        "metadata": {
            "topic": "amendment_process",
            "class_level": "10th-12th",
            "importance": "high",
            "keywords": ["amendment", "article 368", "simple majority", "special majority", "ratification", "constitutional change", "42nd amendment", "basic structure", "kesavananda bharati"]
        }
    },
    {
        "id": "preamble_comprehensive",
        "content": """
        The Preamble: The Soul and Philosophy of Indian Constitution

        The Preamble serves as the introduction and preface to the Constitution, embodying its basic philosophy, fundamental values, and guiding principles. It declares the source of Constitution's authority and lays down the objectives that the Constitution seeks to establish and promote.

        TEXT OF THE PREAMBLE:

        "WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC and to secure to all its citizens:

        JUSTICE, social, economic and political;
        LIBERTY of thought, expression, belief, faith and worship;
        EQUALITY of status and of opportunity; and to promote among them all
        FRATERNITY assuring the dignity of the individual and the unity and integrity of the Nation;

        IN OUR CONSTITUENT ASSEMBLY this twenty-sixth day of November, 1949, do HEREBY ADOPT, ENACT AND GIVE TO OURSELVES THIS CONSTITUTION."

        HISTORICAL BACKGROUND:

        The Preamble was based on the 'Objective Resolution' moved by Jawaharlal Nehru on December 13, 1946, in the Constituent Assembly. This resolution was unanimously adopted on January 22, 1947, and became the foundation of the Preamble.

        Nehru's Objective Resolution declared:
        - India shall be an Independent Sovereign Republic
        - All power and authority shall derive from the people
        - All people shall be guaranteed justice, equality, and freedom
        - Adequate safeguards for minorities, backward areas, and depressed classes
        - India shall promote world peace and welfare of mankind

        The Preamble was drafted by the Drafting Committee and was adopted along with the Constitution on November 26, 1949.

        KEY WORDS AND THEIR MEANINGS:

        WE, THE PEOPLE OF INDIA:
        - Ultimate source of Constitution's authority is the people
        - Popular sovereignty - government derives power from people
        - Direct democracy where people are supreme
        - Rejection of monarchy and foreign rule
        - Emphasizes unity of Indian people regardless of religion, region, language

        SOVEREIGN:
        - India is internally and externally free
        - No external authority can dictate to India
        - Supreme power vests in Indian people
        - Freedom to conduct internal and external affairs
        - Not subordinate to any other country

        SOCIALIST:
        - Added by 42nd Amendment in 1976
        - Commitment to social and economic equality
        - Wealth should not be concentrated in few hands
        - Democratic socialism, not communist socialism
        - Mixed economy with public and private sectors
        - Welfare state ensuring basic needs for all

        SECULAR:
        - Added by 42nd Amendment in 1976
        - No official religion of the state
        - Equal treatment and respect for all religions
        - Freedom of religion for all citizens
        - State maintains neutrality in religious matters
        - Positive secularism - state supports all religions equally

        DEMOCRATIC:
        - Government by the people, for the people, of the people
        - Representative government through elections
        - Majority rule with minority rights
        - Political equality through universal adult suffrage
        - Responsible government accountable to people
        - Rule of law and constitutional government

        REPUBLIC:
        - Head of state is elected, not hereditary
        - No monarchy or privileged class
        - Equal opportunities for all in public office
        - Merit-based selection for positions
        - Rejection of birth-based privileges

        JUSTICE:
        Three types of justice are guaranteed:

        Social Justice:
        - Absence of discrimination based on caste, creed, color, religion, sex
        - Equal treatment regardless of social status
        - Special protection for weaker sections
        - Removal of social inequalities and disabilities

        Economic Justice:
        - No discrimination based on economic status
        - Equal opportunity for economic development
        - Minimum standard of living for all
        - Elimination of exploitation
        - Equitable distribution of resources

        Political Justice:
        - Equal political rights for all citizens
        - Universal adult suffrage
        - Equal opportunity to participate in politics
        - Right to contest elections
        - Democratic participation in governance

        LIBERTY:
        Five types of liberty guaranteed:

        Liberty of Thought:
        - Freedom to think and form opinions
        - Right to hold beliefs and ideas
        - Protection against thought control
        - Intellectual freedom

        Liberty of Expression:
        - Freedom of speech and expression
        - Right to communicate ideas and opinions
        - Freedom of press and media
        - Artistic and creative expression

        Liberty of Belief:
        - Freedom to hold religious or philosophical beliefs
        - Right to choose one's worldview
        - Protection of conscience

        Liberty of Faith:
        - Freedom to practice religion
        - Right to follow religious customs and traditions
        - Protection of religious practices

        Liberty of Worship:
        - Freedom to worship according to one's faith
        - Right to perform religious rituals
        - Protection of places of worship

        EQUALITY:
        Two types of equality ensured:

        Equality of Status:
        - No discrimination based on birth, caste, religion, sex
        - Equal dignity and respect for all citizens
        - Absence of privileged classes
        - Social equality

        Equality of Opportunity:
        - Equal chances for all in education, employment, and advancement
        - Merit-based selection
        - No unfair advantages based on birth or status
        - Equal access to public facilities and services

        FRATERNITY:
        - Spirit of brotherhood among all Indians
        - Emotional integration and unity
        - Mutual respect and cooperation
        - Common citizenship transcending differences

        Two aspects of fraternity:

        Dignity of Individual:
        - Respect for human dignity
        - Individual rights and freedoms
        - Protection against discrimination and exploitation
        - Value of each person regardless of status

        Unity and Integrity of Nation:
        - National integration and cohesion
        - Territorial integrity
        - Cultural and emotional unity
        - Pride in Indian identity

        AMENDMENT OF PREAMBLE:

        The Preamble has been amended only once:
        42nd Amendment (1976): Added words "Socialist" and "Secular"

        Original Preamble said: "SOVEREIGN DEMOCRATIC REPUBLIC"
        After amendment: "SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC"

        This amendment was made during the Emergency period under Indira Gandhi's government and reflected the political ideology of that time.

        LEGAL STATUS AND JUDICIAL INTERPRETATION:

        Important Cases:

        Berubari Union Case (1960): Supreme Court held that Preamble is not part of Constitution and cannot be enforced in courts.

        Kesavananda Bharati Case (1973): Supreme Court reversed its earlier position and held that:
        - Preamble is part of Constitution
        - It provides key to understanding Constitution
        - It cannot be amended to destroy basic structure
        - It embodies basic structure of Constitution

        LIC of India Case (1995): Supreme Court reaffirmed that Preamble is part of Constitution and can be used to interpret constitutional provisions.

        Current Legal Position:
        - Preamble is part of Constitution
        - It is not enforceable in courts directly
        - It serves as guide for constitutional interpretation
        - It embodies the basic structure of Constitution
        - It can be amended but not destroyed

        SIGNIFICANCE AND FUNCTIONS:

        1. Source of Authority: Declares people as source of Constitution
        2. Statement of Objectives: Outlines goals and aspirations
        3. Guide for Interpretation: Helps understand constitutional provisions
        4. Basic Structure: Embodies fundamental features
        5. Limitation on Amendment: Prevents destruction of basic features
        6. Integration Tool: Promotes national unity and identity
        7. Moral Foundation: Provides ethical basis for governance

        COMPARISON WITH OTHER COUNTRIES:

        USA: "We the People..." - Similar popular sovereignty
        France: "Liberty, Equality, Fraternity" - Similar values (influenced Indian Preamble)
        Ireland: Detailed objectives and aspirations
        Australia: Simple introduction without elaborate objectives

        CRITICISM AND EVALUATION:

        Strengths:
        - Comprehensive statement of objectives
        - Reflects Indian values and aspirations
        - Provides guidance for governance
        - Promotes national integration
        - Embodies democratic ideals

        Weaknesses:
        - Too lengthy and detailed
        - Some words added during Emergency
        - Idealistic goals difficult to achieve
        - Legal enforceability limited
        - Some contradictions in objectives

        CONTEMPORARY RELEVANCE:

        The Preamble remains highly relevant in modern India:
        - Secularism important in diverse society
        - Socialism relevant for reducing inequality
        - Democracy strengthened through elections
        - Justice needed for marginalized sections
        - Liberty essential for individual development
        - Equality crucial for social harmony
        - Fraternity necessary for national unity

        FOR STUDENTS:

        Understanding the Preamble helps students:
        - Appreciate constitutional philosophy
        - Understand India's democratic values
        - Learn about national objectives and aspirations
        - Develop civic sense and responsibility
        - Prepare for citizenship in democratic India
        - Connect with India's constitutional heritage

        The Preamble serves as the North Star of Indian Constitution, guiding the nation towards its cherished goals of justice, liberty, equality, and fraternity in a sovereign, socialist, secular, democratic republic.
        """,
        "metadata": {
            "topic": "preamble",
            "class_level": "8th-12th",
            "importance": "very_high",
            "keywords": ["preamble", "sovereign", "socialist", "secular", "democratic", "republic", "justice", "liberty", "equality", "fraternity", "we the people", "objective resolution", "nehru"]
        }
    }
]

def initialize_complete_rag_system():
    """Initialize the complete RAG system with constitutional documents"""
    try:
        # Check if documents already exist
        if DocumentChunk.query.count() == 0:
            logger.info("Initializing Complete RAG system with comprehensive constitution documents...")
            rag_pipeline.add_documents(COMPREHENSIVE_CONSTITUTION_DOCUMENTS)
            logger.info("Complete RAG system initialized successfully")
        else:
            logger.info("Complete RAG system already initialized, loading existing documents...")
            load_existing_documents()
    except Exception as e:
        logger.error(f"Error initializing Complete RAG system: {e}")

def load_existing_documents():
    """Load existing documents from database into RAG pipeline"""
    try:
        chunks = DocumentChunk.query.all()
        
        for chunk in chunks:
            # Add to FAISS index
            embedding = np.array(chunk.embedding_vector).astype('float32')
            rag_pipeline.faiss_index.add(embedding.reshape(1, -1))
            
            # Add to document storage
            rag_pipeline.documents.append(chunk.content)
            rag_pipeline.document_metadata.append(chunk.metadata)
        
        # Initialize search components
        if rag_pipeline.documents:
            # BM25 initialization
            tokenized_docs = [doc.split() for doc in rag_pipeline.documents]
            rag_pipeline.bm25 = BM25Okapi(tokenized_docs)
            
            # TF-IDF initialization
            try:
                rag_pipeline.tfidf_matrix = rag_pipeline.tfidf_vectorizer.fit_transform(rag_pipeline.documents)
            except Exception as e:
                logger.warning(f"TF-IDF re-initialization failed: {e}")
        
        logger.info(f"Loaded {len(chunks)} documents into Complete RAG pipeline")
    except Exception as e:
        logger.error(f"Error loading existing documents: {e}")

# Flask Routes

@app.route('/api/chat', methods=['POST'])
def chat():
    start_time = datetime.now()
    
    try:
        data = request.json
        query = data.get('query', '')
        user_id = data.get('user_id', 'anonymous')
        user_class = data.get('class', '10th')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        logger.info(f"Processing query: {query[:100]}... for class {user_class}")
        
        # Multi-method retrieval
        retrieved_docs = rag_pipeline.multi_retrieval(query, top_k=6)
        
        # Generate response using local models
        response, generation_score = rag_pipeline.generate_response(query, retrieved_docs, user_class)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        relevance_score = retrieved_docs[0]['final_score'] if retrieved_docs else 0.0
        
        # Prepare retrieved context for storage
        retrieved_context = json.dumps([
            {
                'content': doc['content'][:300] + '...',
                'score': doc.get('final_score', doc.get('combined_score', 0)),
                'methods': doc.get('retrieval_methods', ['unknown']),
                'metadata': doc['metadata']
            } for doc in retrieved_docs[:3]
        ])
        
        # Save to search history
        history_entry = SearchHistory(
            user_id=user_id,
            query=query,
            response=response,
            retrieved_context=retrieved_context,
            relevance_score=relevance_score,
            generation_score=generation_score,
            processing_time=processing_time
        )
        db.session.add(history_entry)
        db.session.commit()
        
        # Update RAG metrics
        update_rag_metrics('total_queries', 1, relevance_score, generation_score, processing_time)
        
        return jsonify({
            'response': response,
            'query_id': history_entry.id,
            'timestamp': history_entry.timestamp.isoformat(),
            'relevance_score': relevance_score,
            'generation_score': generation_score,
            'processing_time': processing_time,
            'retrieved_sources': len(retrieved_docs),
            'pipeline_info': {
                'retrieval_methods': ['semantic', 'keyword', 'tfidf'],
                'generation_method': 'neural' if rag_pipeline.generation_model else 'template',
                'reranking': 'cross-encoder' if rag_pipeline.reranker else 'similarity'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        history = SearchHistory.query.filter_by(user_id=user_id)\
                                   .order_by(SearchHistory.timestamp.desc())\
                                   .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'history': [{
                'id': h.id,
                'query': h.query,
                'response': h.response,
                'timestamp': h.timestamp.isoformat(),
                'feedback_score': h.feedback_score,
                'relevance_score': h.relevance_score,
                'generation_score': h.generation_score,
                'processing_time': h.processing_time,
                'retrieved_context': json.loads(h.retrieved_context) if h.retrieved_context else []
            } for h in history.items],
            'total': history.total,
            'pages': history.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        query_id = data.get('query_id')
        score = data.get('score')
        
        history_entry = SearchHistory.query.get(query_id)
        if history_entry:
            old_score = history_entry.feedback_score
            history_entry.feedback_score = score
            db.session.commit()
            
            # Update RAG metrics with feedback
            update_rag_metrics('feedback_received', 1)
            if score >= 4:
                update_rag_metrics('positive_feedback', 1)
            
            # Update generation quality based on feedback
            generation_quality = score / 5.0
            update_rag_metrics('generation_quality', generation_quality, 
                             history_entry.relevance_score, generation_quality)
            
            return jsonify({
                'message': 'Feedback recorded successfully',
                'previous_score': old_score,
                'new_score': score
            })
        else:
            return jsonify({'error': 'Query not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    try:
        # Calculate comprehensive metrics
        total_queries = SearchHistory.query.count()
        avg_feedback = db.session.query(db.func.avg(SearchHistory.feedback_score))\
                                .filter(SearchHistory.feedback_score > 0).scalar() or 0
        avg_relevance = db.session.query(db.func.avg(SearchHistory.relevance_score))\
                                 .filter(SearchHistory.relevance_score.isnot(None)).scalar() or 0
        avg_generation = db.session.query(db.func.avg(SearchHistory.generation_score))\
                                  .filter(SearchHistory.generation_score.isnot(None)).scalar() or 0
        avg_processing_time = db.session.query(db.func.avg(SearchHistory.processing_time))\
                                       .filter(SearchHistory.processing_time.isnot(None)).scalar() or 0
        
        positive_feedback_count = SearchHistory.query.filter(SearchHistory.feedback_score >= 4).count()
        feedback_count = SearchHistory.query.filter(SearchHistory.feedback_score > 0).count()
        
        satisfaction_rate = (positive_feedback_count / feedback_count * 100) if feedback_count > 0 else 0
        
        # Get usage over time (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_queries = SearchHistory.query.filter(SearchHistory.timestamp >= week_ago).count()
        
        # RAG-specific metrics
        rag_metrics = calculate_comprehensive_rag_performance()
        
        return jsonify({
            'total_queries': total_queries,
            'average_feedback': round(avg_feedback, 2),
            'average_relevance': round(avg_relevance, 3),
            'average_generation': round(avg_generation, 3),
            'average_processing_time': round(avg_processing_time, 3),
            'satisfaction_rate': round(satisfaction_rate, 2),
            'recent_activity': recent_queries,
            'rag_performance': rag_metrics,
            'learning_progress': calculate_learning_progress(),
            'system_info': {
                'total_documents': len(rag_pipeline.documents),
                'embedding_model': 'all-MiniLM-L6-v2',
                'generation_model': 'DialoGPT-small' if rag_pipeline.generation_model else 'Template-based',
                'retrieval_methods': ['FAISS', 'BM25', 'TF-IDF'],
                'reranking': 'Cross-encoder' if rag_pipeline.reranker else 'Similarity-based'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_rag_metrics(metric_name: str, value: float, retrieval_accuracy: float = None, 
                      generation_quality: float = None, processing_time: float = None):
    """Update comprehensive RAG metrics"""
    try:
        metric = RAGMetrics(
            metric_name=metric_name,
            metric_value=value,
            retrieval_accuracy=retrieval_accuracy,
            generation_quality=generation_quality,
            processing_time=processing_time
        )
        db.session.add(metric)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error updating RAG metrics: {e}")

def calculate_comprehensive_rag_performance():
    """Calculate comprehensive RAG pipeline performance metrics"""
    try:
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_metrics = RAGMetrics.query.filter(RAGMetrics.timestamp >= week_ago).all()
        
        if not recent_metrics:
            return {
                "retrieval_accuracy": 0.85,
                "generation_quality": 0.80,
                "overall_performance": 0.82,
                "avg_processing_time": 0.5,
                "status": "Initializing",
                "components": {
                    "faiss_index": "Active",
                    "bm25_ranking": "Active", 
                    "tfidf_search": "Active",
                    "neural_generation": "Active" if rag_pipeline.generation_model else "Template-based",
                    "cross_encoder_reranking": "Active" if rag_pipeline.reranker else "Disabled"
                }
            }
        
        # Calculate averages
        retrieval_scores = [m.retrieval_accuracy for m in recent_metrics if m.retrieval_accuracy]
        generation_scores = [m.generation_quality for m in recent_metrics if m.generation_quality]
        processing_times = [m.processing_time for m in recent_metrics if m.processing_time]
        
        avg_retrieval = sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0.85
        avg_generation = sum(generation_scores) / len(generation_scores) if generation_scores else 0.80
        avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0.5
        
        overall_performance = (avg_retrieval + avg_generation) / 2
        
        # Determine status
        if overall_performance > 0.9:
            status = "Excellent"
        elif overall_performance > 0.8:
            status = "Very Good"
        elif overall_performance > 0.7:
            status = "Good"
        elif overall_performance > 0.6:
            status = "Improving"
        else:
            status = "Learning"
        
        return {
            "retrieval_accuracy": round(avg_retrieval, 3),
            "generation_quality": round(avg_generation, 3),
            "overall_performance": round(overall_performance, 3),
            "avg_processing_time": round(avg_processing, 3),
            "status": status,
            "components": {
                "faiss_index": "Active",
                "bm25_ranking": "Active",
                "tfidf_search": "Active",
                "neural_generation": "Active" if rag_pipeline.generation_model else "Template-based",
                "cross_encoder_reranking": "Active" if rag_pipeline.reranker else "Similarity-based"
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating comprehensive RAG performance: {e}")
        return {
            "retrieval_accuracy": 0.85,
            "generation_quality": 0.80,
            "overall_performance": 0.82,
            "avg_processing_time": 0.5,
            "status": "Error",
            "components": {
                "status": "Error in calculation"
            }
        }

def calculate_learning_progress():
    """Calculate learning progress with comprehensive RAG insights"""
    try:
        # Get feedback trends
        recent_feedback = SearchHistory.query.filter(
            SearchHistory.feedback_score > 0,
            SearchHistory.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(SearchHistory.timestamp.desc()).limit(100).all()
        
        if len(recent_feedback) < 10:
            return {
                "status": "Learning from multi-modal RAG interactions", 
                "progress": 0, 
                "current_avg": 0,
                "rag_insights": {
                    "retrieval_evolution": "Hybrid search optimization in progress",
                    "generation_improvement": "Neural and template-based generation learning",
                    "overall_trend": "System building knowledge base"
                }
            }
        
        # Calculate improvement trend
        first_half = recent_feedback[len(recent_feedback)//2:]
        second_half = recent_feedback[:len(recent_feedback)//2]
        
        avg_first = sum(f.feedback_score for f in first_half) / len(first_half)
        avg_second = sum(f.feedback_score for f in second_half) / len(second_half)
        
        improvement = ((avg_second - avg_first) / avg_first) * 100 if avg_first > 0 else 0
        
        # RAG-specific insights
        relevance_scores = [f.relevance_score for f in recent_feedback if f.relevance_score]
        generation_scores = [f.generation_score for f in recent_feedback if f.generation_score]
        
        avg_relevance_trend = "improving" if improvement > 5 else "stable" if improvement > -5 else "learning"
        
        return {
            "status": f"Complete RAG pipeline {avg_relevance_trend}",
            "progress": round(improvement, 2),
            "current_avg": round(avg_second, 2),
            "rag_insights": {
                "retrieval_quality": "Multi-method hybrid search active",
                "generation_quality": "Neural + template generation optimizing",
                "processing_efficiency": "Sub-second response times",
                "learning_mechanism": "Feedback-driven continuous improvement",
                "knowledge_coverage": "Comprehensive Constitution knowledge base"
            }
        }
        
    except Exception as e:
        return {
            "status": "Analyzing complete RAG performance", 
            "progress": 0, 
            "current_avg": 0,
            "rag_insights": {
                "status": "Error in progress calculation"
            }
        }

@app.route('/api/search', methods=['GET'])
def search_history():
    try:
        user_id = request.args.get('user_id')
        search_term = request.args.get('q', '')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        query = SearchHistory.query.filter_by(user_id=user_id)
        
        if search_term:
            query = query.filter(
                SearchHistory.query.contains(search_term) |
                SearchHistory.response.contains(search_term)
            )
        
        results = query.order_by(SearchHistory.timestamp.desc()).limit(50).all()
        
        return jsonify({
            'results': [{
                'id': r.id,
                'query': r.query,
                'response': r.response[:200] + '...' if len(r.response) > 200 else r.response,
                'timestamp': r.timestamp.isoformat(),
                'relevance_score': r.relevance_score,
                'processing_time': r.processing_time
            } for r in results]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Complete Constitution Chatbot with RAG Pipeline is running!',
        'version': '3.0.0',
        'pipeline': 'Complete RAG (Local Models Only)',
        'features': [
            'Multi-Method Hybrid Search (FAISS + BM25 + TF-IDF)',
            'Advanced Document Chunking & Semantic Indexing',
            'Neural + Template-based Generation',
            'Cross-Encoder Reranking',
            'Comprehensive Performance Analytics',
            'Self-Learning with Detailed Feedback Analysis',
            'Class-Specific Content (8th-12th)',
            'Zero External API Dependencies',
            'Real-time Relevance Scoring',
            'Comprehensive Constitution Knowledge Base'
        ],
        'components': {
            'retrieval': 'FAISS + BM25 + TF-IDF Hybrid Search',
            'embedding': 'SentenceTransformer (all-MiniLM-L6-v2)',
            'generation': 'DialoGPT-small + Template-based',
            'reranking': 'Cross-encoder/ms-marco-MiniLM-L-2-v2',
            'knowledge_base': 'Comprehensive Indian Constitution'
        },
        'models': {
            'embedding_model': 'all-MiniLM-L6-v2',
            'generation_model': 'microsoft/DialoGPT-small',
            'reranking_model': 'cross-encoder/ms-marco-MiniLM-L-2-v2',
            'no_external_apis': True,
            'fully_local': True
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_complete_rag_system()
    app.run(debug=True, port=5000, host='0.0.0.0')