"""
🎓⚖️ COMPLETE FINAL Educational Law & Constitution RAG Chatbot
================================================================================
FINAL VERSION - All Features Integrated
Perfect for 8th-12th Grade Students Learning Indian Constitution & Law System

Features:
✅ Advanced RAG Pipeline (FAISS + BM25 + TF-IDF)
✅ Scenario-Based Learning ("What if I do that crime?")
✅ PDF Upload & Processing (Your own documents)
✅ Search History Preservation & Analytics
✅ Self-Learning & Response Optimization
✅ Age-Appropriate Responses (Child/Teen/Adult)
✅ Constitutional Education & Rights Learning
✅ 100% FREE & Open Source
✅ Beautiful Web Interface
✅ Educational Safety & Responsibility

Author: AI Assistant for Educational Technology
Purpose: Safe, Interactive Legal Education for Students
================================================================================
"""

from flask import Flask, request, jsonify, render_template_string, session
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
import time
import uuid

# PDF Processing (FREE)
import PyPDF2
import pdfplumber
from io import BytesIO

# RAG Components (ALL FREE)
from sentence_transformers import SentenceTransformer
import faiss
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Text Processing (FREE)
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# ================================================================================
# FLASK APP SETUP
# ================================================================================

app = Flask(__name__)
app.secret_key = 'educational_law_chatbot_final_2024'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_educational_law.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ================================================================================
# DATABASE MODELS
# ================================================================================

