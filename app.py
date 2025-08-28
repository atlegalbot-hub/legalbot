from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
from chromadb.utils import embedding_functions

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///constitution_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB for vector storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="constitution_knowledge",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
)

# Database Models
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)  # For self-learning
    
class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    difficulty_level = db.Column(db.String(20), nullable=False)  # 8th, 9th, 10th, 11th, 12th
    
class OptimizationMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Indian Constitution Knowledge Base
CONSTITUTION_KNOWLEDGE = {
    "history": {
        "title": "History of Indian Constitution",
        "content": """
        The Indian Constitution was drafted by the Constituent Assembly, which was formed in 1946.
        
        Key Timeline:
        - 1946: Constituent Assembly formed under Cabinet Mission Plan
        - August 29, 1947: Drafting Committee appointed with Dr. B.R. Ambedkar as Chairman
        - November 26, 1949: Constitution adopted by Constituent Assembly
        - January 26, 1950: Constitution came into effect (Republic Day)
        
        Key Figures:
        - Dr. B.R. Ambedkar: Chairman of Drafting Committee, known as "Father of Indian Constitution"
        - Dr. Rajendra Prasad: President of Constituent Assembly
        - Jawaharlal Nehru: Prime Minister, gave Objective Resolution
        - Sardar Vallabhbhai Patel: Deputy Prime Minister, handled integration of princely states
        
        The Constitution took 2 years, 11 months, and 18 days to complete.
        """
    },
    "fundamental_rights": {
        "title": "Fundamental Rights (Articles 12-35)",
        "content": """
        Six Fundamental Rights guaranteed by Indian Constitution:
        
        1. Right to Equality (Articles 14-18):
           - Equality before law
           - Prohibition of discrimination
           - Equality of opportunity in employment
           - Abolition of untouchability
           
        2. Right to Freedom (Articles 19-22):
           - Freedom of speech and expression
           - Freedom of assembly
           - Freedom of movement
           - Freedom of residence
           
        3. Right against Exploitation (Articles 23-24):
           - Prohibition of traffic in human beings
           - Prohibition of child labor
           
        4. Right to Freedom of Religion (Articles 25-28):
           - Freedom of conscience and religion
           - Right to manage religious affairs
           
        5. Cultural and Educational Rights (Articles 29-30):
           - Rights of minorities
           - Right to establish educational institutions
           
        6. Right to Constitutional Remedies (Article 32):
           - Right to approach Supreme Court
           - Dr. Ambedkar called it "Heart and Soul" of Constitution
        """
    },
    "directive_principles": {
        "title": "Directive Principles of State Policy (Articles 36-51)",
        "content": """
        DPSP are guidelines for the government to create a welfare state:
        
        Key Principles:
        - Adequate means of livelihood for all citizens
        - Equal distribution of material resources
        - Equal pay for equal work for men and women
        - Protection of children and youth
        - Right to work and education
        - Public assistance in unemployment, old age, sickness
        - Uniform Civil Code
        - Protection of environment and wildlife
        
        Classification:
        1. Socialist Principles: Equal distribution of wealth
        2. Gandhian Principles: Village panchayats, cottage industries
        3. Liberal Principles: Uniform Civil Code, separation of judiciary
        
        Note: DPSPs are non-justiciable (cannot be enforced by courts)
        """
    },
    "fundamental_duties": {
        "title": "Fundamental Duties (Article 51A)",
        "content": """
        Added by 42nd Amendment (1976), inspired by USSR Constitution:
        
        11 Fundamental Duties:
        1. Respect Constitution, National Flag, and National Anthem
        2. Follow noble ideals of freedom struggle
        3. Protect sovereignty and integrity of India
        4. Defend country and render national service
        5. Promote harmony and brotherhood
        6. Value and preserve composite culture
        7. Protect natural environment
        8. Develop scientific temper and humanism
        9. Safeguard public property
        10. Strive for excellence in individual and collective activity
        11. Provide education opportunities to children (added by 86th Amendment, 2002)
        
        Note: Like DPSPs, Fundamental Duties are also non-justiciable
        """
    },
    "amendment_process": {
        "title": "Constitutional Amendment Process (Article 368)",
        "content": """
        Three types of amendment procedures:
        
        1. Simple Majority (Like ordinary law):
           - Admission of new states
           - Formation of new states
           - Abolition of Legislative Councils
           
        2. Special Majority (2/3 majority + 50% of total membership):
           - Fundamental Rights
           - Directive Principles
           - Most constitutional provisions
           
        3. Special Majority + State Ratification:
           - Distribution of legislative powers
           - Representation of states in Parliament
           - Election of President
           - Amendment procedure itself
           
        Notable Amendments:
        - 1st Amendment (1951): Added 9th Schedule
        - 42nd Amendment (1976): "Mini Constitution"
        - 44th Amendment (1978): Restored many provisions
        - 73rd & 74th Amendments (1992): Panchayati Raj
        """
    }
}

