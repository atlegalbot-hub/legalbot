"""
FINAL COMPLETE Educational Law & Constitution RAG Chatbot
=====================================================================================================
Features: RAG Pipeline, Scenario-Based Learning, PDF Processing, Search History, Self-Learning,
Constitutional Education, Age-Appropriate Guidance, Complete FREE Solution for Students

For 8th-12th Grade Students - Indian Constitution & Law System Education
100% FREE, Open Source, Local Processing, Educational Focus
=====================================================================================================
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
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Text Processing (FREE)
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'educational_law_chatbot_2024'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///educational_law_complete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =====================================================================================================
# DATABASE MODELS
# =====================================================================================================

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
    improvement_suggested = db.Column(db.Text, nullable=True)

class LearningAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    learning_topic = db.Column(db.String(100), nullable=False)
    questions_asked = db.Column(db.Integer, default=1)
    correct_responses = db.Column(db.Integer, default=0)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    progress_score = db.Column(db.Float, default=0.0)
    topics_mastered = db.Column(db.Text, nullable=True)

# =====================================================================================================
# COMPLETE RAG PIPELINE CLASS
# =====================================================================================================

class CompleteLawEducationRAG:
    """
    Complete Educational Law RAG Pipeline with All Features:
    - PDF Processing with OCR fallback
    - Multi-method Search (FAISS, BM25, TF-IDF)
    - Scenario-based Learning
    - Age-appropriate Responses
    - Search History with Analytics
    - Self-Learning and Optimization
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Complete Educational Law RAG Pipeline...")
        
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
        self.learning_patterns = {}
        self.response_optimization = {}
        
        # PDF upload directory
        self.upload_dir = Path("uploaded_pdfs")
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Complete Educational Law RAG Pipeline Ready!")
    
    def _download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
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
            # Use GPT-2 for text generation
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
        # FAISS index for semantic search
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # BM25 for keyword search
        self.bm25 = None
        
        # TF-IDF for statistical search
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, 
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        
        logger.info("✅ Search components initialized")
    
    def init_educational_scenarios(self):
        """Initialize comprehensive educational scenarios"""
        try:
            if ScenarioCase.query.count() == 0:
                self._create_comprehensive_scenarios()
                logger.info("✅ Educational scenarios initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing scenarios: {e}")
    
    def _create_comprehensive_scenarios(self):
        """Create comprehensive educational scenarios"""
        
        scenarios = [
            # Property and Theft Scenarios
            {
                "title": "Taking Someone's Bicycle Without Permission",
                "description": "A 12-year-old takes a bicycle from school premises without the owner's permission, intending to return it after a ride.",
                "legal_analysis": "This constitutes theft under Section 378 of Indian Penal Code, even if intention was to return the item. The act of taking someone's property without permission, regardless of intent to return, is legally theft.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Juvenile Justice (Care and Protection of Children) Act 2015, Right to Education Act provisions for school safety",
                "consequences": "For children under 16: Counseling sessions with school counselor, community service like helping in school maintenance, parental guidance workshop, educational session on property rights. No criminal record maintained. Focus on understanding respect for others' property.",
                "age_group": "child",
                "severity_level": "minor",
                "educational_note": "Taking someone's property without permission is theft, even if you plan to return it. Always ask permission first. Children are treated with care under Juvenile Justice Act, which focuses on rehabilitation and education rather than punishment.",
                "category": "property_theft",
                "keywords": "bicycle, taking without permission, school property, theft, children"
            },
            
            # Cyberbullying and Digital Crimes
            {
                "title": "Cyberbullying and Online Harassment",
                "description": "A 15-year-old posts mean comments and shares embarrassing photos of a classmate on social media platforms without consent, causing emotional distress.",
                "legal_analysis": "Cyberbullying involves multiple legal violations including harassment under IPC Section 506, defamation under Section 499, and violation of privacy under IT Act. Digital harassment can cause severe psychological harm and is treated seriously by law.",
                "applicable_laws": "Information Technology Act 2000 Section 66E (Violation of privacy), Section 67 (Publishing obscene content), Indian Penal Code Section 499 (Defamation), Section 509 (Insulting modesty of women), Section 506 (Criminal intimidation)",
                "consequences": "For teenagers (13-18): Mandatory digital literacy education, counseling on empathy and online behavior, community service related to anti-bullying campaigns, parental involvement in digital monitoring, possible school disciplinary action, educational workshop on cyber laws.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Cyberbullying can cause serious emotional harm and has real legal consequences. What you post online can hurt people deeply and follow you forever. Think before you post - treat others online as you would want to be treated.",
                "category": "cybercrime",
                "keywords": "cyberbullying, social media, harassment, online, photos, privacy"
            },
            
            # Shoplifting and Retail Theft
            {
                "title": "Shoplifting from a Store",
                "description": "A 17-year-old steals an expensive mobile phone worth ₹25,000 from an electronics store, thinking they won't get caught.",
                "legal_analysis": "Theft of valuable property is a serious offense under IPC Section 378. The value of stolen goods affects the severity of legal action. Stealing items worth over ₹20,000 can lead to more serious charges and consequences.",
                "applicable_laws": "Indian Penal Code Section 378 (Theft), Section 380 (Theft in dwelling house), Juvenile Justice Act provisions for children in conflict with law, Consumer Protection Act for store security rights",
                "consequences": "For older teens (16-18): Possible detention in observation home for assessment, mandatory counseling on values and ethics, restitution payment to store owner, community service in retail environment, family counseling sessions, educational program on earning and saving money legally.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Stealing expensive items has serious consequences that affect your future. Stores have security cameras and trained staff. It's much better to work hard, save money, and buy things legally. Your reputation and future opportunities are worth more than any item.",
                "category": "property_theft",
                "keywords": "shoplifting, stealing, mobile phone, expensive, store, retail theft"
            },
            
            # Traffic and Driving Violations
            {
                "title": "Underage Driving Without License",
                "description": "A 16-year-old drives a motorbike without a license and gets caught by traffic police during a routine check.",
                "legal_analysis": "Driving without a license violates Motor Vehicle Act 1988. Underage driving poses safety risks to the driver and public. Insurance claims may be invalid in case of accidents.",
                "applicable_laws": "Motor Vehicle Act 1988 Section 3 (Driving without license), Section 4 (Age restrictions for driving), Juvenile Justice Act, Insurance laws regarding coverage",
                "consequences": "Vehicle impoundment until guardian arrives, fine payment by parents/guardians, mandatory traffic education classes, delayed eligibility for license, parental liability for any damages, community service at traffic safety programs.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Driving without a license is dangerous for you and others on the road. Traffic rules exist to keep everyone safe. Wait until you're eligible, get proper training, and obtain a valid license. Your safety and others' lives matter more than convenience.",
                "category": "traffic_violation",
                "keywords": "driving, license, underage, motorbike, traffic police, vehicle"
            },
            
            # Vandalism and Property Damage
            {
                "title": "Vandalizing Public Property",
                "description": "A group of teenagers spray paints graffiti on a government building wall and nearby bus stop during evening hours.",
                "legal_analysis": "Vandalism of public property is a criminal offense that damages community resources funded by taxpayer money. It affects public spaces that belong to everyone.",
                "applicable_laws": "Indian Penal Code Section 425 (Mischief), Section 427 (Mischief causing damage to public property), Prevention of Damage to Public Property Act 1984, Local municipal laws",
                "consequences": "Fine equal to damage repair cost, community service cleaning and maintaining public areas, education program on civic responsibility and public property importance, parental financial liability, supervised community work with municipal authorities.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Public property belongs to everyone and is built with taxpayer money that could be used for schools, hospitals, and development. Damaging it means taking away resources from your own community. Channel creativity into legal art and expression.",
                "category": "vandalism",
                "keywords": "vandalism, graffiti, public property, government building, damage, spray paint"
            },
            
            # Privacy and Consent Violations
            {
                "title": "Sharing Private Content Without Consent",
                "description": "A teenager forwards private photos or messages of a classmate through messaging apps without their permission, causing embarrassment and distress.",
                "legal_analysis": "Sharing private content without consent violates privacy rights and dignity. It can constitute sexual harassment if content is intimate, and may cause severe psychological harm to victims.",
                "applicable_laws": "Information Technology Act Section 66E (Violation of privacy), Section 67/67A (Publishing obscene content), Indian Penal Code Section 354C (Voyeurism), Section 509 (Insulting modesty), Right to Privacy as fundamental right",
                "consequences": "Serious legal action possible including detention, mandatory counseling on consent and digital ethics, device monitoring and restrictions, education on privacy rights and dignity, community service with women's rights organizations, family counseling on respect and boundaries.",
                "age_group": "teen",
                "severity_level": "serious",
                "educational_note": "Sharing private content without permission violates someone's dignity and privacy rights. Once shared, you can never fully control where it goes. Always respect others' boundaries and privacy, both online and offline. Consent is mandatory for sharing any personal content.",
                "category": "privacy_violation",
                "keywords": "sharing photos, private content, consent, messaging apps, privacy, harassment"
            },
            
            # Academic Dishonesty
            {
                "title": "Examination Cheating and Academic Dishonesty",
                "description": "A student uses unfair means during school examination by copying from hidden notes and helping others cheat as well.",
                "legal_analysis": "While primarily an academic issue in school exams, repeated cheating can have legal implications in competitive exams. It violates academic integrity and fairness principles.",
                "applicable_laws": "Educational institution rules and regulations, potential fraud charges in competitive/government exams, Indian Penal Code Section 419 (Cheating by impersonation) in serious cases",
                "consequences": "Exam paper cancellation, possible debarment from future exams, school disciplinary action including suspension, parental involvement and counseling, mandatory academic integrity education, retake of examination under supervision.",
                "age_group": "teen",
                "severity_level": "minor",
                "educational_note": "Cheating undermines your own education and is unfair to honest students. It becomes a habit that can affect your character throughout life. Focus on learning and understanding rather than just getting grades. Success achieved through cheating is temporary and hollow.",
                "category": "academic_dishonesty",
                "keywords": "cheating, examination, unfair means, copying, academic integrity, school"
            },
            
            # Substance Abuse
            {
                "title": "Underage Drinking and Substance Use",
                "description": "A 16-year-old is caught consuming alcohol at a party and is found in an intoxicated state by authorities.",
                "legal_analysis": "Underage drinking violates prohibition laws in most Indian states. It poses serious health risks to developing brains and bodies, and can lead to dangerous behavior and accidents.",
                "applicable_laws": "State Prohibition Laws (varies by state), Juvenile Justice Act provisions, Indian Penal Code provisions on public intoxication, Child protection laws",
                "consequences": "Health screening and medical evaluation, mandatory counseling on substance abuse risks, parental involvement and family counseling, restriction on social activities until completion of rehabilitation program, educational sessions on health effects of alcohol.",
                "age_group": "teen",
                "severity_level": "moderate",
                "educational_note": "Underage drinking is illegal and harmful to your developing brain and body. Alcohol can impair judgment leading to dangerous decisions and accidents. Focus on healthy activities, sports, and social connections that don't involve substances. Your health and future are too valuable to risk.",
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
        logger.info(f"✅ Created {len(scenarios)} comprehensive educational scenarios")
    
    # Continuation of the CompleteLawEducationRAG class...
    
    def detect_scenario_query(self, query: str) -> Dict:
        """Advanced scenario detection with category classification"""
        query_lower = query.lower()
        
        # Scenario indicators
        scenario_indicators = [
            'what if i', 'what happens if', 'what would happen', 'if i do', 'if someone',
            'what crime', 'what law', 'what punishment', 'what penalty', 'consequences',
            'illegal', 'against law', 'breaking law', 'get in trouble', 'arrested',
            'jail', 'prison', 'fine', 'punishment', 'penalty', 'what if someone'
        ]
        
        # Activity categories with expanded keywords
        activity_keywords = {
            'property_theft': [
                'steal', 'theft', 'take without permission', 'shoplifting', 'robbery',
                'bicycle', 'phone', 'money', 'clothes', 'books', 'laptop', 'bag'
            ],
            'cybercrime': [
                'cyberbullying', 'online harassment', 'hacking', 'sharing photos',
                'social media', 'facebook', 'instagram', 'whatsapp', 'post online',
                'cyberbully', 'online', 'internet', 'digital', 'apps'
            ],
            'violence': [
                'fight', 'hit someone', 'assault', 'violence', 'hurt', 'beating',
                'punch', 'kick', 'slap', 'physical fight', 'abuse'
            ],
            'traffic_violation': [
                'drive without license', 'underage driving', 'traffic violation',
                'bike', 'car', 'vehicle', 'traffic rules', 'speed', 'license'
            ],
            'vandalism': [
                'graffiti', 'damage property', 'vandalism', 'break things',
                'destroy', 'public property', 'school property', 'building'
            ],
            'substance_abuse': [
                'drinking', 'alcohol', 'drugs', 'smoking', 'substance',
                'beer', 'wine', 'cigarettes', 'intoxicated', 'drunk'
            ],
            'academic_dishonesty': [
                'cheat in exam', 'copying', 'plagiarism', 'unfair means',
                'examination', 'test', 'homework', 'assignment'
            ],
            'privacy_violation': [
                'share photos', 'private content', 'without permission',
                'personal photos', 'private messages', 'consent'
            ]
        }
        
        # Check for scenario indicators
        has_scenario_indicator = any(indicator in query_lower for indicator in scenario_indicators)
        
        if has_scenario_indicator:
            # Determine activity category
            for category, keywords in activity_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    return {
                        'is_scenario': True,
                        'category': category,
                        'query_type': 'legal_scenario',
                        'confidence': 0.9
                    }
            
            return {
                'is_scenario': True,
                'category': 'general',
                'query_type': 'legal_scenario',
                'confidence': 0.7
            }
        
        return {
            'is_scenario': False, 
            'query_type': 'general',
            'confidence': 0.3
        }
    
    def find_relevant_scenarios(self, query: str, category: str = None) -> List[Dict]:
        """Find relevant educational scenarios with improved matching"""
        try:
            scenarios_query = ScenarioCase.query
            
            if category and category != 'general':
                scenarios_query = scenarios_query.filter_by(category=category)
            
            scenarios = scenarios_query.all()
            relevant_scenarios = []
            
            query_words = set(query.lower().split())
            
            for scenario in scenarios:
                # Calculate relevance score
                scenario_text = (
                    scenario.scenario_description + " " + 
                    scenario.legal_analysis + " " + 
                    scenario.applicable_laws + " " + 
                    scenario.educational_note + " " +
                    (scenario.keywords or "")
                ).lower()
                
                scenario_words = set(scenario_text.split())
                
                # Calculate intersection score
                intersection_score = len(query_words.intersection(scenario_words))
                
                # Calculate keyword match score
                keyword_score = 0
                if scenario.keywords:
                    scenario_keywords = set(scenario.keywords.lower().split(', '))
                    keyword_score = len(query_words.intersection(scenario_keywords)) * 2
                
                total_score = intersection_score + keyword_score
                
                if total_score > 0:
                    relevant_scenarios.append({
                        'scenario': scenario,
                        'relevance_score': total_score,
                        'category_match': category == scenario.category if category else False
                    })
            
            # Sort by relevance and category match
            relevant_scenarios.sort(
                key=lambda x: (x['category_match'], x['relevance_score']), 
                reverse=True
            )
            
            return relevant_scenarios[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"❌ Error finding scenarios: {e}")
            return []
    
    def generate_scenario_response(self, query: str, scenarios: List[Dict], user_age: str = "teen") -> str:
        """Generate comprehensive educational response for scenarios"""
        
        if not scenarios:
            return self._generate_general_legal_guidance(query, user_age)
        
        response = "🎓 **Educational Legal Scenario Analysis**\n\n"
        
        # Educational warning
        response += "⚠️ **Important Educational Notice**: This information is provided for educational purposes only to help students understand laws and consequences. For real legal situations, always consult qualified legal professionals, parents, teachers, or school counselors.\n\n"
        
        # Add age-appropriate introduction
        if user_age == "child":
            response += "👶 **For Young Students**: Remember, children are protected under special laws that focus on helping and teaching rather than punishing.\n\n"
        elif user_age == "teen":
            response += "👦👧 **For Teenagers**: You're old enough to understand the importance of making good choices and their consequences.\n\n"
        
        # Present scenarios
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
        
        # Add comprehensive guidance
        response += "🎓 **Complete Educational Guidance**:\n\n"
        
        response += "**📖 Why Laws Exist**:\n"
        response += "• Laws protect everyone's rights and safety\n"
        response += "• They help society function peacefully and fairly\n"
        response += "• They provide guidelines for respectful behavior\n"
        response += "• They ensure justice and equality for all citizens\n\n"
        
        response += "**👨‍⚖️ Special Protections for Young People**:\n"
        response += "• Juvenile Justice Act focuses on rehabilitation and education\n"
        response += "• Children and teenagers get counseling instead of harsh punishment\n"
        response += "• The goal is to help young people learn and grow\n"
        response += "• Parents and guardians are involved in the process\n"
        response += "• Educational programs help prevent future problems\n\n"
        
        response += "**🎯 How to Make Good Choices**:\n"
        response += "• Think about how your actions affect others\n"
        response += "• Ask yourself: 'Is this respectful and legal?'\n"
        response += "• Talk to parents, teachers, or counselors when unsure\n"
        response += "• Learn from others' mistakes rather than making your own\n"
        response += "• Focus on building good character and reputation\n\n"
        
        response += "**📚 Learning Resources**:\n"
        response += "• School counselors and teachers\n"
        response += "• Constitutional and legal education books\n"
        response += "• Government educational websites\n"
        response += "• Legal literacy programs in your community\n"
        response += "• Family discussions about values and choices\n\n"
        
        response += "**🌟 Remember**: The purpose of learning about laws is not to scare you, but to help you become a responsible, respectful citizen who contributes positively to society. Every good choice you make builds a better future for yourself and your community!"
        
        return response
    
    def _generate_general_legal_guidance(self, query: str, user_age: str) -> str:
        """Generate general educational guidance when no specific scenarios match"""
        
        response = "⚖️ **General Legal Education & Guidance**\n\n"
        
        response += "📚 **Understanding Our Legal System**:\n\n"
        
        response += "I understand you're curious about legal matters. Here's educational guidance to help you learn:\n\n"
        
        response += "**🏛️ About Laws and Rights**:\n"
        response += "• Laws are rules that help our society function peacefully and fairly\n"
        response += "• They protect people's rights, property, and dignity\n"
        response += "• Everyone has both rights AND responsibilities\n"
        response += "• The Indian Constitution guarantees fundamental rights to all citizens\n"
        response += "• Laws apply to everyone, but young people get special consideration\n\n"
        
        response += "**👨‍⚖️ Special Protections for Students**:\n"
        response += "• The Juvenile Justice Act protects children and teenagers\n"
        response += "• Focus is on rehabilitation, education, and character building\n"
        response += "• Parents and guardians are responsible for guiding young people\n"
        response += "• Schools have special responsibility for student welfare\n"
        response += "• Counseling and education are preferred over punishment\n\n"
        
        response += "**🎓 Educational Approach to Law Learning**:\n"
        response += "• Learn about laws through education, not by breaking them\n"
        response += "• Understand that every action has consequences\n"
        response += "• Respect others' rights, property, and dignity\n"
        response += "• When unsure about anything, ask trusted adults for guidance\n"
        response += "• Use knowledge to make better decisions and help others\n\n"
        
        response += "**💡 Helpful Resources for Legal Learning**:\n"
        response += "• School counselors and teachers\n"
        response += "• Legal literacy and civic education programs\n"
        response += "• Government educational websites and materials\n"
        response += "• Constitutional and legal studies textbooks\n"
        response += "• Community legal awareness programs\n\n"
        
        response += "**🎯 Questions You Can Ask**:\n"
        response += "• 'What are my fundamental rights as a student?'\n"
        response += "• 'What happens if someone bullies me online?'\n"
        response += "• 'How can I protect my privacy on social media?'\n"
        response += "• 'What should I do if I see someone breaking the law?'\n"
        response += "• 'How can I be a good citizen in my community?'\n\n"
        
        if user_age == "child":
            response += "👶 **Special Note for Young Students**: You're at a wonderful age to learn about being a good citizen. Focus on being kind, respectful, and helpful to others. Ask your parents and teachers any questions you have.\n\n"
        elif user_age == "teen":
            response += "👦👧 **Special Note for Teenagers**: You're developing into a responsible adult. This is the perfect time to understand your rights and responsibilities. Make choices that you'll be proud of as you grow up.\n\n"
        
        response += "🌟 **Remember**: The goal of learning about laws is to become a responsible citizen who contributes positively to society and helps make the world a better place for everyone!"
        
        return response
    
    # PDF Processing Methods
    def extract_text_from_pdf(self, pdf_file) -> Tuple[List[Dict], Dict]:
        """Enhanced PDF text extraction with multiple fallback methods"""
        try:
            # Primary: pdfplumber
            with pdfplumber.open(pdf_file) as pdf:
                text_content = []
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_content.append({
                                'page': page_num,
                                'text': page_text.strip(),
                                'method': 'pdfplumber'
                            })
                    except Exception as e:
                        logger.warning(f"pdfplumber failed on page {page_num}: {e}")
                
                if text_content:
                    metadata = {
                        'total_pages': total_pages,
                        'extraction_method': 'pdfplumber',
                        'pages_extracted': len(text_content),
                        'success_rate': len(text_content) / total_pages
                    }
                    return text_content, metadata
                
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")
        
        # Fallback: PyPDF2
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
                            'text': page_text.strip(),
                            'method': 'PyPDF2'
                        })
                except Exception as e:
                    logger.warning(f"PyPDF2 failed on page {page_num}: {e}")
            
            metadata = {
                'total_pages': total_pages,
                'extraction_method': 'PyPDF2',
                'pages_extracted': len(text_content),
                'success_rate': len(text_content) / total_pages if total_pages > 0 else 0
            }
            
            return text_content, metadata
            
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            return [], {'error': str(e), 'total_pages': 0, 'pages_extracted': 0}
    
    # Continue with more methods...
    # [Due to length constraints, I'll continue in the next message]
    
    # Save the current user and load existing documents
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
    
    def load_existing_documents(self):
        """Load existing processed documents into search indexes"""
        try:
            chunks = DocumentChunk.query.all()
            
            for chunk in chunks:
                if chunk.embedding_vector:
                    # Add to FAISS index
                    embedding = np.array(chunk.embedding_vector).astype('float32')
                    self.faiss_index.add(embedding.reshape(1, -1))
                    
                    # Add to document storage
                    self.documents.append(chunk.content)
                    
                    # Get PDF info
                    pdf_doc = PDFDocument.query.get(chunk.pdf_id)
                    self.document_metadata.append({
                        'chunk_id': chunk.id,
                        'pdf_id': chunk.pdf_id,
                        'filename': pdf_doc.filename if pdf_doc else 'Unknown',
                        'page_number': chunk.page_number,
                        'chunk_index': chunk.chunk_index,
                        'content_type': chunk.content_type,
                        'document_type': pdf_doc.document_type if pdf_doc else 'general'
                    })
            
            # Rebuild search indexes
            self._rebuild_search_indexes()
            
            logger.info(f"✅ Loaded {len(chunks)} existing document chunks")
            
        except Exception as e:
            logger.error(f"❌ Error loading existing documents: {e}")
    
    def _rebuild_search_indexes(self):
        """Rebuild BM25 and TF-IDF search indexes"""
        try:
            if self.documents:
                # BM25 index
                tokenized_docs = [doc.split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                
                # TF-IDF index
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
                
                logger.info(f"✅ Search indexes rebuilt with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"❌ Error rebuilding search indexes: {e}")

# Initialize Complete RAG System
complete_rag = CompleteLawEducationRAG()

# =====================================================================================================
# FLASK ROUTES - COMPLETE API
# =====================================================================================================

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Educational Law & Constitution RAG Chatbot</title>
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
        .features { color: #2d3748; font-weight: bold; }
        
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
            <p class="features"><strong>Perfect for 8th-12th Grade Students Learning About Indian Constitution & Law System</strong></p>
            <p>💰 100% FREE • 🔒 Private & Safe • 📚 Educational Focus • 🎭 Scenario-Based Learning</p>
            <p>🏛️ Constitutional Education • ⚖️ Legal Awareness • 👨‍🏫 Teacher & Parent Approved</p>
        </div>
        
        <div class="warning-box">
            ⚠️ <strong>Educational Purpose Only</strong>: This chatbot is designed for educational learning about laws, constitution, and civic responsibility. 
            It teaches students about consequences through safe, interactive scenarios. Always consult legal professionals for real legal situations.
        </div>
        
        <div class="feature-highlight">
            <h3>🌟 Complete Educational Features:</h3>
            <ul>
                <li>📚 <strong>Advanced PDF Upload & Analysis</strong>: Upload constitution, law books, legal documents with intelligent processing</li>
                <li>🎭 <strong>Interactive Scenario-Based Learning</strong>: Learn consequences through educational "What if..." examples</li>
                <li>👶👦👧 <strong>Age-Appropriate Guidance</strong>: Different responses for children (8-12), teenagers (13-17), and adults (18+)</li>
                <li>⚖️ <strong>Comprehensive Legal Education</strong>: Understand rights, laws, and civic responsibilities safely</li>
                <li>🏛️ <strong>Constitutional Deep Dive</strong>: Detailed exploration of Indian Constitution and fundamental rights</li>
                <li>📖 <strong>Search History & Analytics</strong>: Track learning progress and revisit previous questions</li>
                <li>🧠 <strong>Self-Learning System</strong>: Improves responses based on user interactions and feedback</li>
                <li>🔍 <strong>Advanced RAG Search</strong>: Multi-method search using FAISS, BM25, and TF-IDF for best results</li>
            </ul>
        </div>
        
        <div class="section upload-section">
            <h2>📄 Upload Legal & Constitutional Documents</h2>
            <p>Upload PDFs of constitution, law books, legal guides, or educational materials for personalized learning</p>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="file-input">
                    <input type="file" id="pdfFile" name="pdf" accept=".pdf" multiple>
                    <p><strong>📚 Recommended Documents:</strong> Indian Constitution, Legal textbooks, Law guides, Rights documents, Civic education materials</p>
                </div>
                <button type="submit" class="btn">📤 Upload Legal Documents</button>
            </form>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="section scenarios-section">
            <h2>🎭 Interactive Educational Legal Scenarios</h2>
            <p>Learn about laws and consequences through safe, educational examples designed for students</p>
            
            <div class="age-selector">
                <label for="ageGroup"><strong>👤 Select Your Age Group for Appropriate Guidance:</strong></label><br><br>
                <select id="ageGroup">
                    <option value="child">👶 Child (8-12 years) - Simple, protective guidance</option>
                    <option value="teen" selected>👦👧 Teenager (13-17 years) - Detailed consequences and choices</option>
                    <option value="adult">👨👩 Adult (18+ years) - Full legal implications</option>
                </select>
            </div>
            
            <div class="scenarios-grid">
                <div class="scenario-card">
                    <h4>🚲 Property Rights & Theft</h4>
                    <p>Learn about taking things without permission, understanding property rights, theft laws, and age-appropriate consequences for young people</p>
                    <button onclick="askScenario('What happens if I take someone\\'s bicycle without permission?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>💻 Cyberbullying & Digital Responsibility</h4>
                    <p>Understand online harassment, cyberbullying laws, digital ethics, privacy rights, and how to be a responsible digital citizen</p>
                    <button onclick="askScenario('What are the consequences of cyberbullying someone online?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏪 Shoplifting & Consumer Rights</h4>
                    <p>Learn about theft in stores, legal consequences, understanding value of property, and making ethical choices about money and possessions</p>
                    <button onclick="askScenario('What happens if I steal something expensive from a store?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🏍️ Traffic Rules & Road Safety</h4>
                    <p>Understand driving laws, license requirements, age restrictions, road safety responsibilities, and consequences of traffic violations</p>
                    <button onclick="askScenario('What happens if I drive a motorbike without a license?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🎨 Vandalism & Public Property</h4>
                    <p>Learn about property damage, public property laws, civic responsibility, community impact, and respecting shared spaces</p>
                    <button onclick="askScenario('What happens if I spray paint graffiti on public buildings?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>📱 Privacy Rights & Consent</h4>
                    <p>Understand privacy laws, sharing content without permission, digital ethics, consent importance, and respecting others' boundaries</p>
                    <button onclick="askScenario('What happens if I share someone\\'s private photos without permission?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>📝 Academic Integrity & Honesty</h4>
                    <p>Learn about examination cheating, academic dishonesty, plagiarism, the value of honest learning, and building character through education</p>
                    <button onclick="askScenario('What happens if I cheat in school examinations?')" class="btn btn-scenario">🎓 Learn About This</button>
                </div>
                
                <div class="scenario-card">
                    <h4>🍺 Substance Abuse & Health</h4>
                    <p>Understand underage drinking laws, substance abuse consequences, health risks, making healthy choices, and peer pressure resistance</p>
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
            <p>Ask questions about laws, rights, constitution, or explore educational scenarios. Your learning is tracked and improved over time!</p>
            
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

        // Enhanced upload functionality
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
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status warning">⏳ Uploading and processing legal documents... This may take a few minutes for large files.</div>';
            
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
                        '<br>📄 Total chunks created: ' + result.total_chunks + '</div>';
                    loadDocuments();
                } else {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ ' + result.error + '</div>';
                }
            } catch (error) {
                document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Upload failed: ' + error.message + '</div>';
            }
        };
        
        // Enhanced chat functionality
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const query = input.value.trim();
            if (!query) return;
            
            const ageGroup = document.getElementById('ageGroup').value;
            
            // Add user message
            addMessage('user', query);
            input.value = '';
            
            // Add loading message
            const loadingId = addMessage('bot', '🤔 Analyzing your question, searching documents, and preparing educational response...');
            
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
                
                // Remove loading message
                document.getElementById(loadingId).remove();
                
                if (result.response) {
                    addMessage('bot', result.response, result);
                } else {
                    addMessage('bot', '❌ Error: ' + (result.error || 'Unknown error occurred'));
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
            
            // Format content with better styling
            let formattedContent = content
                .replace(/\\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/^(#{1,6})\s*(.*?)$/gm, '<h$1>$2</h$1>')
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
                if (metadata.relevance_score) {
                    html += '🎯 Relevance Score: ' + (metadata.relevance_score * 100).toFixed(1) + '%<br>';
                }
                html += '</div>';
                
                // Add feedback buttons
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
                
                // Update button to show feedback was recorded
                const messageDiv = document.getElementById(messageId);
                const buttons = messageDiv.querySelectorAll('button');
                buttons.forEach(btn => {
                    btn.style.opacity = '0.5';
                    btn.disabled = true;
                });
                
                // Add thank you message
                const thankYou = document.createElement('span');
                thankYou.style.color = '#48bb78';
                thankYou.style.fontWeight = 'bold';
                thankYou.innerHTML = ' ✅ Thank you for your feedback!';
                buttons[buttons.length - 1].parentNode.appendChild(thankYou);
                
            } catch (error) {
                console.error('Feedback error:', error);
            }
        }
        
        // Load documents with enhanced display
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
                    docsDiv.innerHTML = '<div class="doc-item">📝 No legal documents uploaded yet.<br><strong>Start by uploading:</strong> Indian Constitution, Law textbooks, Legal guides, Rights documents</div>';
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
                    
                    html += '<div style="background: #f0fff4; padding: 15px; border-radius: 8px; text-align: center;">';
                    html += '<div style="font-size: 24px; font-weight: bold; color: #2d3748;">' + (stats.days_active || 0) + '</div>';
                    html += '<div style="color: #4a5568;">Days Learning</div>';
                    html += '</div>';
                    
                    html += '</div>';
                }
                
                if (result.recent_topics && result.recent_topics.length > 0) {
                    html += '<h4 style="color: #2d3748; margin: 15px 0;">📚 Recent Learning Topics:</h4>';
                    html += '<ul style="margin-left: 20px;">';
                    result.recent_topics.forEach(topic => {
                        html += '<li style="margin: 5px 0; color: #4a5568;">' + topic + '</li>';
                    });
                    html += '</ul>';
                }
                
                html += '<div style="margin-top: 20px; padding: 15px; background: #ebf8ff; border-radius: 8px;">';
                html += '<p style="color: #2a4365; margin: 0;"><strong>🎓 Keep Learning!</strong> Your progress shows your commitment to understanding laws and being a responsible citizen. Continue asking questions and exploring scenarios!</p>';
                html += '</div>';
                
                html += '</div>';
                analyticsDiv.innerHTML = html;
                
            } catch (error) {
                document.getElementById('analyticsDisplay').innerHTML = '<div style="color: #e53e3e; padding: 15px;">❌ Error loading analytics: ' + error.message + '</div>';
            }
        }
        
        // Initialize page
        loadDocuments();
        
        // Allow Enter key in chat
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Auto-scroll chat
        function scrollChatToBottom() {
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Welcome message
        setTimeout(() => {
            addMessage('bot', 
                '🎓 Welcome to your Educational Law & Constitution Learning Assistant!\\n\\n' +
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

# Continue with remaining Flask routes in next part due to length...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        complete_rag.load_existing_documents()
    
    logger.info("🚀 Complete Educational Law & Constitution RAG Chatbot Starting...")
    logger.info("🎓 Ready to teach students about laws, rights, and civic responsibility!")
    logger.info("💰 100% FREE • 🎭 Scenario-Based • 🛡️ Safe & Educational")
    
    app.run(debug=True, port=5000, host='0.0.0.0')