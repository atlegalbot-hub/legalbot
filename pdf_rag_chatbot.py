"""
PDF-Based RAG Chatbot - 100% Free & Open Source
Uses your own PDF files as knowledge base
No paid APIs or services required!
"""

from flask import Flask, request, jsonify, render_template_string
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
import hashlib

# PDF Processing (FREE)
import PyPDF2
import pdfplumber
from io import BytesIO

# RAG Components (ALL FREE)
from sentence_transformers import SentenceTransformer
import faiss
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Text Processing (FREE)
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdf_rag_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class PDFDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False, unique=True)
    total_pages = db.Column(db.Integer, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    
class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdf_document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    embedding_vector = db.Column(db.PickleType, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    retrieved_chunks = db.Column(db.Text, nullable=True)
    relevance_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)

class SystemMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PDFRAGPipeline:
    """
    Complete PDF-based RAG Pipeline using only FREE components
    """
    
    def __init__(self):
        logger.info("Initializing PDF RAG Pipeline with FREE models...")
        
        # Download NLTK data (free)
        self._download_nltk_data()
        
        # Initialize FREE embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # FREE
        self.embedding_dim = 384
        
        # Initialize FAISS index (FREE)
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Initialize FREE generation model
        self.init_free_generation_model()
        
        # Document storage
        self.documents = []
        self.document_metadata = []
        
        # Search components (ALL FREE)
        self.bm25 = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.tfidf_matrix = None
        
        # PDF upload directory
        self.upload_dir = Path("uploaded_pdfs")
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("PDF RAG Pipeline initialized with FREE components!")
    
    def _download_nltk_data(self):
        """Download required NLTK data (FREE)"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            logger.warning("NLTK data download failed, using basic tokenization")
    
    def init_free_generation_model(self):
        """Initialize FREE generation model"""
        try:
            # Use GPT-2 small (completely FREE)
            model_name = "gpt2"
            self.generation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.generation_model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add pad token
            self.generation_tokenizer.pad_token = self.generation_tokenizer.eos_token
            
            logger.info("FREE GPT-2 model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load GPT-2: {e}, using template-based generation")
            self.generation_model = None
            self.generation_tokenizer = None
    
    def extract_text_from_pdf(self, pdf_file) -> Tuple[str, Dict]:
        """Extract text from PDF using FREE libraries"""
        try:
            # Method 1: Try pdfplumber (better for complex layouts)
            with pdfplumber.open(pdf_file) as pdf:
                text_content = []
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append({
                                'page': page_num,
                                'text': page_text.strip()
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {e}")
                
                metadata = {
                    'total_pages': total_pages,
                    'extraction_method': 'pdfplumber',
                    'pages_extracted': len(text_content)
                }
                
                return text_content, metadata
                
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
            
            # Method 2: Fallback to PyPDF2 (FREE)
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = []
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append({
                                'page': page_num,
                                'text': page_text.strip()
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {e}")
                
                metadata = {
                    'total_pages': total_pages,
                    'extraction_method': 'PyPDF2',
                    'pages_extracted': len(text_content)
                }
                
                return text_content, metadata
                
            except Exception as e:
                logger.error(f"All PDF extraction methods failed: {e}")
                return [], {'error': str(e)}
    
    def chunk_text_intelligently(self, page_content: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """Intelligent text chunking with context preservation"""
        chunks = []
        
        for page_data in page_content:
            page_num = page_data['page']
            text = page_data['text']
            
            # Split into sentences using NLTK (FREE)
            try:
                sentences = sent_tokenize(text)
            except:
                # Fallback to simple splitting
                sentences = [s.strip() for s in text.split('.') if s.strip()]
            
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_words = len(sentence.split())
                
                if current_length + sentence_words > chunk_size and current_chunk:
                    # Create chunk
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'page_number': page_num,
                        'chunk_index': len(chunks),
                        'word_count': current_length,
                        'sentences': len(current_chunk)
                    })
                    
                    # Handle overlap
                    if overlap > 0 and len(current_chunk) > 1:
                        overlap_sentences = current_chunk[-(overlap//50):] if overlap//50 > 0 else []
                        current_chunk = overlap_sentences + [sentence]
                        current_length = sum(len(s.split()) for s in current_chunk)
                    else:
                        current_chunk = [sentence]
                        current_length = sentence_words
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_words
            
            # Add remaining chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'page_number': page_num,
                    'chunk_index': len(chunks),
                    'word_count': current_length,
                    'sentences': len(current_chunk)
                })
        
        return chunks
    
    def process_pdf_file(self, pdf_file, filename: str) -> bool:
        """Process uploaded PDF and add to knowledge base"""
        try:
            # Calculate file hash
            pdf_file.seek(0)
            file_content = pdf_file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            pdf_file.seek(0)
            
            # Check if already processed
            existing_doc = PDFDocument.query.filter_by(file_hash=file_hash).first()
            if existing_doc:
                logger.info(f"PDF {filename} already processed")
                return True
            
            # Extract text from PDF
            logger.info(f"Extracting text from {filename}...")
            page_content, metadata = self.extract_text_from_pdf(pdf_file)
            
            if not page_content:
                logger.error(f"No text extracted from {filename}")
                return False
            
            # Save PDF document record
            pdf_doc = PDFDocument(
                filename=filename,
                file_hash=file_hash,
                total_pages=metadata.get('total_pages', 0),
                file_size=len(file_content),
                processed=False
            )
            db.session.add(pdf_doc)
            db.session.commit()
            
            # Chunk the text intelligently
            logger.info(f"Chunking text from {filename}...")
            chunks = self.chunk_text_intelligently(page_content, chunk_size=400, overlap=50)
            
            # Process chunks and create embeddings
            logger.info(f"Creating embeddings for {len(chunks)} chunks...")
            for chunk in chunks:
                # Generate embedding (FREE)
                embedding = self.embedding_model.encode(chunk['content'])
                
                # Save chunk to database
                db_chunk = DocumentChunk(
                    pdf_id=pdf_doc.id,
                    chunk_index=chunk['chunk_index'],
                    content=chunk['content'],
                    page_number=chunk['page_number'],
                    embedding_vector=embedding.tolist(),
                    metadata=chunk
                )
                db.session.add(db_chunk)
                
                # Add to FAISS index
                self.faiss_index.add(embedding.reshape(1, -1).astype('float32'))
                
                # Store for other search methods
                self.documents.append(chunk['content'])
                self.document_metadata.append({
                    'pdf_id': pdf_doc.id,
                    'filename': filename,
                    'page_number': chunk['page_number'],
                    'chunk_index': chunk['chunk_index']
                })
            
            # Update processed status
            pdf_doc.processed = True
            db.session.commit()
            
            # Rebuild search indexes
            self._rebuild_search_indexes()
            
            logger.info(f"Successfully processed {filename} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            db.session.rollback()
            return False
    
    def _rebuild_search_indexes(self):
        """Rebuild BM25 and TF-IDF indexes"""
        try:
            if self.documents:
                # BM25 index (FREE)
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                
                # TF-IDF index (FREE)
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
                
                logger.info("Search indexes rebuilt successfully")
        except Exception as e:
            logger.error(f"Error rebuilding search indexes: {e}")
    
    def load_existing_documents(self):
        """Load existing processed documents"""
        try:
            chunks = DocumentChunk.query.all()
            
            for chunk in chunks:
                # Add to FAISS index
                embedding = np.array(chunk.embedding_vector).astype('float32')
                self.faiss_index.add(embedding.reshape(1, -1))
                
                # Add to document storage
                self.documents.append(chunk.content)
                
                # Get PDF info
                pdf_doc = PDFDocument.query.get(chunk.pdf_id)
                self.document_metadata.append({
                    'pdf_id': chunk.pdf_id,
                    'filename': pdf_doc.filename if pdf_doc else 'Unknown',
                    'page_number': chunk.page_number,
                    'chunk_index': chunk.chunk_index
                })
            
            # Rebuild search indexes
            self._rebuild_search_indexes()
            
            logger.info(f"Loaded {len(chunks)} existing document chunks")
            
        except Exception as e:
            logger.error(f"Error loading existing documents: {e}")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Multi-method document search (ALL FREE)"""
        if not self.documents:
            return []
        
        results = []
        
        # 1. Semantic search with FAISS (FREE)
        try:
            query_embedding = self.embedding_model.encode(query).astype('float32')
            semantic_scores, semantic_indices = self.faiss_index.search(
                query_embedding.reshape(1, -1), min(top_k * 2, len(self.documents))
            )
            
            for score, idx in zip(semantic_scores[0], semantic_indices[0]):
                if idx < len(self.documents) and score > 0:
                    results.append({
                        'content': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'semantic_score': float(score),
                        'index': idx
                    })
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
        
        # 2. Keyword search with BM25 (FREE)
        try:
            if self.bm25:
                query_tokens = query.split()
                bm25_scores = self.bm25.get_scores(query_tokens)
                
                for idx, score in enumerate(bm25_scores):
                    if idx < len(results) and score > 0:
                        results[idx]['bm25_score'] = float(score)
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
        
        # 3. TF-IDF search (FREE)
        try:
            if self.tfidf_matrix is not None:
                query_vector = self.tfidf_vectorizer.transform([query])
                tfidf_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
                
                for idx, score in enumerate(tfidf_scores):
                    if idx < len(results) and score > 0:
                        results[idx]['tfidf_score'] = float(score)
        except Exception as e:
            logger.error(f"TF-IDF search error: {e}")
        
        # Combine scores
        for result in results:
            semantic = result.get('semantic_score', 0)
            bm25 = result.get('bm25_score', 0)
            tfidf = result.get('tfidf_score', 0)
            
            # Normalize BM25 score
            max_bm25 = max([r.get('bm25_score', 0) for r in results]) if results else 1
            bm25_norm = bm25 / max_bm25 if max_bm25 > 0 else 0
            
            # Combined score
            result['combined_score'] = 0.5 * semantic + 0.3 * bm25_norm + 0.2 * tfidf
        
        # Sort by combined score and return top_k
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        return results[:top_k]
    
    def generate_response(self, query: str, retrieved_docs: List[Dict]) -> Tuple[str, float]:
        """Generate response using FREE models"""
        if not retrieved_docs:
            return self._generate_fallback_response(query), 0.5
        
        # Prepare context
        context = self._prepare_context(retrieved_docs[:3])
        
        # Try FREE GPT-2 generation
        if self.generation_model and self.generation_tokenizer:
            response, score = self._free_neural_generation(query, context)
            if len(response) > 50 and self._is_good_response(response, query):
                return response, score
        
        # Fallback to template-based generation (FREE)
        return self._template_based_generation(query, context, retrieved_docs)
    
    def _prepare_context(self, docs: List[Dict]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs):
            metadata = doc['metadata']
            filename = metadata.get('filename', 'Unknown')
            page = metadata.get('page_number', 'Unknown')
            score = doc.get('combined_score', 0)
            
            context_parts.append(
                f"**Source {i+1}** (File: {filename}, Page: {page}, Relevance: {score:.2f}):\n"
                f"{doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _free_neural_generation(self, query: str, context: str) -> Tuple[str, float]:
        """Generate response using FREE GPT-2 model"""
        try:
            # Create prompt
            prompt = f"Context: {context[:800]}\n\nQuestion: {query}\n\nAnswer:"
            
            # Tokenize
            inputs = self.generation_tokenizer.encode(
                prompt, return_tensors='pt', max_length=512, truncation=True
            )
            
            # Generate
            with torch.no_grad():
                outputs = self.generation_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.generation_tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs)
                )
            
            # Decode
            generated_text = self.generation_tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated_text[len(prompt):].strip()
            
            # Clean up response
            response = self._clean_generated_response(response)
            
            return response, 0.8
            
        except Exception as e:
            logger.error(f"Free neural generation error: {e}")
            return "", 0.0
    
    def _clean_generated_response(self, response: str) -> str:
        """Clean up generated response"""
        # Remove common artifacts
        response = re.sub(r'\n+', '\n', response)
        response = re.sub(r'\s+', ' ', response)
        
        # Stop at first complete sentence if too long
        sentences = response.split('.')
        if len(sentences) > 1 and len(response) > 200:
            response = sentences[0] + '.'
        
        return response.strip()
    
    def _is_good_response(self, response: str, query: str) -> bool:
        """Check if generated response is good quality"""
        if len(response) < 20:
            return False
        
        # Check relevance
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words.intersection(response_words))
        
        return overlap > 0
    
    def _template_based_generation(self, query: str, context: str, docs: List[Dict]) -> Tuple[str, float]:
        """Template-based response generation (FREE)"""
        
        # Extract key information from context
        key_info = self._extract_key_information(context, query)
        
        # Build response
        response = f"📖 **Based on your documents:**\n\n{key_info}\n\n"
        
        # Add source information
        if docs:
            response += "📚 **Sources:**\n"
            for i, doc in enumerate(docs[:3]):
                metadata = doc['metadata']
                filename = metadata.get('filename', 'Unknown')
                page = metadata.get('page_number', 'Unknown')
                response += f"• {filename} (Page {page})\n"
        
        # Add helpful note
        response += f"\n💡 **Note:** This answer is based on your uploaded PDF documents. "
        response += f"If you need more specific information, try rephrasing your question."
        
        return response, 0.7
    
    def _extract_key_information(self, context: str, query: str) -> str:
        """Extract key information from context"""
        # Split context into sentences
        sentences = []
        for line in context.split('\n'):
            if line.strip() and not line.strip().startswith('**Source'):
                sentences.extend([s.strip() for s in line.split('.') if s.strip()])
        
        # Score sentences based on query relevance
        query_words = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 20:
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
            return context[:500] + '...' if len(context) > 500 else context
    
    def _generate_fallback_response(self, query: str) -> str:
        """Fallback response when no documents found"""
        return """
📚 **No relevant information found in your uploaded documents.**

To get better results:

🔍 **Try these tips:**
• Use more specific keywords
• Check if your PDF contains the information you're looking for
• Upload more relevant documents
• Rephrase your question

📄 **Upload more PDFs** to expand the knowledge base and get better answers!

💡 **Tip:** Make sure your PDFs are text-based (not scanned images) for best results.
        """