def initialize_knowledge_base():
    """Initialize the knowledge base with constitutional data"""
    if KnowledgeBase.query.count() == 0:
        for key, value in CONSTITUTION_KNOWLEDGE.items():
            kb_entry = KnowledgeBase(
                topic=key,
                content=value["content"],
                category="constitution",
                difficulty_level="8th-12th"
            )
            db.session.add(kb_entry)
            
            # Add to vector database
            collection.add(
                documents=[value["content"]],
                metadatas=[{"topic": key, "title": value["title"]}],
                ids=[key]
            )
        
        db.session.commit()

def find_best_match(query, user_class="10th"):
    """Find the best matching content for a query"""
    try:
        # Search in vector database
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if results['documents'] and len(results['documents'][0]) > 0:
            best_match = results['documents'][0][0]
            metadata = results['metadatas'][0][0] if results['metadatas'] else {}
            
            # Generate contextual response
            response = generate_contextual_response(query, best_match, metadata, user_class)
            return response
        else:
            return generate_fallback_response(query)
            
    except Exception as e:
        print(f"Error in find_best_match: {e}")
        return generate_fallback_response(query)

def generate_contextual_response(query, content, metadata, user_class):
    """Generate a contextual response based on the query and matched content"""
    
    # Extract relevant information based on query keywords
    query_lower = query.lower()
    
    response = f"**{metadata.get('title', 'Indian Constitution Information')}**\n\n"
    
    if any(word in query_lower for word in ['history', 'when', 'who', 'timeline']):
        response += "📚 **Historical Context:**\n"
    elif any(word in query_lower for word in ['rights', 'fundamental']):
        response += "⚖️ **Rights and Freedoms:**\n"
    elif any(word in query_lower for word in ['duties', 'responsibilities']):
        response += "🤝 **Civic Responsibilities:**\n"
    elif any(word in query_lower for word in ['amendment', 'change', 'modify']):
        response += "📝 **Constitutional Changes:**\n"
    else:
        response += "📖 **Key Information:**\n"
    
    # Add the main content
    response += content
    
    # Add class-specific note
    class_tips = {
        "8th": "💡 **For Class 8:** Focus on understanding basic concepts and key personalities.",
        "9th": "💡 **For Class 9:** Remember the connection between freedom struggle and constitutional making.",
        "10th": "💡 **For Class 10:** Pay attention to the balance between rights and duties.",
        "11th": "💡 **For Class 11:** Understand the federal structure and separation of powers.",
        "12th": "💡 **For Class 12:** Focus on constitutional amendments and contemporary challenges."
    }
    
    if user_class in class_tips:
        response += f"\n\n{class_tips[user_class]}"
    
    return response

