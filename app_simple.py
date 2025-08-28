from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import re

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///constitution_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_score = db.Column(db.Integer, default=0)
    
class KnowledgeBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    difficulty_level = db.Column(db.String(20), nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # Store keywords as comma-separated string
    
class OptimizationMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Indian Constitution Knowledge Base with Keywords
CONSTITUTION_KNOWLEDGE = {
    "history": {
        "title": "History of Indian Constitution",
        "keywords": ["history", "dr ambedkar", "constituent assembly", "1950", "republic day", "father", "constitution", "timeline", "formation", "making"],
        "content": """
🏛️ **History of Indian Constitution**

The Indian Constitution was drafted by the Constituent Assembly, which was formed in 1946.

**📅 Key Timeline:**
- **1946**: Constituent Assembly formed under Cabinet Mission Plan
- **August 29, 1947**: Drafting Committee appointed with Dr. B.R. Ambedkar as Chairman
- **November 26, 1949**: Constitution adopted by Constituent Assembly
- **January 26, 1950**: Constitution came into effect (Republic Day)

**👥 Key Personalities:**
- **Dr. B.R. Ambedkar**: Chairman of Drafting Committee, known as "Father of Indian Constitution"
- **Dr. Rajendra Prasad**: President of Constituent Assembly
- **Jawaharlal Nehru**: Prime Minister, gave Objective Resolution
- **Sardar Vallabhbhai Patel**: Deputy Prime Minister, handled integration of princely states

**⏱️ Timeline**: The Constitution took 2 years, 11 months, and 18 days to complete.

**📝 Interesting Facts:**
- Originally handwritten in Hindi and English
- Currently has 395 articles and 12 schedules
- Longest written constitution in the world
        """
    },
    "fundamental_rights": {
        "title": "Fundamental Rights (Articles 12-35)",
        "keywords": ["fundamental rights", "articles 12-35", "equality", "freedom", "right to life", "constitutional remedies", "rights", "equality", "freedom", "religion", "exploitation"],
        "content": """
⚖️ **Fundamental Rights (Articles 12-35)**

Six Fundamental Rights guaranteed by Indian Constitution:

**1. Right to Equality (Articles 14-18):**
   - Equality before law and equal protection of laws
   - Prohibition of discrimination on grounds of religion, race, caste, sex
   - Equality of opportunity in public employment
   - Abolition of untouchability and titles

**2. Right to Freedom (Articles 19-22):**
   - Freedom of speech and expression
   - Freedom of peaceful assembly
   - Freedom to form associations
   - Freedom of movement throughout India
   - Freedom to reside and settle anywhere in India
   - Freedom of profession, occupation, trade, or business

**3. Right against Exploitation (Articles 23-24):**
   - Prohibition of traffic in human beings and forced labor
   - Prohibition of employment of children in hazardous work

**4. Right to Freedom of Religion (Articles 25-28):**
   - Freedom of conscience and free profession, practice, and propagation of religion
   - Freedom to manage religious affairs
   - Freedom from payment of taxes for promotion of any religion
   - Freedom from religious instruction in state-funded schools

**5. Cultural and Educational Rights (Articles 29-30):**
   - Protection of language, script, and culture of minorities
   - Right of minorities to establish and administer educational institutions

**6. Right to Constitutional Remedies (Article 32):**
   - Right to directly approach Supreme Court for enforcement of rights
   - Dr. Ambedkar called it the "Heart and Soul" of the Constitution
   - Supreme Court can issue writs: Habeas Corpus, Mandamus, Prohibition, Certiorari, Quo-warranto
        """
    },
    "directive_principles": {
        "title": "Directive Principles of State Policy (Articles 36-51)",
        "keywords": ["directive principles", "dpsp", "articles 36-51", "state policy", "welfare state", "gandhi", "socialist", "non-justiciable"],
        "content": """
📋 **Directive Principles of State Policy (Articles 36-51)**

DPSP are guidelines for the government to create a welfare state:

**🎯 Key Principles:**
- Adequate means of livelihood for all citizens
- Equal distribution of material resources of community
- Equal pay for equal work for men and women
- Protection of children and youth against exploitation
- Right to work, education, and public assistance
- Uniform Civil Code for all citizens
- Protection and improvement of environment and wildlife

**📚 Classification:**

**1. Socialist Principles:**
   - Equal distribution of wealth and resources
   - Worker's participation in management
   - Living wages for workers

**2. Gandhian Principles:**
   - Organization of village panchayats
   - Promotion of cottage industries
   - Prohibition of cow slaughter
   - Promotion of handicrafts

**3. Liberal/Intellectual Principles:**
   - Uniform Civil Code
   - Separation of judiciary from executive
   - International peace and security

**⚖️ Nature**: DPSPs are non-justiciable (cannot be enforced by courts) but are fundamental in governance.

**🎯 Goal**: To establish a welfare state and achieve socio-economic democracy.
        """
    },
    "fundamental_duties": {
        "title": "Fundamental Duties (Article 51A)",
        "keywords": ["fundamental duties", "article 51a", "42nd amendment", "civic duties", "responsibilities", "obligations"],
        "content": """
🤝 **Fundamental Duties (Article 51A)**

Added by 42nd Amendment (1976), inspired by USSR Constitution:

**📜 11 Fundamental Duties:**

1. **Respect Constitution**: Abide by Constitution, respect National Flag and National Anthem
2. **Freedom Struggle Ideals**: Cherish and follow noble ideals of freedom struggle
3. **Protect Integrity**: Uphold and protect sovereignty, unity and integrity of India
4. **Defend Country**: Defend the country and render national service when called upon
5. **Promote Harmony**: Promote harmony and spirit of brotherhood among all people
6. **Preserve Culture**: Value and preserve rich heritage of composite culture
7. **Protect Environment**: Protect and improve natural environment (forests, lakes, rivers, wildlife)
8. **Scientific Temper**: Develop scientific temper, humanism and spirit of inquiry
9. **Safeguard Property**: Safeguard public property and abjure violence
10. **Strive for Excellence**: Strive towards excellence in all spheres of individual and collective activity
11. **Education Duty**: Provide opportunities for education to children between 6-14 years (added by 86th Amendment, 2002)

**⚖️ Nature**: Like DPSPs, Fundamental Duties are also non-justiciable but serve as moral obligations.

**🎯 Purpose**: To remind citizens of their responsibilities towards nation and society.
        """
    },
    "amendment_process": {
        "title": "Constitutional Amendment Process (Article 368)",
        "keywords": ["amendment", "article 368", "constitutional changes", "parliament", "special majority", "ratification"],
        "content": """
📝 **Constitutional Amendment Process (Article 368)**

Three types of amendment procedures:

**1. Simple Majority (Like ordinary law):**
   - Admission or establishment of new states
   - Formation of new states and alteration of areas, boundaries or names of states
   - Abolition or creation of Legislative Councils in states
   - Second Schedule (salaries, allowances, privileges)
   - Quorum in Parliament
   - Salaries and allowances of President, Governor, Speaker, Judge etc.

**2. Special Majority (2/3 majority of present & voting + 50% of total strength):**
   - Fundamental Rights
   - Directive Principles of State Policy
   - All other provisions not covered elsewhere
   - Supreme Court and High Court provisions (except those requiring ratification)

**3. Special Majority + State Ratification (by half of the states):**
   - Election of President and its manner
   - Extent of executive power of Union and states
   - Distribution of legislative powers between Union and states
   - Representation of states in Parliament
   - Amendment procedure itself (Article 368)
   - Matters related to High Courts

**📈 Notable Amendments:**
- **1st Amendment (1951)**: Added 9th Schedule to protect land reform laws
- **42nd Amendment (1976)**: Called "Mini Constitution" - added Socialist, Secular to Preamble
- **44th Amendment (1978)**: Restored many provisions changed by 42nd Amendment
- **73rd & 74th Amendments (1992)**: Panchayati Raj and Urban Local Bodies
- **86th Amendment (2002)**: Right to Education as Fundamental Right

**🎯 Balance**: Amendment process balances flexibility with stability of Constitution.
        """
    },
    "preamble": {
        "title": "Preamble of Indian Constitution",
        "keywords": ["preamble", "we the people", "sovereign", "socialist", "secular", "democratic", "republic", "justice", "liberty", "equality", "fraternity"],
        "content": """
🏛️ **Preamble of Indian Constitution**

**📜 Text:**
"WE, THE PEOPLE OF INDIA, having solemnly resolved to constitute India into a SOVEREIGN SOCIALIST SECULAR DEMOCRATIC REPUBLIC and to secure to all its citizens:

JUSTICE, social, economic and political;
LIBERTY of thought, expression, belief, faith and worship;
EQUALITY of status and of opportunity; and to promote among them all
FRATERNITY assuring the dignity of the individual and the unity and integrity of the Nation;

IN OUR CONSTITUENT ASSEMBLY this twenty-sixth day of November, 1949, do HEREBY ADOPT, ENACT AND GIVE TO OURSELVES THIS CONSTITUTION."

**🔑 Key Words Explained:**

**🌟 SOVEREIGN**: India is internally and externally free
**🤝 SOCIALIST**: Wealth should not be concentrated in few hands
**🕊️ SECULAR**: No official religion, equal respect to all religions
**🗳️ DEMOCRATIC**: Government by the people, for the people
**🏛️ REPUBLIC**: Head of state is elected, not hereditary

**⚖️ Core Values:**
- **JUSTICE**: Social, Economic, Political
- **LIBERTY**: Of thought, expression, belief, faith, worship
- **EQUALITY**: Of status and opportunity
- **FRATERNITY**: Unity and integrity of nation

**📅 Amendment**: Only amended once by 42nd Amendment (1976) which added "Socialist" and "Secular".

**🎯 Significance**: Reflects philosophy and fundamental values of Constitution.
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
                difficulty_level="8th-12th",
                keywords=",".join(value["keywords"])
            )
            db.session.add(kb_entry)
        
        db.session.commit()

def find_best_match(query, user_class="10th"):
    """Find the best matching content for a query using keyword matching"""
    try:
        query_lower = query.lower()
        
        # Search for exact keyword matches
        best_match = None
        best_score = 0
        
        knowledge_entries = KnowledgeBase.query.all()
        
        for entry in knowledge_entries:
            score = 0
            keywords = entry.keywords.split(",") if entry.keywords else []
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword.strip().lower() in query_lower:
                    score += len(keyword.strip())
            
            # Check for topic name match
            if entry.topic.replace("_", " ").lower() in query_lower:
                score += 20
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        if best_match:
            response = generate_contextual_response(query, best_match.content, {"title": best_match.topic.replace("_", " ").title()}, user_class)
            return response
        else:
            return generate_fallback_response(query)
            
    except Exception as e:
        print(f"Error in find_best_match: {e}")
        return generate_fallback_response(query)

def generate_contextual_response(query, content, metadata, user_class):
    """Generate a contextual response based on the query and matched content"""
    
    query_lower = query.lower()
    
    response = content
    
    # Add class-specific tip
    class_tips = {
        "8th": "\n\n💡 **For Class 8:** Focus on understanding basic concepts and remember key personalities like Dr. B.R. Ambedkar.",
        "9th": "\n\n💡 **For Class 9:** Remember the connection between freedom struggle and constitutional making process.",
        "10th": "\n\n💡 **For Class 10:** Pay attention to the balance between rights and duties in our Constitution.",
        "11th": "\n\n💡 **For Class 11:** Understand the federal structure and separation of powers in Indian government.",
        "12th": "\n\n💡 **For Class 12:** Focus on constitutional amendments and contemporary challenges facing our democracy."
    }
    
    if user_class in class_tips:
        response += class_tips[user_class]
    
    # Add relevant exam tip
    if any(word in query_lower for word in ['exam', 'test', 'important', 'questions']):
        response += "\n\n📚 **Exam Tip:** This topic is frequently asked in board exams. Focus on dates, key personalities, and main provisions."
    
    return response

def generate_fallback_response(query):
    """Generate a fallback response when no good match is found"""
    return """
🤔 I apologize, but I couldn't find specific information about your query in my current knowledge base. 

However, I can help you with topics related to:

🏛️ **Indian Constitution:**
- History and making of Constitution
- Fundamental Rights and Duties  
- Directive Principles of State Policy
- Amendment Process
- Preamble and its significance

⚖️ **Constitutional Bodies:**
- Supreme Court and High Courts
- President and Governor
- Parliament and State Legislatures

🎯 **Suggested Questions:**
- "Who is the Father of Indian Constitution?"
- "What are the Fundamental Rights?"
- "Explain the Preamble of Constitution"
- "How can Constitution be amended?"

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
        score = data.get('score')
        
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
        from datetime import datetime, timedelta
        
        # Get feedback trends
        recent_feedback = SearchHistory.query.filter(
            SearchHistory.feedback_score > 0,
            SearchHistory.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(SearchHistory.timestamp.desc()).limit(100).all()
        
        if len(recent_feedback) < 10:
            return {"status": "Learning from interactions", "progress": 0, "current_avg": 0}
        
        # Calculate improvement trend
        first_half = recent_feedback[len(recent_feedback)//2:]
        second_half = recent_feedback[:len(recent_feedback)//2]
        
        avg_first = sum(f.feedback_score for f in first_half) / len(first_half)
        avg_second = sum(f.feedback_score for f in second_half) / len(second_half)
        
        improvement = ((avg_second - avg_first) / avg_first) * 100 if avg_first > 0 else 0
        
        return {
            "status": "Improving" if improvement > 5 else "Stable" if improvement > -5 else "Learning",
            "progress": round(improvement, 2),
            "current_avg": round(avg_second, 2)
        }
        
    except Exception as e:
        return {"status": "Analyzing performance", "progress": 0, "current_avg": 0}

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

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Constitution Chatbot API is running!',
        'version': '1.0.0',
        'features': [
            'Indian Constitution Knowledge Base',
            'Search History with Persistence',
            'Self-Learning with Feedback System',
            'Class-Specific Content (8th-12th)',
            'Performance Analytics'
        ]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_knowledge_base()
    app.run(debug=True, port=5000, host='0.0.0.0')