# Initialize RAG Pipeline
pdf_rag = PDFRAGPipeline()

# Flask Routes
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>PDF RAG Chatbot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .upload-section { background: #e8f4f8; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .chat-section { background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .file-input { margin: 10px 0; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .chat-input { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .chat-response { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff; }
        .documents-list { margin: 20px 0; }
        .doc-item { background: white; padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 PDF RAG Chatbot</h1>
            <p>Upload your PDFs and chat with your documents using AI - 100% FREE!</p>
            <p><strong>💰 Zero Cost • 🔒 Private • 🏠 Local Processing</strong></p>
        </div>
        
        <div class="upload-section">
            <h2>📄 Upload PDF Documents</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="pdfFile" name="pdf" accept=".pdf" multiple class="file-input">
                <br>
                <button type="submit" class="btn">📤 Upload PDF(s)</button>
            </form>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="documents-list">
            <h3>📚 Uploaded Documents</h3>
            <div id="documentsList">Loading...</div>
        </div>
        
        <div class="chat-section">
            <h2>💬 Chat with Your Documents</h2>
            <div id="chatMessages"></div>
            <br>
            <input type="text" id="chatInput" class="chat-input" placeholder="Ask questions about your uploaded PDFs...">
            <button onclick="sendMessage()" class="btn">🚀 Send</button>
        </div>
    </div>

    <script>
        // Upload functionality
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            const files = document.getElementById('pdfFile').files;
            
            for (let file of files) {
                formData.append('pdfs', file);
            }
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status warning">⏳ Uploading and processing PDFs...</div>';
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status success">✅ ' + result.message + '</div>';
                    loadDocuments();
                } else {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ ' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Upload failed: ' + error.message + '</div>';
            }
        };
        
        // Chat functionality
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const query = input.value.trim();
            if (!query) return;
            
            // Add user message
            addMessage('user', query);
            input.value = '';
            
            // Add loading message
            const loadingId = addMessage('bot', '🤔 Searching your documents...');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, user_id: 'user123'})
                });
                const result = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId).remove();
                
                if (result.response) {
                    addMessage('bot', result.response, result);
                } else {
                    addMessage('bot', '❌ Error: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessage('bot', '❌ Error: ' + error.message);
            }
        }
        
        function addMessage(type, content, metadata = null) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageId = 'msg_' + Date.now();
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = 'chat-response';
            
            let html = '<strong>' + (type === 'user' ? '👤 You:' : '🤖 Bot:') + '</strong><br>';
            html += content.replace(/\\n/g, '<br>');
            
            if (metadata) {
                html += '<br><small>⚡ Processing time: ' + (metadata.processing_time || 'N/A') + 's | 📊 Relevance: ' + (metadata.relevance_score || 'N/A') + '</small>';
            }
            
            messageDiv.innerHTML = html;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageId;
        }
        
        // Load documents list
        async function loadDocuments() {
            try {
                const response = await fetch('/documents');
                const result = await response.json();
                
                const docsDiv = document.getElementById('documentsList');
                if (result.documents && result.documents.length > 0) {
                    let html = '';
                    result.documents.forEach(doc => {
                        html += '<div class="doc-item">';
                        html += '<strong>' + doc.filename + '</strong> ';
                        html += '<span style="color: #666;">(' + doc.total_pages + ' pages, ' + Math.round(doc.file_size/1024) + ' KB)</span>';
                        html += '<br><small>Uploaded: ' + new Date(doc.upload_date).toLocaleString() + '</small>';
                        html += '</div>';
                    });
                    docsDiv.innerHTML = html;
                } else {
                    docsDiv.innerHTML = '<p>📝 No documents uploaded yet. Upload some PDFs to get started!</p>';
                }
            } catch (error) {
                document.getElementById('documentsList').innerHTML = '<p>❌ Error loading documents: ' + error.message + '</p>';
            }
        }
        
        // Load documents on page load
        loadDocuments();
        
        // Allow Enter key in chat input
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_pdfs():
    try:
        if 'pdfs' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF files uploaded'})
        
        files = request.files.getlist('pdfs')
        processed_count = 0
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not file.filename.lower().endswith('.pdf'):
                errors.append(f"{file.filename} is not a PDF file")
                continue
            
            try:
                success = pdf_rag.process_pdf_file(file, file.filename)
                if success:
                    processed_count += 1
                else:
                    errors.append(f"Failed to process {file.filename}")
            except Exception as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
        
        if processed_count > 0:
            message = f"Successfully processed {processed_count} PDF(s)"
            if errors:
                message += f". Errors: {'; '.join(errors)}"
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': f"No PDFs processed. Errors: {'; '.join(errors)}"})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/documents')
def get_documents():
    try:
        docs = PDFDocument.query.all()
        documents = [{
            'id': doc.id,
            'filename': doc.filename,
            'total_pages': doc.total_pages,
            'file_size': doc.file_size,
            'upload_date': doc.upload_date.isoformat(),
            'processed': doc.processed
        } for doc in docs]
        
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    start_time = datetime.now()
    
    try:
        data = request.json
        query = data.get('query', '')
        user_id = data.get('user_id', 'anonymous')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'})
        
        # Search documents
        retrieved_docs = pdf_rag.search_documents(query, top_k=5)
        
        # Generate response
        response, generation_score = pdf_rag.generate_response(query, retrieved_docs)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        relevance_score = retrieved_docs[0]['combined_score'] if retrieved_docs else 0.0
        
        # Save to history
        history_entry = ChatHistory(
            user_id=user_id,
            query=query,
            response=response,
            retrieved_chunks=json.dumps([{
                'content': doc['content'][:200] + '...',
                'metadata': doc['metadata'],
                'score': doc['combined_score']
            } for doc in retrieved_docs[:3]]),
            relevance_score=relevance_score,
            processing_time=processing_time
        )
        db.session.add(history_entry)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'relevance_score': relevance_score,
            'processing_time': processing_time,
            'sources_found': len(retrieved_docs)
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/metrics')
def get_metrics():
    try:
        total_docs = PDFDocument.query.count()
        total_chunks = DocumentChunk.query.count()
        total_chats = ChatHistory.query.count()
        
        return jsonify({
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'total_conversations': total_chats,
            'system_status': 'FREE RAG System Active',
            'models_used': {
                'embeddings': 'all-MiniLM-L6-v2',
                'generation': 'GPT-2',
                'search': 'FAISS + BM25 + TF-IDF'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        pdf_rag.load_existing_documents()
    
    logger.info("🚀 FREE PDF RAG Chatbot starting...")
    logger.info("💰 Zero cost - All components are free and open source!")
    logger.info("🔒 Private - All processing happens locally on your machine!")
    
    app.run(debug=True, port=5000, host='0.0.0.0')