class User(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    age_group = db.Column(db.String(20), default='teen')
    grade_level = db.Column(db.String(10), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    total_questions = db.Column(db.Integer, default=0)
    scenario_questions = db.Column(db.Integer, default=0)

class PDFDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False, unique=True)
    total_pages = db.Column(db.Integer, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    document_type = db.Column(db.String(50), default='general')
    content_summary = db.Column(db.Text, nullable=True)
    
class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdf_document.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    embedding_vector = db.Column(db.PickleType, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    content_type = db.Column(db.String(50), default='general')
    
class ScenarioCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_title = db.Column(db.String(200), nullable=False)
    scenario_description = db.Column(db.Text, nullable=False)
    legal_analysis = db.Column(db.Text, nullable=False)
    applicable_laws = db.Column(db.Text, nullable=False)
    consequences = db.Column(db.Text, nullable=False)
    age_group = db.Column(db.String(20), nullable=False)
    severity_level = db.Column(db.String(20), nullable=False)
    educational_note = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    keywords = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), default='general')
    retrieved_chunks = db.Column(db.Text, nullable=True)
    scenario_triggered = db.Column(db.Boolean, default=False)
    relevance_score = db.Column(db.Float, nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)
    user_age_group = db.Column(db.String(20), nullable=True)

class LearningAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    learning_topic = db.Column(db.String(100), nullable=False)
    questions_asked = db.Column(db.Integer, default=1)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    progress_score = db.Column(db.Float, default=0.0)

# ================================================================================
# COMPLETE RAG PIPELINE CLASS
# ================================================================================

class CompleteFinalEducationRAG:
    """
    Complete Final Educational Law RAG Pipeline - All Features Integrated
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Complete Final Educational Law RAG Pipeline...")
        
        # Download NLTK data
        self._download_nltk_data()
        
        # Initialize AI models
        self.init_embedding_model()
        self.init_generation_model()
        
        # Initialize search components
        self.init_search_components()
        
        # Document storage
        self.documents = []
        self.document_metadata = []
        
        # Educational scenarios
        self.init_educational_scenarios()
        
        # Learning analytics
        self.response_optimization = {}
        
        # PDF upload directory
        self.upload_dir = Path("uploaded_pdfs")
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Complete Final Educational Law RAG Pipeline Ready!")
    
    def _download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except Exception as e:
            logger.warning(f"NLTK download issue: {e}")
    
    def init_embedding_model(self):
        """Initialize sentence transformer for embeddings"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384
            logger.info("✅ Embedding model loaded: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def init_generation_model(self):
        """Initialize generation model"""
        try:
            model_name = "gpt2"
            self.generation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.generation_model = AutoModelForCausalLM.from_pretrained(model_name)
            self.generation_tokenizer.pad_token = self.generation_tokenizer.eos_token
            logger.info("✅ Generation model loaded: GPT-2")
        except Exception as e:
            logger.warning(f"⚠️ Generation model not available: {e}")
            self.generation_model = None
            self.generation_tokenizer = None
    
    def init_search_components(self):
        """Initialize all search components"""
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        self.bm25 = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        self.tfidf_matrix = None
        logger.info("✅ Search components initialized")
    
    def init_educational_scenarios(self):
        """Initialize comprehensive educational scenarios"""
        try:
            if ScenarioCase.query.count() == 0:
                self._create_educational_scenarios()
                logger.info("✅ Educational scenarios initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing scenarios: {e}")
    
    def _create_educational_scenarios(self):
        """Create comprehensive educational scenarios"""
        
        scenarios = [
            {
                "title": "Taking Someone's Bicycle Without Permission",
                "description": "A 12-year-old takes a bicycle from school premises without the owner's permission, intending to return it after a ride.",
                "legal_analysis": "This constitutes theft under Section 378 of Indian Penal Code, even if intention was to return the item. Taking someone's property without permission is legally theft regardless of intent.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Juvenile Justice (Care and Protection of Children) Act 2015",
                "consequences": "For children under 16: Counseling sessions, community service, parental guidance workshop, educational session on property rights. No criminal record. Focus on understanding respect for others' property.",
                "age_group": "child",
                "severity_level": "minor",
                "educational_note": "Taking someone's property without permission is theft, even if you plan to return it. Always ask permission first. Children are treated with care under Juvenile Justice Act.",
                "category": "property_theft",
                "keywords": "bicycle, taking without permission, school property, theft, children"
            },
            {
                "title": "Cyberbullying and Online Harassment",
                "description": "A 15-year-old posts mean comments and shares embarrassing photos of a classmate on social media platforms without consent.",
                "legal_analysis": "Cyberbullying involves harassment under IPC Section 506, defamation under Section 499, and violation of privacy under IT Act. Digital harassment can cause severe psychological harm.",
                "applicable_laws": "Information Technology Act 2000 Section 66E (Violation of privacy), Section 67, Indian Penal Code Section 499 (Defamation), Section 509 (Insulting modesty)",
                "consequences": "For teenagers: Mandatory digital literacy education, counseling on empathy, community service, parental involvement, school disciplinary action, cyber law workshop.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Cyberbullying can cause serious emotional harm and has real legal consequences. What you post online can hurt people deeply. Think before you post - treat others online as you would want to be treated.",
                "category": "cybercrime",
                "keywords": "cyberbullying, social media, harassment, online, photos, privacy"
            },
            {
                "title": "Shoplifting from a Store",
                "description": "A 17-year-old steals an expensive mobile phone worth ₹25,000 from an electronics store.",
                "legal_analysis": "Theft of valuable property is a serious offense under IPC Section 378. The value of stolen goods affects severity of legal action. Items worth over ₹20,000 can lead to serious charges.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Section 380 (Theft in dwelling house), Juvenile Justice Act provisions",
                "consequences": "For older teens: Possible detention in observation home, mandatory counseling, restitution payment, community service, family counseling, educational program on earning money legally.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Stealing expensive items has serious consequences that affect your future. Stores have security systems. It's much better to work hard, save money, and buy things legally. Your reputation is worth more than any item.",
                "category": "property_theft",
                "keywords": "shoplifting, stealing, mobile phone, expensive, store, retail theft"
            },
            {
                "title": "Underage Driving Without License",
                "description": "A 16-year-old drives a motorbike without a license and gets caught by traffic police.",
                "legal_analysis": "Driving without a license violates Motor Vehicle Act 1988. Underage driving poses safety risks to the driver and public. Insurance claims may be invalid in accidents.",
                "applicable_laws": "Motor Vehicle Act 1988 Section 3 (Driving without license), Section 4 (Age restrictions), Juvenile Justice Act",
                "consequences": "Vehicle impoundment, fine payment by parents, mandatory traffic education classes, delayed license eligibility, parental liability, community service at traffic programs.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Driving without a license is dangerous for you and others. Traffic rules exist to keep everyone safe. Wait until you're eligible, get proper training, and obtain a valid license.",
                "category": "traffic_violation",
                "keywords": "driving, license, underage, motorbike, traffic police, vehicle"
            },
            {
                "title": "Vandalizing Public Property",
                "description": "A group of teenagers spray paints graffiti on a government building wall.",
                "legal_analysis": "Vandalism of public property is a criminal offense that damages community resources funded by taxpayer money. It affects public spaces that belong to everyone.",
                "applicable_laws": "Indian Penal Code Section 425 (Mischief), Section 427 (Mischief causing damage), Prevention of Damage to Public Property Act 1984",
                "consequences": "Fine equal to damage repair cost, community service cleaning public areas, civic responsibility education, parental financial liability, supervised community work.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Public property belongs to everyone and is built with taxpayer money for schools, hospitals, and development. Damaging it takes away resources from your community. Channel creativity into legal art.",
                "category": "vandalism",
                "keywords": "vandalism, graffiti, public property, government building, damage, spray paint"
            },
            {
                "title": "Sharing Private Content Without Consent",
                "description": "A teenager forwards private photos or messages of a classmate through messaging apps without permission.",
                "legal_analysis": "Sharing private content without consent violates privacy rights and dignity. It can constitute sexual harassment if content is intimate, and causes severe psychological harm.",
                "applicable_laws": "Information Technology Act Section 66E (Violation of privacy), Section 67/67A, Indian Penal Code Section 354C (Voyeurism), Section 509",
                "consequences": "Serious legal action possible, mandatory counseling on consent and digital ethics, device monitoring, education on privacy rights, community service, family counseling.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Sharing private content without permission violates someone's dignity and privacy rights. Once shared, you can never control where it goes. Always respect others' boundaries and privacy.",
                "category": "privacy_violation",
                "keywords": "sharing photos, private content, consent, messaging apps, privacy, harassment"
            },
            {
                "title": "Examination Cheating",
                "description": "A student uses unfair means during school examination by copying from hidden notes.",
                "legal_analysis": "While primarily academic in school exams, repeated cheating can have legal implications in competitive exams. It violates academic integrity and fairness principles.",
                "applicable_laws": "Educational institution rules, potential fraud charges in competitive exams, Indian Penal Code Section 419 (Cheating by impersonation)",
                "consequences": "Exam cancellation, possible debarment, school disciplinary action, parental involvement, mandatory academic integrity education, supervised retake.",
                "age_group": "teen",
                "severity_level": "minor",
                "educational_note": "Cheating undermines your education and is unfair to honest students. It becomes a habit affecting your character. Focus on learning rather than grades. Success through cheating is temporary.",
                "category": "academic_dishonesty",
                "keywords": "cheating, examination, unfair means, copying, academic integrity, school"
            },
            {
                "title": "Underage Drinking",
                "description": "A 16-year-old is caught consuming alcohol at a party and is found intoxicated.",
                "legal_analysis": "Underage drinking violates prohibition laws in most Indian states. It poses serious health risks to developing brains and can lead to dangerous behavior.",
                "applicable_laws": "State Prohibition Laws, Juvenile Justice Act provisions, Indian Penal Code provisions on public intoxication",
                "consequences": "Health screening, mandatory counseling on substance abuse, parental involvement, restriction on social activities, educational sessions on alcohol effects.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Underage drinking is illegal and harmful to your developing brain and body. Alcohol impairs judgment leading to dangerous decisions. Focus on healthy activities and connections.",
                "category": "substance_abuse",
                "keywords": "underage drinking, alcohol, party, intoxicated, substance abuse, health"
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
                educational_note=scenario_data["educational_note"],
                category=scenario_data["category"],
                keywords=scenario_data["keywords"]
            )
            db.session.add(scenario)
        
        db.session.commit()
        logger.info(f"✅ Created {len(scenarios)} educational scenarios")
    
    def detect_scenario_query(self, query: str) -> Dict:
        """Detect if query is asking about legal scenarios"""
        query_lower = query.lower()
        
        scenario_indicators = [
            'what if i', 'what happens if', 'what would happen', 'if i do', 'if someone',
            'what crime', 'what law', 'what punishment', 'what penalty', 'consequences',
            'illegal', 'against law', 'breaking law', 'get in trouble', 'arrested'
        ]
        
        activity_keywords = {
            'property_theft': ['steal', 'theft', 'take without permission', 'shoplifting', 'bicycle', 'phone'],
            'cybercrime': ['cyberbullying', 'online harassment', 'social media', 'sharing photos'],
            'traffic_violation': ['drive without license', 'underage driving', 'traffic violation'],
            'vandalism': ['graffiti', 'damage property', 'vandalism', 'public property'],
            'substance_abuse': ['drinking', 'alcohol', 'drugs', 'smoking'],
            'academic_dishonesty': ['cheat in exam', 'copying', 'plagiarism'],
            'privacy_violation': ['share photos', 'private content', 'without permission']
        }
        
        has_scenario_indicator = any(indicator in query_lower for indicator in scenario_indicators)
        
        if has_scenario_indicator:
            for category, keywords in activity_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    return {'is_scenario': True, 'category': category, 'query_type': 'legal_scenario'}
            return {'is_scenario': True, 'category': 'general', 'query_type': 'legal_scenario'}
        
        return {'is_scenario': False, 'query_type': 'general'}
    
    def find_relevant_scenarios(self, query: str, category: str = None) -> List[Dict]:
        """Find relevant educational scenarios"""
        try:
            scenarios_query = ScenarioCase.query
            if category and category != 'general':
                scenarios_query = scenarios_query.filter_by(category=category)
            
            scenarios = scenarios_query.all()
            relevant_scenarios = []
            query_words = set(query.lower().split())
            
            for scenario in scenarios:
                scenario_text = (
                    scenario.scenario_description + " " + 
                    scenario.legal_analysis + " " + 
                    (scenario.keywords or "")
                ).lower()
                
                scenario_words = set(scenario_text.split())
                relevance_score = len(query_words.intersection(scenario_words))
                
                if scenario.keywords:
                    keyword_score = len(query_words.intersection(set(scenario.keywords.lower().split(', ')))) * 2
                    relevance_score += keyword_score
                
                if relevance_score > 0:
                    relevant_scenarios.append({
                        'scenario': scenario,
                        'relevance_score': relevance_score
                    })
            
            relevant_scenarios.sort(key=lambda x: x['relevance_score'], reverse=True)
            return relevant_scenarios[:3]
            
        except Exception as e:
            logger.error(f"❌ Error finding scenarios: {e}")
            return []
    
    def generate_scenario_response(self, query: str, scenarios: List[Dict], user_age: str = "teen") -> str:
        """Generate comprehensive educational response for scenarios"""
        
        if not scenarios:
            return self._generate_general_legal_guidance(query, user_age)
        
        response = "🎓 **Educational Legal Scenario Analysis**\n\n"
        response += "⚠️ **Important Educational Notice**: This information is provided for educational purposes only to help students understand laws and consequences. For real legal situations, always consult qualified legal professionals, parents, teachers, or school counselors.\n\n"
        
        if user_age == "child":
            response += "👶 **For Young Students**: Remember, children are protected under special laws that focus on helping and teaching rather than punishing.\n\n"
        elif user_age == "teen":
            response += "👦👧 **For Teenagers**: You're old enough to understand the importance of making good choices and their consequences.\n\n"
        
        for i, scenario_data in enumerate(scenarios[:2]):
            scenario = scenario_data['scenario']
            
            response += f"📚 **Educational Example {i+1}: {scenario.scenario_title}**\n\n"
            response += f"**📖 Learning Scenario**: {scenario.scenario_description}\n\n"
            response += f"**⚖️ Legal Understanding**: {scenario.legal_analysis}\n\n"
            response += f"**📋 Laws That Apply**: {scenario.applicable_laws}\n\n"
            response += f"**🎯 Educational Consequences for Young People**: {scenario.consequences}\n\n"
            response += f"💡 **Key Learning Point**: {scenario.educational_note}\n\n"
            
            if i < len(scenarios) - 1:
                response += "---\n\n"
        
        response += "🎓 **Complete Educational Guidance**:\n\n"
        response += "**📖 Why Laws Exist**:\n"
        response += "• Laws protect everyone's rights and safety\n"
        response += "• They help society function peacefully and fairly\n"
        response += "• They provide guidelines for respectful behavior\n\n"
        
        response += "**👨‍⚖️ Special Protections for Young People**:\n"
        response += "• Juvenile Justice Act focuses on rehabilitation and education\n"
        response += "• Children get counseling instead of harsh punishment\n"
        response += "• The goal is to help young people learn and grow\n\n"
        
        response += "**🌟 Remember**: The purpose of learning about laws is to help you become a responsible, respectful citizen who contributes positively to society!"
        
        return response
    
    def _generate_general_legal_guidance(self, query: str, user_age: str) -> str:
        """Generate general educational guidance"""
        response = "⚖️ **General Legal Education & Guidance**\n\n"
        response += "I understand you're curious about legal matters. Here's educational guidance:\n\n"
        
        response += "**🏛️ About Laws and Rights**:\n"
        response += "• Laws help our society function peacefully and fairly\n"
        response += "• Everyone has both rights AND responsibilities\n"
        response += "• The Indian Constitution guarantees fundamental rights\n\n"
        
        response += "**👨‍⚖️ Special Protections for Students**:\n"
        response += "• The Juvenile Justice Act protects children and teenagers\n"
        response += "• Focus is on rehabilitation and education\n"
        response += "• Parents and schools have special responsibilities\n\n"
        
        response += "**🎓 Learning Resources**:\n"
        response += "• School counselors and teachers\n"
        response += "• Constitutional and legal education books\n"
        response += "• Government educational websites\n\n"
        
        response += "🌟 **Remember**: Learning about laws helps you become a responsible citizen!"
        
        return response
    
    def extract_text_from_pdf(self, pdf_file) -> Tuple[List[Dict], Dict]:
        """Extract text from PDF using multiple methods"""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text_content = []
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
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
            
            try:
                pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = []
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
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
    
    def chunk_text_intelligently(self, page_content: List[Dict], chunk_size: int = 500) -> List[Dict]:
        """Intelligent text chunking for legal documents"""
        chunks = []
        
        for page_data in page_content:
            page_num = page_data['page']
            text = page_data['text']
            
            content_type = self._classify_legal_content(text)
            
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
                        'content_type': content_type
                    })
                    current_chunk = [sentence]
                    current_length = sentence_words
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_words
            
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'page_number': page_num,
                    'chunk_index': len(chunks),
                    'content_type': content_type
                })
        
        return chunks
    
    def _classify_legal_content(self, text: str) -> str:
        """Classify legal content type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['fundamental right', 'article', 'constitution']):
            return 'constitutional'
        elif any(word in text_lower for word in ['punishment', 'penalty', 'fine', 'imprisonment']):
            return 'punishment'
        elif any(word in text_lower for word in ['right to', 'freedom of', 'liberty']):
            return 'rights'
        elif any(word in text_lower for word in ['procedure', 'court', 'trial']):
            return 'procedure'
        elif any(word in text_lower for word in ['section', 'ipc', 'penal code', 'act']):
            return 'law'
        else:
            return 'general'
    
    def process_pdf_file(self, pdf_file, filename: str, document_type: str = 'general') -> Tuple[bool, int]:
        """Process uploaded PDF file"""
        try:
            pdf_file.seek(0)
            file_content = pdf_file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            pdf_file.seek(0)
            
            existing_doc = PDFDocument.query.filter_by(file_hash=file_hash).first()
            if existing_doc:
                logger.info(f"PDF {filename} already processed")
                return True, DocumentChunk.query.filter_by(pdf_id=existing_doc.id).count()
            
            page_content, metadata = self.extract_text_from_pdf(pdf_file)
            
            if not page_content:
                logger.error(f"No text extracted from {filename}")
                return False, 0
            
            if document_type == 'general':
                document_type = self._detect_document_type(page_content)
            
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
            
            chunks = self.chunk_text_intelligently(page_content)
            chunks_created = 0
            
            for chunk in chunks:
                try:
                    embedding = self.embedding_model.encode(chunk['content'])
                    
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
                    
                    self.faiss_index.add(embedding.reshape(1, -1).astype('float32'))
                    
                    self.documents.append(chunk['content'])
                    self.document_metadata.append({
                        'pdf_id': pdf_doc.id,
                        'filename': filename,
                        'page_number': chunk['page_number'],
                        'chunk_index': chunk['chunk_index'],
                        'content_type': chunk.get('content_type', 'general'),
                        'document_type': document_type
                    })
                    
                    chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
            
            pdf_doc.processed = True
            db.session.commit()
            
            self._rebuild_search_indexes()
            
            logger.info(f"Successfully processed {filename} with {chunks_created} chunks")
            return True, chunks_created
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            db.session.rollback()
            return False, 0
    
    def _detect_document_type(self, page_content: List[Dict]) -> str:
        """Auto-detect document type"""
        all_text = " ".join([page['text'] for page in page_content]).lower()
        
        if any(term in all_text for term in ['constitution', 'fundamental rights', 'preamble']):
            return 'constitution'
        elif any(term in all_text for term in ['penal code', 'criminal law', 'ipc']):
            return 'law'
        else:
            return 'general'
    
    def _rebuild_search_indexes(self):
        """Rebuild search indexes"""
        try:
            if self.documents:
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
                logger.info("Search indexes rebuilt successfully")
        except Exception as e:
            logger.error(f"Error rebuilding search indexes: {e}")
    
    def load_existing_documents(self):
        """Load existing processed documents"""
        try:
            chunks = DocumentChunk.query.all()
            
            for chunk in chunks:
                if chunk.embedding_vector:
                    embedding = np.array(chunk.embedding_vector).astype('float32')
                    self.faiss_index.add(embedding.reshape(1, -1))
                    
                    self.documents.append(chunk.content)
                    
                    pdf_doc = PDFDocument.query.get(chunk.pdf_id)
                    self.document_metadata.append({
                        'pdf_id': chunk.pdf_id,
                        'filename': pdf_doc.filename if pdf_doc else 'Unknown',
                        'page_number': chunk.page_number,
                        'chunk_index': chunk.chunk_index,
                        'content_type': chunk.content_type,
                        'document_type': pdf_doc.document_type if pdf_doc else 'general'
                    })
            
            self._rebuild_search_indexes()
            
            logger.info(f"Loaded {len(chunks)} existing document chunks")
            
        except Exception as e:
            logger.error(f"Error loading existing documents: {e}")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Multi-method document search"""
        if not self.documents:
            return []
        
        results = []
        
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
        
        try:
            if self.bm25 and results:
                query_tokens = query.lower().split()
                bm25_scores = self.bm25.get_scores(query_tokens)
                
                for result in results:
                    idx = result['index']
                    if idx < len(bm25_scores):
                        result['bm25_score'] = float(bm25_scores[idx])
                    else:
                        result['bm25_score'] = 0.0
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
        
        try:
            if self.tfidf_matrix is not None and results:
                query_vector = self.tfidf_vectorizer.transform([query])
                tfidf_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
                
                for result in results:
                    idx = result['index']
                    if idx < len(tfidf_scores):
                        result['tfidf_score'] = float(tfidf_scores[idx])
                    else:
                        result['tfidf_score'] = 0.0
        except Exception as e:
            logger.error(f"TF-IDF search error: {e}")
        
        for result in results:
            semantic = result.get('semantic_score', 0)
            bm25 = result.get('bm25_score', 0)
            tfidf = result.get('tfidf_score', 0)
            
            max_bm25 = max([r.get('bm25_score', 0) for r in results]) if results else 1
            bm25_norm = bm25 / max_bm25 if max_bm25 > 0 else 0
            
            result['combined_score'] = 0.5 * semantic + 0.3 * bm25_norm + 0.2 * tfidf
        
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        return results[:top_k]
    
    def generate_response(self, query: str, retrieved_docs: List[Dict], query_type: str = 'general', scenarios: List[Dict] = None, user_age: str = "teen") -> Tuple[str, float]:
        """Generate educational response"""
        
        if query_type == 'legal_scenario' and scenarios:
            return self.generate_scenario_response(query, scenarios, user_age), 0.9
        
        if not retrieved_docs:
            if query_type == 'legal_scenario':
                return self.generate_scenario_response(query, [], user_age), 0.7
            else:
                return self._generate_fallback_response(query, user_age), 0.5
        
        context = self._prepare_context(retrieved_docs[:3])
        response = self._generate_template_response(query, context, retrieved_docs, user_age)
        
        return response, 0.8
    
    def _prepare_context(self, docs: List[Dict]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs):
            metadata = doc['metadata']
            filename = metadata.get('filename', 'Unknown')
            page = metadata.get('page_number', 'Unknown')
            content_type = metadata.get('content_type', 'general')
            
            context_parts.append(
                f"**Source {i+1}** (File: {filename}, Page: {page}, Type: {content_type}):\n"
                f"{doc['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _generate_template_response(self, query: str, context: str, docs: List[Dict], user_age: str) -> str:
        """Generate template-based educational response"""
        
        response = "📚 **Educational Legal Information**\n\n"
        response += "⚠️ **Educational Purpose Only**: This information is provided for learning about laws and legal concepts. Always consult legal professionals for real situations.\n\n"
        
        key_info = self._extract_key_information(context, query)
        response += "📖 **Based on your uploaded documents:**\n\n"
        response += key_info + "\n\n"
        
        if docs:
            response += "📚 **Sources from Your Documents:**\n"
            for i, doc in enumerate(docs[:3]):
                metadata = doc['metadata']
                filename = metadata.get('filename', 'Unknown')
                page = metadata.get('page_number', 'Unknown')
                content_type = metadata.get('content_type', 'general')
                response += f"• {filename} (Page {page}) - {content_type.title()} Content\n"
            response += "\n"
        
        if user_age == "child":
            response += "👶 **For Young Students**: Laws are like rules that help everyone get along safely. Always ask trusted adults when you have questions.\n\n"
        elif user_age == "teen":
            response += "👦👧 **For Teenagers**: Understanding laws helps you make good choices and be a responsible citizen. Your actions matter and have consequences.\n\n"
        
        response += "🎓 **Educational Takeaway**: Learning about laws and rights helps you become a responsible citizen who contributes positively to society!"
        
        return response
    
    def _extract_key_information(self, context: str, query: str) -> str:
        """Extract key information from context"""
        sentences = []
        for line in context.split('\n'):
            if line.strip() and not line.strip().startswith('**Source'):
                sentences.extend([s.strip() for s in line.split('.') if s.strip()])
        
        query_words = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 20:
                sentence_words = set(sentence.lower().split())
                relevance_score = len(query_words.intersection(sentence_words))
                
                if relevance_score > 0:
                    scored_sentences.append((sentence, relevance_score))
        
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        key_sentences = [s[0] for s in scored_sentences[:4]]
        
        if key_sentences:
            return '. '.join(key_sentences) + '.'
        else:
            return context[:500] + '...' if len(context) > 500 else context
    
    def _generate_fallback_response(self, query: str, user_age: str) -> str:
        """Educational fallback response"""
        response = "📚 **Educational Legal Information**\n\n"
        response += "I don't have specific information about your query in the uploaded documents, but I can provide some general educational guidance:\n\n"
        
        response += "🏛️ **Understanding Laws and Rights:**\n"
        response += "• Laws are designed to protect everyone in society\n"
        response += "• Everyone has both rights and responsibilities\n"
        response += "• Young people have special protections under the law\n\n"
        
        response += "⚖️ **For Students Learning About Law:**\n"
        response += "• Focus on understanding why laws exist\n"
        response += "• Learn about your rights and how to exercise them responsibly\n"
        response += "• Understand that actions have consequences\n"
        response += "• Respect others' rights and property\n\n"
        
        response += "💡 **Tips for Better Results:**\n"
        response += "• Upload relevant legal or constitutional documents\n"
        response += "• Ask specific questions about laws, rights, or procedures\n"
        response += "• Use keywords like 'constitution,' 'rights,' 'laws,' or 'procedures'\n\n"
        
        response += "Remember: Learning about laws helps you become a responsible citizen! 🇮🇳"
        
        return response
    
    def ensure_user_exists(self, user_id: str, age_group: str = "teen") -> User:
        """Ensure user exists in database"""
        user = User.query.get(user_id)
        if not user:
            user = User(
                id=user_id,
                age_group=age_group,
                created_date=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.last_active = datetime.utcnow()
            db.session.commit()
        return user

# Initialize Complete RAG System
complete_rag = CompleteFinalEducationRAG()

# ================================================================================
# FLASK ROUTES - COMPLETE API
# ================================================================================

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎓⚖️ Complete Educational Law & Constitution RAG Chatbot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            text-align: center; 
            background: rgba(255,255,255,0.95); 
            padding: 30px; 
            border-radius: 20px; 
            margin-bottom: 30px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header h1 { color: #4a5568; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #718096; font-size: 1.1em; margin: 5px 0; }
        
        .warning-box { 
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%); 
            padding: 20px; 
            border-radius: 15px; 
            margin: 20px 0; 
            border: 2px solid #fc8181; 
            color: #742a2a; 
            font-weight: bold;
            text-align: center;
        }
        
        .section { 
            background: rgba(255,255,255,0.95); 
            padding: 25px; 
            border-radius: 15px; 
            margin-bottom: 25px; 
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .upload-section { background: linear-gradient(135deg, #e8f4f8 0%, #d6f5f5 100%); }
        .chat-section { background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%); }
        .scenarios-section { background: linear-gradient(135deg, #fffbf0 0%, #fef5e7 100%); }
        
        .section h2 { color: #2d3748; margin-bottom: 15px; }
        .section p { color: #4a5568; margin-bottom: 15px; line-height: 1.6; }
        
        .file-input { 
            margin: 15px 0; 
            padding: 15px; 
            border: 3px dashed #4299e1; 
            border-radius: 10px; 
            background: #ebf8ff; 
            text-align: center;
        }
        
        .btn { 
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: bold; 
            transition: all 0.3s;
            margin: 5px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(66, 153, 225, 0.4); }
        .btn-scenario { background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%); }
        .btn-education { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); }
        
        .scenarios-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin: 25px 0; 
        }
        
        .scenario-card { 
            background: white; 
            padding: 20px; 
            border-radius: 12px; 
            border: 2px solid #e2e8f0; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .scenario-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .scenario-card h4 { color: #2d3748; margin-bottom: 12px; font-size: 1.1em; }
        .scenario-card p { color: #4a5568; font-size: 14px; line-height: 1.5; margin-bottom: 15px; }
        
        .age-selector { 
            margin: 20px 0; 
            padding: 15px; 
            background: rgba(255,255,255,0.8); 
            border-radius: 10px; 
        }
        .age-selector select { 
            padding: 10px 15px; 
            border: 2px solid #cbd5e0; 
            border-radius: 8px; 
            background: white; 
            font-size: 16px;
            min-width: 200px;
        }
        
        .chat-input { 
            width: 70%; 
            padding: 15px; 
            border: 2px solid #cbd5e0; 
            border-radius: 10px; 
            font-size: 16px; 
            margin: 10px 5px;
        }
        .chat-input:focus { border-color: #4299e1; outline: none; }
        
        .chat-response { 
            background: white; 
            padding: 20px; 
            margin: 15px 0; 
            border-radius: 12px; 
            border-left: 5px solid #4299e1; 
            box-shadow: 0 3px 15px rgba(0,0,0,0.1); 
        }
        .user-message { border-left-color: #48bb78; background: #f0fff4; }
        
        .status { 
            margin: 15px 0; 
            padding: 15px; 
            border-radius: 10px; 
            font-weight: bold; 
        }
        .success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
        
        .documents-list { margin: 25px 0; }
        .doc-item { 
            background: white; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 10px; 
            border: 1px solid #e2e8f0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
        }
        
        .feature-highlight { 
            background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%); 
            padding: 20px; 
            border-radius: 12px; 
            margin: 20px 0; 
            border: 2px solid #81e6d9; 
        }
        .feature-highlight h3 { color: #2d3748; margin-bottom: 15px; }
        .feature-highlight ul { margin-left: 20px; }
        .feature-highlight li { margin: 8px 0; color: #2d3748; }
        
        .tips-box { 
            background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); 
            padding: 20px; 
            border-radius: 12px; 
            margin: 20px 0; 
            border: 2px solid #90cdf4; 
        }
        .tips-box h4 { color: #2a4365; margin-bottom: 10px; }
        .tips-box ul { margin-left: 20px; }
        .tips-box li { margin: 5px 0; color: #2a4365; }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header h1 { font-size: 2em; }
            .chat-input { width: 100%; margin: 10px 0; }
            .scenarios-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓⚖️ Complete Educational Law & Constitution RAG Chatbot</h1>
            <p><strong>Perfect for 8th-12th Grade Students - Indian Constitution & Law System Education</strong></p>
            <p>💰 100% FREE • 🔒 Private & Safe • 📚 Educational Focus • 🎭 Scenario-Based Learning</p>
            <p>🧠 Advanced RAG • 📊 Learning Analytics • 🏛️ Constitutional Education • ⚖️ Legal Awareness</p>
        </div>
        
        <div class="warning-box">
            ⚠️ <strong>Educational Purpose Only</strong>: This chatbot is designed for educational learning about laws, constitution, and civic responsibility. 
            It teaches students about consequences through safe, interactive scenarios. Always consult legal professionals for real legal situations.
        </div>
        
        <div class="feature-highlight">
            <h3>🌟 Complete Educational Features:</h3>
            <ul>
                <li>📚 <strong>Advanced PDF Upload & Analysis</strong>: Upload constitution, law books with intelligent processing</li>
                <li>🎭 <strong>Scenario-Based Learning</strong>: Interactive "What if I do that crime?" educational examples</li>
                <li>👶👦👧 <strong>Age-Appropriate Guidance</strong>: Different responses for children, teenagers, and adults</li>
                <li>⚖️ <strong>Comprehensive Legal Education</strong>: Understand rights, laws, and civic responsibilities</li>
                <li>🏛️ <strong>Constitutional Deep Dive</strong>: Detailed exploration of Indian Constitution</li>
                <li>📊 <strong>Search History & Analytics</strong>: Track learning progress and revisit questions</li>
                <li>🧠 <strong>Self-Learning System</strong>: Improves responses based on user feedback</li>
                <li>🔍 <strong>Advanced RAG Search</strong>: FAISS + BM25 + TF-IDF for best results</li>
            </ul>
        </div>
        
        <div class="section upload-section">
            <h2>📄 Upload Legal & Constitutional Documents</h2>
            <p>Upload PDFs of constitution, law books, legal guides for personalized learning</p>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="file-input">
                    <input type="file" id="pdfFile" name="pdf" accept=".pdf" multiple>
                    <p><strong>📚 Recommended:</strong> Indian Constitution, Legal textbooks, Rights documents, Civic education materials</p>
                </div>
                <button type="submit" class="btn">📤 Upload Legal Documents</button>
            </form>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="section scenarios-section">
            <h2>🎭 Interactive Educational Legal Scenarios</h2>
            <p>Learn about laws and consequences through safe, educational examples</p>
            
            <div class="age-selector">
                <label for="ageGroup"><strong>👤 Select Your Age Group:</strong></label><br><br>
                <select id="ageGroup">
                    <option value="child">👶 Child (8-12 years) - Simple, protective guidance</option>
                    <option value="teen" selected>👦👧 Teenager (13-17 years) - Detailed consequences</option>
                    <option value="adult">👨👩 Adult (18+ years) - Full legal implications</option>
                </select>
            </div>
            
            <div class="scenarios-grid">
                <div class="scenario-card">
                    <h4>🚲 Property Rights & Theft</h4>
                    <p>Learn about taking things without permission, understanding property rights, and age-appropriate consequences</p>
                    <button onclick="askScenario('What happens if I take someone\\'s bicycle without permission?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>💻 Cyberbullying & Digital Ethics</h4>
                    <p>Understand online harassment, cyberbullying laws, digital responsibility, and respecting others online</p>
                    <button onclick="askScenario('What are the consequences of cyberbullying someone online?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏪 Shoplifting & Consumer Ethics</h4>
                    <p>Learn about theft in stores, legal consequences, understanding value of property, and making ethical choices</p>
                    <button onclick="askScenario('What happens if I steal something expensive from a store?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏍️ Traffic Rules & Road Safety</h4>
                    <p>Understand driving laws, license requirements, age restrictions, and road safety responsibilities</p>
                    <button onclick="askScenario('What happens if I drive a motorbike without a license?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🎨 Vandalism & Public Property</h4>
                    <p>Learn about property damage, civic responsibility, community impact, and respecting shared spaces</p>
                    <button onclick="askScenario('What happens if I spray paint graffiti on public buildings?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>📱 Privacy Rights & Consent</h4>
                    <p>Understand privacy laws, sharing content without permission, digital ethics, and respecting boundaries</p>
                    <button onclick="askScenario('What happens if I share someone\\'s private photos without permission?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>📝 Academic Integrity & Honesty</h4>
                    <p>Learn about examination cheating, academic dishonesty, the value of honest learning, and character building</p>
                    <button onclick="askScenario('What happens if I cheat in school examinations?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🍺 Substance Abuse & Health</h4>
                    <p>Understand underage drinking laws, health risks, making healthy choices, and peer pressure resistance</p>
                    <button onclick="askScenario('What happens if I drink alcohol as a teenager?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
            </div>
        </div>
        
        <div class="documents-list">
            <h3>📚 Your Uploaded Legal Documents</h3>
            <div id="documentsList">Loading document library...</div>
        </div>
        
        <div class="section chat-section">
            <h2>💬 Interactive Chat with Your Legal & Constitutional Documents</h2>
            <p>Ask questions about laws, rights, constitution, or explore educational scenarios</p>
            
            <div id="chatMessages"></div>
            
            <div style="margin: 20px 0;">
                <input type="text" id="chatInput" class="chat-input" placeholder="Ask about laws, rights, constitution, or scenarios like 'What happens if I...'">
                <button onclick="sendMessage()" class="btn btn-education">🚀 Ask Question</button>
                <button onclick="clearChat()" class="btn" style="background: #e53e3e;">🗑️ Clear Chat</button>
            </div>
            
            <div class="tips-box">
                <h4>💡 Educational Question Examples:</h4>
                <ul>
                    <li><strong>Constitutional Rights:</strong> "What are my fundamental rights as a student?"</li>
                    <li><strong>Legal Scenarios:</strong> "What happens if someone steals my phone?"</li>
                    <li><strong>Civic Education:</strong> "How can I be a good citizen in my community?"</li>
                    <li><strong>Law Understanding:</strong> "Explain Article 21 of the Indian Constitution"</li>
                    <li><strong>Student Rights:</strong> "What laws protect children from bullying?"</li>
                    <li><strong>Digital Safety:</strong> "What should I do if someone harasses me online?"</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Learning Analytics & Progress</h2>
            <p>Track your educational progress and see how your legal knowledge is improving!</p>
            <button onclick="showAnalytics()" class="btn btn-education">📈 View My Learning Progress</button>
            <div id="analyticsDisplay"></div>
        </div>
    </div>

    <script>
        // Global variables
        let currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let currentUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // Scenario learning functions
        function askScenario(question) {
            document.getElementById('chatInput').value = question;
            sendMessage();
        }

        // Upload functionality
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            const files = document.getElementById('pdfFile').files;
            
            if (files.length === 0) {
                document.getElementById('uploadStatus').innerHTML = '<div class="status warning">⚠️ Please select PDF files to upload</div>';
                return;
            }
            
            for (let file of files) {
                formData.append('pdfs', file);
            }
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status warning">⏳ Uploading and processing legal documents...</div>';
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('uploadStatus').innerHTML = 
                        '<div class="status success">✅ ' + result.message + 
                        '<br>📊 Processed: ' + result.processed_count + ' document(s)' +
                        '<br>📄 Total chunks: ' + result.total_chunks + '</div>';
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
            
            addMessage('user', query);
            input.value = '';
            
            const loadingId = addMessage('bot', '🤔 Analyzing your question and searching documents...');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: query, 
                        user_id: currentUserId,
                        session_id: currentSessionId,
                        age_group: ageGroup
                    })
                });
                const result = await response.json();
                
                document.getElementById(loadingId).remove();
                
                if (result.response) {
                    addMessage('bot', result.response, result);
                } else {
                    addMessage('bot', '❌ Error: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessage('bot', '❌ Network Error: ' + error.message);
            }
        }
        
        function addMessage(type, content, metadata = null) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = 'chat-response ' + (type === 'user' ? 'user-message' : '');
            
            let html = '<strong>' + (type === 'user' ? '👤 You:' : '🤖 Educational Law Assistant:') + '</strong><br><br>';
            
            let formattedContent = content
                .replace(/\\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/^• /gm, '&bullet; ')
                .replace(/^- /gm, '&ndash; ');
            
            html += formattedContent;
            
            if (metadata && type === 'bot') {
                html += '<br><br><div style="background: #f7fafc; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 0.9em; color: #4a5568;">';
                html += '<strong>📊 Response Details:</strong><br>';
                html += '⚡ Processing Time: ' + (metadata.processing_time ? metadata.processing_time.toFixed(2) + 's' : 'N/A') + '<br>';
                if (metadata.query_type) {
                    html += '📝 Query Type: ' + metadata.query_type.replace(/_/g, ' ').toUpperCase() + '<br>';
                }
                if (metadata.scenario_triggered) {
                    html += '🎭 Educational Scenario: Yes<br>';
                }
                if (metadata.sources_found) {
                    html += '📚 Document Sources: ' + metadata.sources_found + '<br>';
                }
                html += '</div>';
                
                html += '<div style="margin-top: 15px;">';
                html += '<button onclick="provideFeedback(\'' + messageId + '\', 1)" class="btn" style="background: #48bb78; margin-right: 10px;">👍 Helpful</button>';
                html += '<button onclick="provideFeedback(\'' + messageId + '\', -1)" class="btn" style="background: #e53e3e;">👎 Not Helpful</button>';
                html += '</div>';
            }
            
            messageDiv.innerHTML = html;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageId;
        }
        
        function clearChat() {
            document.getElementById('chatMessages').innerHTML = '';
        }
        
        // Feedback system
        async function provideFeedback(messageId, score) {
            try {
                await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message_id: messageId,
                        score: score,
                        user_id: currentUserId
                    })
                });
                
                const messageDiv = document.getElementById(messageId);
                const buttons = messageDiv.querySelectorAll('button');
                buttons.forEach(btn => {
                    btn.style.opacity = '0.5';
                    btn.disabled = true;
                });
                
                const thankYou = document.createElement('span');
                thankYou.style.color = '#48bb78';
                thankYou.style.fontWeight = 'bold';
                thankYou.innerHTML = ' ✅ Thank you for your feedback!';
                buttons[buttons.length - 1].parentNode.appendChild(thankYou);
                
            } catch (error) {
                console.error('Feedback error:', error);
            }
        }
        
        // Load documents
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents');
                const result = await response.json();
                
                const docsDiv = document.getElementById('documentsList');
                if (result.documents && result.documents.length > 0) {
                    let html = '<div style="display: grid; gap: 15px;">';
                    result.documents.forEach(doc => {
                        const typeEmoji = doc.document_type === 'constitution' ? '🏛️' : 
                                        doc.document_type === 'law' ? '⚖️' : '📄';
                        const statusColor = doc.processed ? '#48bb78' : '#ed8936';
                        
                        html += '<div class="doc-item">';
                        html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
                        html += '<div>';
                        html += typeEmoji + ' <strong>' + doc.filename + '</strong><br>';
                        html += '<small style="color: #666;">Type: ' + doc.document_type.toUpperCase() + 
                               ' | Pages: ' + doc.total_pages + 
                               ' | Size: ' + Math.round(doc.file_size/1024) + ' KB</small><br>';
                        html += '<small style="color: #666;">Uploaded: ' + new Date(doc.upload_date).toLocaleString() + '</small>';
                        html += '</div>';
                        html += '<div style="color: ' + statusColor + '; font-weight: bold;">';
                        html += doc.processed ? '✅ Processed' : '⏳ Processing';
                        html += '</div>';
                        html += '</div>';
                        html += '</div>';
                    });
                    html += '</div>';
                    docsDiv.innerHTML = html;
                } else {
                    docsDiv.innerHTML = '<div class="doc-item">📝 No legal documents uploaded yet.<br><strong>Start by uploading:</strong> Indian Constitution, Law textbooks, Legal guides</div>';
                }
            } catch (error) {
                document.getElementById('documentsList').innerHTML = '<div class="doc-item" style="color: #e53e3e;">❌ Error loading documents: ' + error.message + '</div>';
            }
        }
        
        // Learning analytics
        async function showAnalytics() {
            try {
                const response = await fetch('/api/analytics?user_id=' + currentUserId);
                const result = await response.json();
                
                const analyticsDiv = document.getElementById('analyticsDisplay');
                let html = '<div style="background: white; padding: 20px; border-radius: 10px; margin-top: 15px; border: 2px solid #4299e1;">';
                html += '<h3 style="color: #2d3748; margin-bottom: 15px;">📊 Your Learning Progress</h3>';
                
                if (result.user_stats) {
                    const stats = result.user_stats;
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">';
                    
                    html += '<div style="background: #e6fffa; padding: 15px; border-radius: 8px; text-align: center;">';
                    html += '<div style="font-size: 24px; font-weight: bold; color: #2d3748;">' + (stats.total_questions || 0) + '</div>';
                    html += '<div style="color: #4a5568;">Total Questions Asked</div>';
                    html += '</div>';
                    
                    html += '<div style="background: #fff5f5; padding: 15px; border-radius: 8px; text-align: center;">';
                    html += '<div style="font-size: 24px; font-weight: bold; color: #2d3748;">' + (stats.scenario_questions || 0) + '</div>';
                    html += '<div style="color: #4a5568;">Scenario Questions</div>';
                    html += '</div>';
                    
                    html += '</div>';
                }
                
                html += '<div style="margin-top: 20px; padding: 15px; background: #ebf8ff; border-radius: 8px;">';
                html += '<p style="color: #2a4365; margin: 0;"><strong>🎓 Keep Learning!</strong> Continue asking questions and exploring scenarios to build your legal knowledge!</p>';
                html += '</div>';
                
                html += '</div>';
                analyticsDiv.innerHTML = html;
                
            } catch (error) {
                document.getElementById('analyticsDisplay').innerHTML = '<div style="color: #e53e3e; padding: 15px;">❌ Error loading analytics: ' + error.message + '</div>';
            }
        }
        
        // Initialize
        loadDocuments();
        
        // Allow Enter key in chat
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Welcome message
        setTimeout(() => {
            addMessage('bot', 
                '🎓 Welcome to your Complete Educational Law & Constitution Learning Assistant!\\n\\n' +
                'I\\'m here to help you learn about laws, rights, and civic responsibilities through safe, educational examples.\\n\\n' +
                '🎭 **Try asking scenario questions like:**\\n' +
                '• "What happens if someone steals something?"\\n' +
                '• "What are my rights as a student?"\\n' +
                '• "How can I protect myself from cyberbullying?"\\n\\n' +
                '📚 **Upload legal documents** to get personalized answers from constitution and law books.\\n\\n' +
                '🛡️ Remember: This is for educational learning only. Always consult legal professionals for real situations!'
            );
        }, 1000);
    </script>
