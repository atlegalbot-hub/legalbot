# Constitution Chatbot for Students 🇮🇳

An intelligent chatbot designed to help students of classes 8th-12th learn about the Indian Constitution and legal system. Features advanced AI learning capabilities, comprehensive search history, and performance analytics.

## 🌟 Features

### 📚 Educational Content
- **Comprehensive Knowledge Base**: Covers all aspects of Indian Constitution
- **Class-Specific Content**: Tailored responses for different grade levels (8th-12th)
- **Scenario-Based Learning**: Real-world examples and case studies
- **Historical Context**: Complete timeline of Constitutional development

### 🤖 AI Capabilities
- **Self-Learning System**: Improves responses based on user feedback
- **Vector Search**: Advanced semantic search using sentence transformers
- **Context-Aware Responses**: Understands query intent and provides relevant answers
- **Feedback Loop**: Continuous learning from user interactions

### 📊 Analytics & Tracking
- **Performance Metrics**: Track accuracy, satisfaction rates, and usage patterns
- **Learning Progress**: Monitor AI improvement over time
- **User Analytics**: Understand engagement and learning patterns
- **Real-time Optimization**: Live performance tracking

### 💾 Data Management
- **Complete Search History**: All conversations preserved with timestamps
- **Advanced Search**: Find previous conversations quickly
- **Export Functionality**: Download chat history for offline review
- **User Sessions**: Persistent user identification across sessions

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

2. **Initialize the Database**
```bash
python app.py
```
The database will be automatically created on first run.

3. **Start the Backend Server**
```bash
python app.py
```
Server runs on `http://localhost:5000`

### Frontend Setup

1. **Install Node Dependencies**
```bash
npm install
```

2. **Start the Development Server**
```bash
npm start
```
Frontend runs on `http://localhost:3000`

## 📖 Constitutional Knowledge Base

### Covered Topics

#### 📜 Historical Foundation
- **Making of Constitution**: 1946-1950 timeline
- **Key Personalities**: Dr. B.R. Ambedkar, Nehru, Patel
- **Constituent Assembly**: Formation and proceedings
- **Adoption Process**: November 26, 1949 to January 26, 1950

#### ⚖️ Fundamental Rights (Articles 12-35)
1. **Right to Equality** (Articles 14-18)
2. **Right to Freedom** (Articles 19-22)
3. **Right against Exploitation** (Articles 23-24)
4. **Right to Freedom of Religion** (Articles 25-28)
5. **Cultural and Educational Rights** (Articles 29-30)
6. **Right to Constitutional Remedies** (Article 32)

#### 📋 Directive Principles (Articles 36-51)
- **Socialist Principles**: Economic equality
- **Gandhian Principles**: Village panchayats, khadi
- **Liberal Principles**: Uniform civil code, separation of powers

#### 🤝 Fundamental Duties (Article 51A)
- 11 duties added by 42nd Amendment
- Civic responsibilities and national obligations

#### 📝 Amendment Process (Article 368)
- **Simple Majority**: Basic legislative changes
- **Special Majority**: Constitutional provisions
- **Special Majority + Ratification**: Federal structure changes

## 🔧 API Endpoints

### Chat Functionality
- `POST /api/chat` - Send query and get AI response
- `POST /api/feedback` - Submit feedback for learning
- `GET /api/search` - Search chat history

### History Management
- `GET /api/history/{user_id}` - Get user's chat history
- `GET /api/metrics` - Get performance analytics

## 📊 Self-Learning Mechanism

### How It Works
1. **User Interaction**: Students ask questions about Constitution
2. **AI Response**: System provides contextual, class-appropriate answers
3. **Feedback Collection**: Users rate responses (1-5 stars)
4. **Learning Loop**: AI adjusts based on feedback patterns
5. **Optimization Tracking**: Continuous monitoring of improvement

### Learning Indicators
- **Response Accuracy**: Based on user ratings
- **Satisfaction Rate**: Percentage of positive feedback
- **Topic Coverage**: Knowledge base effectiveness
- **Engagement Metrics**: User interaction patterns

### Optimization Features
- **Vector Similarity Search**: Find most relevant constitutional content
- **Contextual Response Generation**: Tailor answers to student's class level
- **Feedback Analysis**: Identify areas for improvement
- **Performance Metrics**: Track learning progress over time

## 🎨 Frontend Features

### Modern UI/UX
- **Responsive Design**: Works on all devices
- **Gradient Backgrounds**: Beautiful visual design
- **Smooth Animations**: Framer Motion animations
- **Intuitive Navigation**: Easy-to-use interface

### Interactive Components
- **Real-time Chat**: Instant responses with typing indicators
- **Search History**: Quick access to previous conversations
- **Class Selection**: Grade-appropriate content filtering
- **Feedback System**: Easy rating and improvement mechanism

### Analytics Dashboard
- **Performance Charts**: Visual representation of metrics
- **Learning Progress**: AI improvement tracking
- **Usage Statistics**: Student engagement analytics
- **Optimization Insights**: Actionable improvement data

## 📱 Usage Guide

### For Students
1. **Select Your Class**: Choose your grade level (8th-12th)
2. **Ask Questions**: Type any Constitution-related query
3. **Rate Responses**: Help improve the AI by rating answers
4. **Review History**: Access all previous conversations
5. **Track Progress**: See how the AI is learning from your feedback

### Sample Questions
- "Who is the Father of Indian Constitution?"
- "What are Fundamental Rights?"
- "Explain the Preamble"
- "How can the Constitution be amended?"
- "What is the difference between Fundamental Rights and Duties?"

## 🔒 Data Privacy
- **Local Storage**: All data stored locally
- **No External APIs**: No data sent to third parties
- **User Anonymization**: Users identified by random IDs
- **Secure Sessions**: Safe conversation management

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: AI embeddings for search
- **CORS**: Cross-origin resource sharing

### Frontend
- **React 18**: Modern UI framework
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Axios**: HTTP client
- **React Router**: Navigation
- **Lucide React**: Beautiful icons

### AI/ML
- **Sentence Transformers**: Text embeddings
- **Vector Search**: Semantic similarity
- **Feedback Learning**: Continuous improvement
- **Performance Analytics**: Learning metrics

## 📈 Performance Monitoring

### Key Metrics
- **Total Queries**: Number of questions asked
- **Average Rating**: User satisfaction score
- **Response Time**: AI processing speed
- **Learning Rate**: Improvement over time

### Optimization Tracking
- **Feedback Trends**: User satisfaction patterns
- **Topic Performance**: Subject-wise accuracy
- **Usage Analytics**: Student engagement metrics
- **System Health**: Technical performance indicators

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License
This project is open source and available under the MIT License.

## 🙏 Acknowledgments
- **Indian Constitution**: Source of all educational content
- **Dr. B.R. Ambedkar**: Father of Indian Constitution
- **Open Source Community**: Libraries and frameworks used

---

**Made with ❤️ for Indian students learning about their Constitution**