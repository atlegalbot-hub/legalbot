"""
Educational Law & Constitution RAG Chatbot with Scenario-Based Learning
Designed for students to understand laws, rights, and consequences through interactive scenarios
100% FREE & Educational Focus
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///educational_law_rag.db'
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
    document_type = db.Column(db.String(50), default='general')  # general, law, constitution
    
class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdf_document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    embedding_vector = db.Column(db.PickleType, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    content_type = db.Column(db.String(50), default='general')  # law, rights, punishment, procedure
    
class ScenarioCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_title = db.Column(db.String(200), nullable=False)
    scenario_description = db.Column(db.Text, nullable=False)
    legal_analysis = db.Column(db.Text, nullable=False)
    applicable_laws = db.Column(db.Text, nullable=False)
    consequences = db.Column(db.Text, nullable=False)
    age_group = db.Column(db.String(20), nullable=False)  # child, teen, adult
    severity_level = db.Column(db.String(20), nullable=False)  # minor, moderate, serious
    educational_note = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), default='general')  # general, scenario, legal_question
    retrieved_chunks = db.Column(db.Text, nullable=True)
    scenario_triggered = db.Column(db.Boolean, default=False)
    relevance_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)
    user_age_group = db.Column(db.String(20), nullable=True)

class EducationalLawRAG:
    """
    Educational Law RAG Pipeline with Scenario-Based Learning
    Focuses on teaching students about laws, rights, and consequences
    """
    
    def __init__(self):
        logger.info("Initializing Educational Law RAG Pipeline...")
        
        # Download NLTK data
        self._download_nltk_data()
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # Initialize FAISS index
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Initialize generation model
        self.init_generation_model()
        
        # Document storage
        self.documents = []
        self.document_metadata = []
        
        # Search components
        self.bm25 = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.tfidf_matrix = None
        
        # Educational content
        self.init_educational_scenarios()
        
        # PDF upload directory
        self.upload_dir = Path("uploaded_pdfs")
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("Educational Law RAG Pipeline initialized!")
    
    def _download_nltk_data(self):
        """Download NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            logger.warning("NLTK data download failed")
    
    def init_generation_model(self):
        """Initialize generation model"""
        try:
            model_name = "gpt2"
            self.generation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.generation_model = AutoModelForCausalLM.from_pretrained(model_name)
            self.generation_tokenizer.pad_token = self.generation_tokenizer.eos_token
            logger.info("GPT-2 model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load GPT-2: {e}")
            self.generation_model = None
            self.generation_tokenizer = None
    
    def init_educational_scenarios(self):
        """Initialize educational law scenarios"""
        try:
            # Check if scenarios already exist
            if ScenarioCase.query.count() == 0:
                self._create_educational_scenarios()
                logger.info("Educational scenarios initialized")
        except Exception as e:
            logger.error(f"Error initializing scenarios: {e}")
    
    def _create_educational_scenarios(self):
        """Create educational law scenarios for different age groups"""
        
        scenarios = [
            {
                "title": "Scenario: Taking Someone's Bicycle Without Permission",
                "description": "A 12-year-old takes a bicycle from school premises without the owner's permission, intending to return it after a ride.",
                "legal_analysis": "This constitutes theft under Section 378 of Indian Penal Code, even if intention was to return the item.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Juvenile Justice Act 2015",
                "consequences": "For children under 16: Counseling, community service, parental guidance. No criminal record. Focus on rehabilitation and education.",
                "age_group": "child",
                "severity_level": "minor",
                "educational_note": "Taking someone's property without permission is theft, even if you plan to return it. Always ask permission first. Children are treated with care under Juvenile Justice Act."
            },
            {
                "title": "Scenario: Cyberbullying on Social Media",
                "description": "A 15-year-old posts mean comments and shares embarrassing photos of a classmate on social media platforms.",
                "legal_analysis": "Cyberbullying involves multiple legal violations including harassment, defamation, and violation of privacy laws.",
                "applicable_laws": "Information Technology Act 2000 Section 66A (now struck down but similar provisions exist), Section 67, Indian Penal Code Section 499 (Defamation), Section 509 (Insulting modesty)",
                "consequences": "For teenagers (16-18): Counseling, digital literacy education, possible community service, parental involvement. May face school disciplinary action.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Cyberbullying can cause serious emotional harm and has legal consequences. Think before you post. Treat others online as you would in person."
            },
            {
                "title": "Scenario: Shoplifting Expensive Item",
                "description": "A 17-year-old steals an expensive mobile phone from an electronics store.",
                "legal_analysis": "Theft of valuable property is a serious offense. Value of stolen goods affects severity of punishment.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Section 380 (Theft in dwelling house), Juvenile Justice Act provisions for children in conflict with law",
                "consequences": "For teens approaching 18: Stronger intervention, possible detention in observation home, mandatory counseling, restitution to victim, family involvement.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Stealing expensive items has serious consequences. The law considers the value of stolen goods. Better to work and save money to buy what you want legally."
            },
            {
                "title": "Scenario: Underage Driving Without License",
                "description": "A 16-year-old drives a motorbike without a license and gets caught by traffic police.",
                "legal_analysis": "Driving without a license violates Motor Vehicle Act. Additional concerns for underage driving.",
                "applicable_laws": "Motor Vehicle Act 1988 Section 3 (driving without license), Section 4 (age restrictions), Juvenile Justice Act",
                "consequences": "Fine, vehicle impoundment, parental responsibility, mandatory traffic education, possible restriction on future license eligibility.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Driving without a license is dangerous and illegal. Wait until you're eligible and get proper training. Road safety protects everyone."
            },
            {
                "title": "Scenario: Examination Cheating",
                "description": "A student uses unfair means during a school examination by copying from hidden notes.",
                "legal_analysis": "While primarily an academic issue, repeated cheating can have legal implications in competitive exams.",
                "applicable_laws": "Educational institution rules, potential fraud charges in competitive exams, Indian Penal Code Section 419 (Cheating by impersonation)",
                "consequences": "School disciplinary action, exam cancellation, possible debarment, parental involvement, counseling on academic integrity.",
                "age_group": "teen",
                "severity_level": "minor",
                "educational_note": "Cheating undermines your education and is unfair to honest students. Focus on learning rather than just grades. Success through cheating is temporary."
            },
            {
                "title": "Scenario: Vandalizing Public Property",
                "description": "A group of teenagers spray paint graffiti on a government building wall.",
                "legal_analysis": "Vandalism of public property is a criminal offense that affects community resources and taxpayer money.",
                "applicable_laws": "Indian Penal Code Section 425 (Mischief), Section 427 (Mischief causing damage), Prevention of Damage to Public Property Act 1984",
                "consequences": "Fine equal to damage cost, community service cleaning public areas, education about civic responsibility, parental liability for damages.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Public property belongs to everyone. Damaging it wastes taxpayer money that could be used for schools, hospitals, and development."
            },
            {
                "title": "Scenario: Sharing Inappropriate Content",
                "description": "A teenager forwards inappropriate or private images without consent through messaging apps.",
                "legal_analysis": "Sharing private content without consent violates privacy and dignity, potentially constituting sexual harassment.",
                "applicable_laws": "Information Technology Act Section 66E (Violation of privacy), Section 67/67A (obscene content), Indian Penal Code Section 354C (Voyeurism)",
                "consequences": "Serious legal action possible, counseling on digital ethics, device restrictions, education on consent and privacy rights.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Sharing private content without permission violates someone's dignity and privacy. Always respect others' boundaries, online and offline."
            },
            {
                "title": "Scenario: Substance Abuse (Underage Drinking)",
                "description": "A 16-year-old is caught consuming alcohol at a party.",
                "legal_analysis": "Underage drinking violates prohibition laws and can lead to health and safety concerns.",
                "applicable_laws": "State Prohibition Laws, Juvenile Justice Act, Indian Penal Code provisions on public intoxication",
                "consequences": "Counseling on substance abuse, health education, parental involvement, possible restriction on social activities, rehabilitation if needed.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Underage drinking is illegal and harmful to developing brain and body. Focus on healthy activities and making responsible choices."
            }
        ]
        
        for scenario_data in scenarios:
            scenario = ScenarioCase(
                scenario_title=scenario_data["title"],
                scenario_description=scenario_data["description"],
                legal_analysis=scenario_data["legal_analysis"],
                applicable_laws=scenario_data["applicable_laws"],
                consequences=scenario_data["consequences"],
                age_group=scenario_data["age_group"],
                severity_level=scenario_data["severity_level"],
                educational_note=scenario_data["educational_note"]
            )
            db.session.add(scenario)
        
        db.session.commit()
        logger.info("Educational scenarios created successfully")
    
    def detect_scenario_query(self, query: str) -> Dict:
        """Detect if query is asking about legal scenarios or consequences"""
        query_lower = query.lower()
        
        scenario_indicators = [
            'what if i', 'what happens if', 'what would happen', 'if i do', 'if someone',
            'what crime', 'what law', 'what punishment', 'what penalty', 'consequences',
            'illegal', 'against law', 'breaking law', 'get in trouble', 'arrested',
            'jail', 'prison', 'fine', 'punishment', 'penalty'
        ]
        
        activity_keywords = {
            'theft': ['steal', 'theft', 'take without permission', 'shoplifting', 'robbery'],
            'cybercrime': ['cyberbullying', 'online harassment', 'hacking', 'sharing photos', 'social media'],
            'violence': ['fight', 'hit someone', 'assault', 'violence', 'hurt'],
            'driving': ['drive without license', 'underage driving', 'traffic violation'],
            'vandalism': ['graffiti', 'damage property', 'vandalism', 'break things'],
            'drugs': ['drinking', 'alcohol', 'drugs', 'smoking', 'substance'],
            'cheating': ['cheat in exam', 'copying', 'plagiarism', 'unfair means'],
            'privacy': ['share photos', 'private content', 'without permission']
        }
        
        # Check for scenario indicators
        has_scenario_indicator = any(indicator in query_lower for indicator in scenario_indicators)
        
        if has_scenario_indicator:
            # Determine activity type
            for activity_type, keywords in activity_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    return {
                        'is_scenario': True,
                        'activity_type': activity_type,
                        'query_type': 'legal_scenario'
                    }
            
            return {
                'is_scenario': True,
                'activity_type': 'general',
                'query_type': 'legal_scenario'
            }
        
        return {'is_scenario': False, 'query_type': 'general'}
    
    def find_relevant_scenarios(self, query: str, activity_type: str = None) -> List[Dict]:
        """Find relevant educational scenarios"""
        try:
            scenarios = ScenarioCase.query.all()
            relevant_scenarios = []
            
            query_words = set(query.lower().split())
            
            for scenario in scenarios:
                # Calculate relevance score
                scenario_text = (
                    scenario.scenario_description + " " + 
                    scenario.legal_analysis + " " + 
                    scenario.applicable_laws + " " + 
                    scenario.educational_note
                ).lower()
                
                scenario_words = set(scenario_text.split())
                relevance_score = len(query_words.intersection(scenario_words))
                
                if relevance_score > 0:
                    relevant_scenarios.append({
                        'scenario': scenario,
                        'relevance_score': relevance_score
                    })
            
            # Sort by relevance
            relevant_scenarios.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return relevant_scenarios[:3]  # Return top 3 most relevant
            
        except Exception as e:
            logger.error(f"Error finding scenarios: {e}")
            return []
    
    def generate_scenario_response(self, query: str, scenarios: List[Dict], user_age: str = "teen") -> str:
        """Generate educational response for scenario-based queries"""
        
        if not scenarios:
            return self._generate_general_legal_guidance(query, user_age)
        
        response = "🎓 **Educational Legal Scenario Analysis**\n\n"
        
        # Add appropriate warning
        response += "⚠️ **Important**: This is for educational purposes only. Always consult legal experts for real situations.\n\n"
        
        for i, scenario_data in enumerate(scenarios[:2]):  # Limit to 2 scenarios
            scenario = scenario_data['scenario']
            
            response += f"📚 **Educational Example {i+1}: {scenario.scenario_title}**\n\n"
            
            response += f"**Scenario**: {scenario.scenario_description}\n\n"
            
            response += f"**Legal Analysis**: {scenario.legal_analysis}\n\n"
            
            response += f"**Applicable Laws**: {scenario.applicable_laws}\n\n"
            
            response += f"**Consequences for Young People**: {scenario.consequences}\n\n"
            
            response += f"💡 **Educational Note**: {scenario.educational_note}\n\n"
            
            response += "---\n\n"
        
        # Add age-appropriate guidance
        if user_age == "child":
            response += "👶 **For Young Students**: Remember that children are protected under special laws. The focus is always on education, not punishment.\n\n"
        elif user_age == "teen":
            response += "👦👧 **For Teenagers**: You're old enough to understand consequences. Make good choices and think about how your actions affect others.\n\n"
        
        # Add general guidance
        response += "📖 **Key Learning Points**:\n"
        response += "• Laws exist to protect everyone in society\n"
        response += "• Young people get special consideration under Juvenile Justice Act\n"
        response += "• It's better to learn about consequences through education than experience\n"
        response += "• When in doubt, ask parents, teachers, or legal advisors\n"
        response += "• Focus on being a responsible citizen\n\n"
        
        response += "🎯 **Remember**: The goal of law is not just punishment, but creating a safe and fair society for everyone!"
        
        return response
    
    def _generate_general_legal_guidance(self, query: str, user_age: str) -> str:
        """Generate general legal guidance when no specific scenarios match"""
        
        response = "⚖️ **General Legal Education**\n\n"
        
        response += "I understand you're curious about legal matters. Here's some general guidance:\n\n"
        
        response += "📚 **Understanding Laws**:\n"
        response += "• Laws are rules that help society function peacefully\n"
        response += "• They protect people's rights and property\n"
        response += "• Everyone, including young people, has both rights and responsibilities\n\n"
        
        response += "👨‍⚖️ **For Young People**:\n"
        response += "• Children and teenagers have special protections under law\n"
        response += "• The Juvenile Justice Act focuses on rehabilitation, not punishment\n"
        response += "• Parents and guardians are responsible for guiding young people\n\n"
        
        response += "🎓 **Educational Approach**:\n"
        response += "• Learn about laws through education, not by breaking them\n"
        response += "• Understand that actions have consequences\n"
        response += "• Respect others' rights and property\n"
        response += "• When unsure, ask trusted adults for guidance\n\n"
        
        response += "💡 **Good Resources**:\n"
        response += "• School counselors and teachers\n"
        response += "• Legal literacy programs\n"
        response += "• Government educational websites\n"
        response += "• Constitutional and legal textbooks\n\n"
        
        response += "Remember: The purpose of learning about laws is to become a responsible citizen who contributes positively to society!"
        
        return response
    
    def extract_text_from_pdf(self, pdf_file) -> Tuple[List[Dict], Dict]:
        """Extract text from PDF using free libraries"""
        try:
            # Try pdfplumber first
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
            
            # Fallback to PyPDF2
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
        """Intelligent text chunking for legal documents"""
        chunks = []
        
        for page_data in page_content:
            page_num = page_data['page']
            text = page_data['text']
            
            # Determine content type based on keywords
            content_type = self._classify_legal_content(text)
            
            # Split into sentences
            try:
                sentences = sent_tokenize(text)
            except:
                sentences = [s.strip() for s in text.split('.') if s.strip()]
            
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_words = len(sentence.split())
                
                if current_length + sentence_words > chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'page_number': page_num,
                        'chunk_index': len(chunks),
                        'word_count': current_length,
                        'sentences': len(current_chunk),
                        'content_type': content_type
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
                    'sentences': len(current_chunk),
                    'content_type': content_type
                })
        
        return chunks
    
    def _classify_legal_content(self, text: str) -> str:
        """Classify legal content type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['punishment', 'penalty', 'fine', 'imprisonment', 'jail']):
            return 'punishment'
        elif any(word in text_lower for word in ['right', 'fundamental right', 'article']):
            return 'rights'
        elif any(word in text_lower for word in ['procedure', 'process', 'court', 'trial']):
            return 'procedure'
        elif any(word in text_lower for word in ['section', 'ipc', 'penal code', 'act']):
            return 'law'
        else:
            return 'general'
    
    def process_pdf_file(self, pdf_file, filename: str, document_type: str = 'general') -> bool:
        """Process uploaded PDF with document type classification"""
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
            
            # Auto-detect document type if not specified
            if document_type == 'general':
                document_type = self._detect_document_type(page_content)
            
            # Save PDF document record
            pdf_doc = PDFDocument(
                filename=filename,
                file_hash=file_hash,
                total_pages=metadata.get('total_pages', 0),
                file_size=len(file_content),
                document_type=document_type,
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
                # Generate embedding
                embedding = self.embedding_model.encode(chunk['content'])
                
                # Save chunk to database
                db_chunk = DocumentChunk(
                    pdf_id=pdf_doc.id,
                    chunk_index=chunk['chunk_index'],
                    content=chunk['content'],
                    page_number=chunk['page_number'],
                    embedding_vector=embedding.tolist(),
                    metadata=chunk,
                    content_type=chunk.get('content_type', 'general')
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
                    'chunk_index': chunk['chunk_index'],
                    'content_type': chunk.get('content_type', 'general'),
                    'document_type': document_type
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
    
    def _detect_document_type(self, page_content: List[Dict]) -> str:
        """Auto-detect document type based on content"""
        all_text = " ".join([page['text'] for page in page_content]).lower()
        
        if any(term in all_text for term in ['constitution', 'fundamental rights', 'article', 'preamble']):
            return 'constitution'
        elif any(term in all_text for term in ['penal code', 'criminal law', 'ipc', 'section']):
            return 'law'
        else:
            return 'general'
    
    def _rebuild_search_indexes(self):
        """Rebuild search indexes"""
        try:
            if self.documents:
                # BM25 index
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                
                # TF-IDF index
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
                    'chunk_index': chunk.chunk_index,
                    'content_type': chunk.content_type,
                    'document_type': pdf_doc.document_type if pdf_doc else 'general'
                })
            
            # Rebuild search indexes
            self._rebuild_search_indexes()
            
            logger.info(f"Loaded {len(chunks)} existing document chunks")
            
        except Exception as e:
            logger.error(f"Error loading existing documents: {e}")
    
    def search_documents(self, query: str, top_k: int = 5, content_type: str = None) -> List[Dict]:
        """Multi-method document search with content type filtering"""
        if not self.documents:
            return []
        
        results = []
        
        # 1. Semantic search with FAISS
        try:
            query_embedding = self.embedding_model.encode(query).astype('float32')
            semantic_scores, semantic_indices = self.faiss_index.search(
                query_embedding.reshape(1, -1), min(top_k * 2, len(self.documents))
            )
            
            for score, idx in zip(semantic_scores[0], semantic_indices[0]):
                if idx < len(self.documents) and score > 0:
                    metadata = self.document_metadata[idx]
                    
                    # Filter by content type if specified
                    if content_type and metadata.get('content_type') != content_type:
                        continue
                    
                    results.append({
                        'content': self.documents[idx],
                        'metadata': metadata,
                        'semantic_score': float(score),
                        'index': idx
                    })
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
        
        # 2. Keyword search with BM25
        try:
            if self.bm25:
                query_tokens = query.split()
                bm25_scores = self.bm25.get_scores(query_tokens)
                
                for idx, score in enumerate(bm25_scores):
                    if idx < len(results) and score > 0:
                        results[idx]['bm25_score'] = float(score)
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
        
        # 3. TF-IDF search
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
    
    def generate_response(self, query: str, retrieved_docs: List[Dict], query_type: str = 'general', scenarios: List[Dict] = None, user_age: str = "teen") -> Tuple[str, float]:
        """Generate educational response based on query type"""
        
        if query_type == 'legal_scenario' and scenarios:
            return self.generate_scenario_response(query, scenarios, user_age), 0.9
        
        if not retrieved_docs:
            if query_type == 'legal_scenario':
                return self.generate_scenario_response(query, [], user_age), 0.7
            else:
                return self._generate_fallback_response(query), 0.5
        
        # Prepare context
        context = self._prepare_context(retrieved_docs[:3])
        
        # Generate educational response
        response = self._educational_template_generation(query, context, retrieved_docs, query_type)
        
        return response, 0.8
    
    def _educational_template_generation(self, query: str, context: str, docs: List[Dict], query_type: str) -> str:
        """Generate educational response with legal guidance"""
        
        # Determine response type
        query_lower = query.lower()
        
        if query_type == 'legal_scenario':
            response_prefix = "⚖️ **Educational Legal Analysis:**\n\n"
        elif any(word in query_lower for word in ['right', 'fundamental']):
            response_prefix = "🏛️ **Constitutional Rights Education:**\n\n"
        elif any(word in query_lower for word in ['law', 'section', 'act']):
            response_prefix = "📚 **Legal Education:**\n\n"
        elif any(word in query_lower for word in ['punishment', 'penalty']):
            response_prefix = "⚖️ **Understanding Legal Consequences:**\n\n"
        else:
            response_prefix = "📖 **Educational Information:**\n\n"
        
        # Extract key information
        key_info = self._extract_key_information(context, query)
        
        # Build response
        response = response_prefix + key_info + "\n\n"
        
        # Add educational context
        if any(word in query_lower for word in ['child', 'children', 'young', 'student']):
            response += "👶 **For Young People**: Remember that children and teenagers have special protections under the Juvenile Justice Act. The law focuses on rehabilitation and education rather than punishment.\n\n"
        
        # Add source information
        if docs:
            response += "📚 **Sources from Your Documents:**\n"
            for i, doc in enumerate(docs[:3]):
                metadata = doc['metadata']
                filename = metadata.get('filename', 'Unknown')
                page = metadata.get('page_number', 'Unknown')
                content_type = metadata.get('content_type', 'general')
                response += f"• {filename} (Page {page}) - {content_type.title()} Content\n"
            response += "\n"
        
        # Add educational guidance
        response += "🎓 **Educational Guidance:**\n"
        response += "• Laws exist to protect everyone and maintain social order\n"
        response += "• Understanding laws helps you make better decisions\n"
        response += "• When in doubt, consult with teachers, parents, or legal advisors\n"
        response += "• Focus on being a responsible and law-abiding citizen\n\n"
        
        response += "💡 **Remember**: This information is for educational purposes. Always seek professional legal advice for real situations."
        
        return response
    
    def _prepare_context(self, docs: List[Dict]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs):
            metadata = doc['metadata']
            filename = metadata.get('filename', 'Unknown')
            page = metadata.get('page_number', 'Unknown')
            content_type = metadata.get('content_type', 'general')
            score = doc.get('combined_score', 0)
            
            context_parts.append(
                f"**Source {i+1}** (File: {filename}, Page: {page}, Type: {content_type}, Relevance: {score:.2f}):\n"
                f"{doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
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
        """Educational fallback response"""
        return """