def generate_fallback_response(query):
    """Generate a fallback response when no good match is found"""
    return """
    I apologize, but I couldn't find specific information about your query in my current knowledge base. 
    
    However, I can help you with topics related to:
    
    🏛️ **Indian Constitution:**
    - History and making of Constitution
    - Fundamental Rights and Duties
    - Directive Principles of State Policy
    - Amendment Process
    - Constitutional Bodies
    
    ⚖️ **Legal System:**
    - Court Structure
    - Legal Procedures
    - Important Laws
    
    Could you please rephrase your question or ask about any of these specific topics?
    """

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        query = data.get('query', '')
        user_id = data.get('user_id', 'anonymous')
        user_class = data.get('class', '10th')
        
        if not query.strip():
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Find best response
        response = find_best_match(query, user_class)
        
        # Save to search history
        history_entry = SearchHistory(
            user_id=user_id,
            query=query,
            response=response
        )
        db.session.add(history_entry)
        db.session.commit()
        
        # Update optimization metrics
        update_optimization_metrics('total_queries')
        
        return jsonify({
            'response': response,
            'query_id': history_entry.id,
            'timestamp': history_entry.timestamp.isoformat()
        })
        
    except Exception as e:
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
                'feedback_score': h.feedback_score
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
        score = data.get('score')  # 1-5 rating
        
        history_entry = SearchHistory.query.get(query_id)
        if history_entry:
            history_entry.feedback_score = score
            db.session.commit()
            
            # Update optimization metrics
            update_optimization_metrics('feedback_received')
            if score >= 4:
                update_optimization_metrics('positive_feedback')
            
            return jsonify({'message': 'Feedback recorded successfully'})
        else:
            return jsonify({'error': 'Query not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    try:
        # Calculate various metrics
        total_queries = SearchHistory.query.count()
        avg_feedback = db.session.query(db.func.avg(SearchHistory.feedback_score))\
                                .filter(SearchHistory.feedback_score > 0).scalar() or 0
        
        positive_feedback_count = SearchHistory.query.filter(SearchHistory.feedback_score >= 4).count()
        feedback_count = SearchHistory.query.filter(SearchHistory.feedback_score > 0).count()
        
        satisfaction_rate = (positive_feedback_count / feedback_count * 100) if feedback_count > 0 else 0
        
        # Get usage over time (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_queries = SearchHistory.query.filter(SearchHistory.timestamp >= week_ago).count()
        
        return jsonify({
            'total_queries': total_queries,
            'average_feedback': round(avg_feedback, 2),
            'satisfaction_rate': round(satisfaction_rate, 2),
            'recent_activity': recent_queries,
            'learning_progress': calculate_learning_progress()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_optimization_metrics(metric_name, value=1):
    """Update optimization metrics"""
    try:
        metric = OptimizationMetrics(
            metric_name=metric_name,
            metric_value=value
        )
        db.session.add(metric)
        db.session.commit()
    except Exception as e:
        print(f"Error updating metrics: {e}")

def calculate_learning_progress():
    """Calculate learning progress based on feedback patterns"""
    try:
        # Get feedback trends
        recent_feedback = SearchHistory.query.filter(
            SearchHistory.feedback_score > 0,
            SearchHistory.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(SearchHistory.timestamp.desc()).limit(100).all()
        
        if len(recent_feedback) < 10:
            return {"status": "Insufficient data", "progress": 0}
        
        # Calculate improvement trend
        first_half = recent_feedback[len(recent_feedback)//2:]
        second_half = recent_feedback[:len(recent_feedback)//2]
        
        avg_first = sum(f.feedback_score for f in first_half) / len(first_half)
        avg_second = sum(f.feedback_score for f in second_half) / len(second_half)
        
        improvement = ((avg_second - avg_first) / avg_first) * 100 if avg_first > 0 else 0
        
        return {
            "status": "Improving" if improvement > 5 else "Stable" if improvement > -5 else "Needs Attention",
            "progress": round(improvement, 2),
            "current_avg": round(avg_second, 2)
        }
        
    except Exception as e:
        return {"status": "Error calculating progress", "progress": 0}

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
                'timestamp': r.timestamp.isoformat()
            } for r in results]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_knowledge_base()
    app.run(debug=True, port=5000)