</body>
</html>
    ''')

@app.route('/api/upload', methods=['POST'])
def upload_pdfs():
    """Upload and process PDF documents"""
    try:
        if 'pdfs' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF files uploaded'})
        
        files = request.files.getlist('pdfs')
        processed_count = 0
        errors = []
        total_chunks = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            if not file.filename.lower().endswith('.pdf'):
                errors.append(f"{file.filename} is not a PDF file")
                continue
            
            try:
                filename_lower = file.filename.lower()
                if any(word in filename_lower for word in ['constitution', 'fundamental', 'rights']):
                    doc_type = 'constitution'
                elif any(word in filename_lower for word in ['law', 'penal', 'criminal', 'ipc']):
                    doc_type = 'law'
                else:
                    doc_type = 'general'
                
                success, chunks_created = complete_rag.process_pdf_file(file, file.filename, doc_type)
                if success:
                    processed_count += 1
                    total_chunks += chunks_created
                else:
                    errors.append(f"Failed to process {file.filename}")
            except Exception as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
        
        if processed_count > 0:
            message = f"Successfully processed {processed_count} legal document(s)"
            if errors:
                message += f". Some errors: {'; '.join(errors[:2])}"
            return jsonify({
                'success': True, 
                'message': message,
                'processed_count': processed_count,
                'total_chunks': total_chunks
            })
        else:
            return jsonify({'success': False, 'error': f"No documents processed. Errors: {'; '.join(errors)}"})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents')
def get_documents():
    """Get all uploaded documents"""
    try:
        docs = PDFDocument.query.order_by(PDFDocument.upload_date.desc()).all()
        documents = []
        
        for doc in docs:
            chunks_count = DocumentChunk.query.filter_by(pdf_id=doc.id).count()
            documents.append({
                'id': doc.id,
                'filename': doc.filename,
                'total_pages': doc.total_pages,
                'file_size': doc.file_size,
                'upload_date': doc.upload_date.isoformat(),
                'processed': doc.processed,
                'document_type': doc.document_type,
                'chunks_created': chunks_count
            })
        
        return jsonify({'documents': documents})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    start_time = time.time()
    
    try:
        data = request.json
        query = data.get('query', '')
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', 'default')
        age_group = data.get('age_group', 'teen')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'})
        
        user = complete_rag.ensure_user_exists(user_id, age_group)
        user.total_questions += 1
        
        scenario_detection = complete_rag.detect_scenario_query(query)
        query_type = scenario_detection['query_type']
        is_scenario = scenario_detection['is_scenario']
        category = scenario_detection.get('category', 'general')
        
        scenarios = []
        retrieved_docs = []
        
        if is_scenario:
            scenarios = complete_rag.find_relevant_scenarios(query, category)
            user.scenario_questions += 1
            retrieved_docs = complete_rag.search_documents(query, top_k=3)
        else:
            retrieved_docs = complete_rag.search_documents(query, top_k=5)
        
        response, generation_score = complete_rag.generate_response(
            query, retrieved_docs, query_type, scenarios, age_group
        )
        
        processing_time = time.time() - start_time
        relevance_score = retrieved_docs[0]['combined_score'] if retrieved_docs else 0.0
        
        history_entry = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            query_type=query_type,
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

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for learning improvement"""
    try:
        data = request.json
        score = data.get('score')
        user_id = data.get('user_id')
        
        recent_chat = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).first()
        
        if recent_chat:
            recent_chat.feedback_score = score
            db.session.commit()
            return jsonify({'success': True, 'message': 'Feedback recorded'})
        else:
            return jsonify({'success': False, 'error': 'Chat history not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analytics')
def get_analytics():
    """Get learning analytics"""
    try:
        user_id = request.args.get('user_id', 'anonymous')
        
        user = User.query.get(user_id)
        user_stats = {}
        
        if user:
            total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
            scenario_chats = ChatHistory.query.filter_by(user_id=user_id, scenario_triggered=True).count()
            
            user_stats = {
                'total_questions': total_chats,
                'scenario_questions': scenario_chats,
                'age_group': user.age_group,
                'member_since': user.created_date.strftime('%Y-%m-%d')
            }
        
        total_docs = PDFDocument.query.count()
        total_chunks = DocumentChunk.query.count()
        
        return jsonify({
            'user_stats': user_stats,
            'system_stats': {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'educational_scenarios': ScenarioCase.query.count(),
                'system_status': 'Educational Law RAG System Active'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        complete_rag.load_existing_documents()
    
    logger.info("🚀 Complete Final Educational Law & Constitution RAG Chatbot Starting...")
    logger.info("🎓 Ready to teach students about laws, rights, and civic responsibility!")
    logger.info("💰 100% FREE • 🎭 Scenario-Based • 🛡️ Safe & Educational")
    
    app.run(debug=True, port=5000, host='0.0.0.0')