📚 **Educational Legal Information**

I don't have specific information about your query in the uploaded documents, but I can provide some general educational guidance:

🏛️ **Understanding Laws and Rights:**
• Laws are designed to protect everyone in society
• Everyone has both rights and responsibilities
• Young people have special protections under the law

⚖️ **For Students Learning About Law:**
• Focus on understanding why laws exist
• Learn about your rights and how to exercise them responsibly
• Understand that actions have consequences
• Respect others' rights and property

🎓 **Educational Resources:**
• Constitutional textbooks and legal guides
• School civics and social studies materials
• Government educational websites
• Legal literacy programs

💡 **Tips for Better Results:**
• Upload relevant legal or constitutional documents
• Ask specific questions about laws, rights, or procedures
• Use keywords like "constitution," "rights," "laws," or "procedures"

📄 **Try uploading documents like:**
• Constitutional texts
• Legal textbooks
• Government publications
• Educational legal materials

Remember: Learning about laws helps you become a responsible citizen! 🇮🇳
        """

# Initialize Educational RAG Pipeline
edu_law_rag = EducationalLawRAG()

# Flask Routes
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Educational Law & Constitution RAG Chatbot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header { text-align: center; margin-bottom: 30px; color: #333; }
        .header h1 { color: #4a5568; margin-bottom: 10px; }
        .header p { color: #718096; }
        .section { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
        .upload-section { background: linear-gradient(135deg, #e8f4f8 0%, #d6f5f5 100%); }
        .chat-section { background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%); }
        .scenarios-section { background: linear-gradient(135deg, #fffbf0 0%, #fef5e7 100%); }
        .file-input { margin: 10px 0; padding: 10px; border: 2px dashed #4299e1; border-radius: 8px; background: #ebf8ff; }
        .btn { background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(66, 153, 225, 0.4); }
        .btn-scenario { background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); }
        .status { margin: 10px 0; padding: 15px; border-radius: 8px; font-weight: bold; }
        .success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
        .chat-input { width: 70%; padding: 12px; border: 2px solid #cbd5e0; border-radius: 8px; font-size: 14px; }
        .chat-input:focus { border-color: #4299e1; outline: none; }
        .chat-response { background: white; padding: 20px; margin: 15px 0; border-radius: 12px; border-left: 5px solid #4299e1; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .user-message { border-left-color: #48bb78; background: #f0fff4; }
        .documents-list { margin: 20px 0; }
        .doc-item { background: white; padding: 15px; margin: 8px 0; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .scenarios-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 20px 0; }
        .scenario-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .scenario-card h4 { color: #2d3748; margin-bottom: 10px; }
        .scenario-card p { color: #4a5568; font-size: 14px; line-height: 1.5; }
        .age-selector { margin: 15px 0; }
        .age-selector select { padding: 8px 12px; border: 1px solid #cbd5e0; border-radius: 6px; background: white; }
        .feature-highlight { background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%); padding: 15px; border-radius: 10px; margin: 15px 0; border: 1px solid #81e6d9; }
        .warning-box { background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%); padding: 15px; border-radius: 10px; margin: 15px 0; border: 1px solid #fc8181; color: #742a2a; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓⚖️ Educational Law & Constitution RAG Chatbot</h1>
            <p><strong>Learn about Laws, Rights, and Consequences through Interactive Education</strong></p>
            <p>💰 100% FREE • 🔒 Private • 📚 Educational Focus • 🏛️ Constitution & Law Learning</p>
        </div>
        
        <div class="warning-box">
            ⚠️ <strong>Educational Purpose Only</strong>: This chatbot is designed for educational learning about laws and constitution. 
            Always consult legal professionals for real legal situations.
        </div>
        
        <div class="feature-highlight">
            <h3>🌟 Special Features for Law Education:</h3>
            <ul>
                <li>📚 <strong>PDF Upload</strong>: Upload constitution, law books, legal documents</li>
                <li>🎭 <strong>Scenario-Based Learning</strong>: Learn consequences through educational examples</li>
                <li>👶👦👧 <strong>Age-Appropriate</strong>: Different guidance for children and teenagers</li>
                <li>⚖️ <strong>Legal Education</strong>: Understand rights, laws, and civic responsibilities</li>
                <li>🏛️ <strong>Constitutional Learning</strong>: Deep dive into Indian Constitution</li>
            </ul>
        </div>
        
        <div class="section upload-section">
            <h2>📄 Upload Legal & Constitutional Documents</h2>
            <p>Upload PDFs of constitution, law books, legal guides, or educational materials</p>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="file-input">
                    <input type="file" id="pdfFile" name="pdf" accept=".pdf" multiple>
                    <p style="margin: 5px 0; color: #4a5568;">📚 Recommended: Constitution, Legal textbooks, Law guides, Rights documents</p>
                </div>
                <br>
                <button type="submit" class="btn">📤 Upload Legal Documents</button>
            </form>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="section scenarios-section">
            <h2>🎭 Educational Legal Scenarios</h2>
            <p>Learn about laws and consequences through educational examples</p>
            
            <div class="age-selector">
                <label for="ageGroup"><strong>👤 Your Age Group:</strong></label>
                <select id="ageGroup">
                    <option value="child">👶 Child (8-12 years)</option>
                    <option value="teen" selected>👦👧 Teenager (13-17 years)</option>
                    <option value="adult">👨👩 Adult (18+ years)</option>
                </select>
            </div>
            
            <div class="scenarios-grid">
                <div class="scenario-card">
                    <h4>🚲 Property & Theft</h4>
                    <p>Learn about taking things without permission, theft laws, and consequences for young people</p>
                    <button onclick="askScenario('What happens if I take someone\\'s bicycle without permission?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
                
                <div class="scenario-card">
                    <h4>💻 Cyberbullying</h4>
                    <p>Understand online harassment, cyberbullying laws, and digital responsibility</p>
                    <button onclick="askScenario('What are the consequences of cyberbullying someone online?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏪 Shoplifting</h4>
                    <p>Learn about theft in stores, legal consequences, and making better choices</p>
                    <button onclick="askScenario('What happens if I steal something from a store?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏍️ Traffic Rules</h4>
                    <p>Understand driving laws, license requirements, and road safety responsibilities</p>
                    <button onclick="askScenario('What happens if I drive without a license?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🎨 Vandalism</h4>
                    <p>Learn about property damage, public property laws, and civic responsibility</p>
                    <button onclick="askScenario('What happens if I damage public property?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
                
                <div class="scenario-card">
                    <h4>📱 Privacy Rights</h4>
                    <p>Understand privacy laws, sharing content without permission, and digital ethics</p>
                    <button onclick="askScenario('What happens if I share someone\\'s private photos?')" class="btn btn-scenario">🎓 Learn More</button>
                </div>
            </div>
        </div>
        
        <div class="documents-list">
            <h3>📚 Uploaded Documents</h3>
            <div id="documentsList">Loading...</div>
        </div>
        
        <div class="section chat-section">
            <h2>💬 Chat with Your Legal & Constitutional Documents</h2>
            <p>Ask questions about laws, rights, constitution, or explore educational scenarios</p>
            <div id="chatMessages"></div>
            <br>
            <input type="text" id="chatInput" class="chat-input" placeholder="Ask about laws, rights, constitution, or scenarios like 'What happens if...'">
            <button onclick="sendMessage()" class="btn">🚀 Ask Question</button>
            
            <div style="margin-top: 15px; padding: 10px; background: #e6fffa; border-radius: 8px; border: 1px solid #81e6d9;">
                <p><strong>💡 Try asking:</strong></p>
                <ul style="margin: 5px 0; color: #2d3748;">
                    <li>"What are fundamental rights?"</li>
                    <li>"What happens if someone steals something?"</li>
                    <li>"Explain Article 21 of Constitution"</li>
                    <li>"What are the consequences of cyberbullying?"</li>
                    <li>"What laws protect children?"</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        function askScenario(question) {
            document.getElementById('chatInput').value = question;
            sendMessage();
        }

        // Upload functionality
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            const files = document.getElementById('pdfFile').files;
            
            for (let file of files) {
                formData.append('pdfs', file);
            }
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status warning">⏳ Uploading and processing legal documents...</div>';
            
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
            
            const ageGroup = document.getElementById('ageGroup').value;
            
            // Add user message
            addMessage('user', query);
            input.value = '';
            
            // Add loading message
            const loadingId = addMessage('bot', '🤔 Analyzing your question and searching documents...');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: query, 
                        user_id: 'student_' + Date.now(),
                        age_group: ageGroup
                    })
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
            messageDiv.className = 'chat-response ' + (type === 'user' ? 'user-message' : '');
            
            let html = '<strong>' + (type === 'user' ? '👤 You:' : '🤖 Educational Law Bot:') + '</strong><br>';
            html += content.replace(/\\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            if (metadata) {
                html += '<br><small style="color: #666;">⚡ Processing: ' + (metadata.processing_time || 'N/A') + 's';
                if (metadata.query_type) {
                    html += ' | 📝 Type: ' + metadata.query_type.replace('_', ' ');
                }
                if (metadata.scenario_triggered) {
                    html += ' | 🎭 Educational scenario provided';
                }
                html += '</small>';
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
                        const typeEmoji = doc.document_type === 'constitution' ? '🏛️' : 
                                        doc.document_type === 'law' ? '⚖️' : '📄';
                        html += '<div class="doc-item">';
                        html += typeEmoji + ' <strong>' + doc.filename + '</strong> ';
                        html += '<span style="color: #666;">(' + doc.total_pages + ' pages, ' + Math.round(doc.file_size/1024) + ' KB)</span>';
                        html += '<br><small>Type: ' + doc.document_type + ' | Uploaded: ' + new Date(doc.upload_date).toLocaleString() + '</small>';
                        html += '</div>';
                    });
                    docsDiv.innerHTML = html;
                } else {
                    docsDiv.innerHTML = '<p>📝 No legal documents uploaded yet. Upload constitution, law books, or legal guides to get started!</p>';
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
                # Auto-detect document type based on filename
                filename_lower = file.filename.lower()
                if any(word in filename_lower for word in ['constitution', 'fundamental', 'rights']):
                    doc_type = 'constitution'
                elif any(word in filename_lower for word in ['law', 'penal', 'criminal', 'ipc']):
                    doc_type = 'law'
                else:
                    doc_type = 'general'
                
                success = edu_law_rag.process_pdf_file(file, file.filename, doc_type)
                if success:
                    processed_count += 1
                else:
                    errors.append(f"Failed to process {file.filename}")
            except Exception as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
        
        if processed_count > 0:
            message = f"Successfully processed {processed_count} legal document(s)"
            if errors:
                message += f". Errors: {'; '.join(errors)}"
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': f"No documents processed. Errors: {'; '.join(errors)}"})
            
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
            'processed': doc.processed,
            'document_type': doc.document_type
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
        age_group = data.get('age_group', 'teen')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'})
        
        # Detect if this is a scenario-based query
        scenario_detection = edu_law_rag.detect_scenario_query(query)
        query_type = scenario_detection['query_type']
        is_scenario = scenario_detection['is_scenario']
        
        scenarios = []
        retrieved_docs = []
        
        if is_scenario:
            # Find relevant educational scenarios
            scenarios = edu_law_rag.find_relevant_scenarios(
                query, 
                scenario_detection.get('activity_type')
            )
            
            # Also search documents for additional context
            retrieved_docs = edu_law_rag.search_documents(query, top_k=3)
        else:
            # Regular document search
            retrieved_docs = edu_law_rag.search_documents(query, top_k=5)
        
        # Generate educational response
        response, generation_score = edu_law_rag.generate_response(
            query, retrieved_docs, query_type, scenarios, age_group
        )
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        relevance_score = retrieved_docs[0]['combined_score'] if retrieved_docs else 0.0
        
        # Save to history
        history_entry = ChatHistory(
            user_id=user_id,
            query=query,
            response=response,
            query_type=query_type,
            retrieved_chunks=json.dumps([{
                'content': doc['content'][:200] + '...',
                'metadata': doc['metadata'],
                'score': doc['combined_score']
            } for doc in retrieved_docs[:3]]),
            scenario_triggered=is_scenario,
            relevance_score=relevance_score,
            processing_time=processing_time,
            user_age_group=age_group
        )
        db.session.add(history_entry)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'relevance_score': relevance_score,
            'processing_time': processing_time,
            'sources_found': len(retrieved_docs),
            'query_type': query_type,
            'scenario_triggered': is_scenario,
            'scenarios_found': len(scenarios),
            'educational_focus': True
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
        scenario_chats = ChatHistory.query.filter_by(scenario_triggered=True).count()
        
        # Document type breakdown
        constitution_docs = PDFDocument.query.filter_by(document_type='constitution').count()
        law_docs = PDFDocument.query.filter_by(document_type='law').count()
        general_docs = PDFDocument.query.filter_by(document_type='general').count()
        
        return jsonify({
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'total_conversations': total_chats,
            'scenario_conversations': scenario_chats,
            'document_types': {
                'constitution': constitution_docs,
                'law': law_docs,
                'general': general_docs
            },
            'educational_scenarios': ScenarioCase.query.count(),
            'system_status': 'Educational Law RAG System Active',
            'models_used': {
                'embeddings': 'all-MiniLM-L6-v2',
                'generation': 'GPT-2 + Educational Templates',
                'search': 'FAISS + BM25 + TF-IDF',
                'scenarios': 'Rule-based + Educational Database'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        edu_law_rag.load_existing_documents()
    
    logger.info("🚀 Educational Law & Constitution RAG Chatbot starting...")
    logger.info("🎓 Focused on teaching students about laws, rights, and consequences!")
    logger.info("💰 100% FREE and educationally responsible!")
    
    app.run(debug=True, port=5000, host='0.0.0.0')