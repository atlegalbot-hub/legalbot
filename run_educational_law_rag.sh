#!/bin/bash

# Educational Law & Constitution RAG Chatbot Startup Script
# Teaches students about laws, rights, and consequences through interactive scenarios
# 100% FREE and Educationally Responsible!

echo "🎓⚖️ Starting Educational Law & Constitution RAG Chatbot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_edu() {
    echo -e "${PURPLE}[EDUCATION]${NC} $1"
}

print_law() {
    echo -e "${CYAN}[LAW]${NC} $1"
}

# Educational header
echo ""
echo "🏛️ Educational Law & Constitution Learning Platform"
echo "📚 Teaching Students About Rights, Laws, and Civic Responsibility"
echo "🎭 Interactive Scenario-Based Learning"
echo "💰 100% FREE • 🔒 Safe • 🎓 Educational Focus"
echo ""

# Important educational notice
print_warning "📋 EDUCATIONAL PURPOSE ONLY"
echo "This chatbot is designed for educational learning about laws and constitution."
echo "It teaches students about consequences through safe, educational scenarios."
echo "Always consult legal professionals for real legal situations."
echo ""

# Check system requirements
print_status "Checking system requirements..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

# Install educational law dependencies
print_edu "Installing Educational Law RAG dependencies..."
print_law "All components are FREE and safe for educational use!"

echo ""
echo "📦 Installing Educational Components:"
echo "  • Flask (Web interface for safe interaction)"
echo "  • PyPDF2 + pdfplumber (Constitution & law book processing)"
echo "  • SentenceTransformers (Educational content search)"
echo "  • GPT-2 (Educational response generation)"
echo "  • Educational scenario database"
echo ""

# Try installation
if python3 -m pip install --break-system-packages -r requirements_free.txt 2>/dev/null; then
    print_success "All educational dependencies installed successfully!"
elif pip3 install --user -r requirements_free.txt 2>/dev/null; then
    print_success "Educational dependencies installed in user directory!"
else
    print_warning "Standard installation failed, trying core educational components..."
    
    core_deps="flask flask-cors flask-sqlalchemy PyPDF2 pdfplumber sentence-transformers transformers torch numpy scikit-learn nltk"
    
    if python3 -m pip install --break-system-packages $core_deps 2>/dev/null; then
        print_success "Core educational components installed!"
        
        print_edu "Installing additional AI models for better learning..."
        python3 -m pip install --break-system-packages faiss-cpu rank-bm25 2>/dev/null || print_warning "Some AI components may not be available"
    else
        print_error "Installation failed. Please install manually:"
        echo ""
        echo "Manual installation commands:"
        echo "pip3 install flask flask-cors flask-sqlalchemy"
        echo "pip3 install PyPDF2 pdfplumber sentence-transformers"
        echo "pip3 install transformers torch numpy scikit-learn nltk"
        echo ""
        exit 1
    fi
fi

# Create educational directories
print_status "Creating educational application directories..."
mkdir -p uploaded_pdfs
mkdir -p instance
mkdir -p educational_scenarios

print_success "Educational setup completed successfully!"

echo ""
print_edu "🚀 Starting Educational Law & Constitution Chatbot..."
print_law "Loading educational scenarios and legal knowledge base..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down Educational Law Chatbot..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start the educational law backend
print_edu "Starting Educational Law RAG backend on port 5000..."
print_law "Initializing: Constitutional knowledge, Legal scenarios, Educational content..."

python3 educational_law_rag_chatbot.py &
BACKEND_PID=$!

# Wait for educational models to load
print_status "Loading educational models and scenarios (30 seconds)..."
sleep 30

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Educational Law backend started successfully (PID: $BACKEND_PID)"
    
    # Test the educational API
    if curl -s http://localhost:5000/ > /dev/null; then
        print_edu "✅ Educational Law API is responding"
    else
        print_warning "Educational API may still be loading..."
    fi
else
    print_error "Failed to start Educational Law backend"
    exit 1
fi

echo ""
print_success "🎉 Educational Law & Constitution Chatbot is now running!"
echo ""
echo -e "${PURPLE}🌐 Access your Educational Chatbot:${NC} http://localhost:5000"
echo ""
echo -e "${CYAN}🎓 Educational Features Available:${NC}"
echo "  • 📚 Constitutional Learning with PDF Upload"
echo "  • 🎭 Interactive Legal Scenarios for Students"
echo "  • 👶👦👧 Age-Appropriate Guidance (Child/Teen/Adult)"
echo "  • ⚖️ Educational Law Consequences Learning"
echo "  • 🏛️ Indian Constitution Deep Dive"
echo "  • 📖 Rights and Duties Education"
echo "  • 🤝 Civic Responsibility Teaching"
echo "  • 🔍 Legal Document Search and Analysis"
echo ""
echo -e "${BLUE}📚 Educational Content Types:${NC}"
echo "  • Constitutional Rights and Duties"
echo "  • Legal Consequences and Punishments"
echo "  • Juvenile Justice Act provisions"
echo "  • Scenario-based learning examples"
echo "  • Age-appropriate legal guidance"
echo ""
echo -e "${GREEN}🎭 Example Educational Scenarios:${NC}"
echo "  • 'What happens if I take someone's bicycle?'"
echo "  • 'What are the consequences of cyberbullying?'"
echo "  • 'What if I drive without a license?'"
echo "  • 'What happens if I damage public property?'"
echo "  • 'What are my fundamental rights?'"
echo ""
echo -e "${YELLOW}👨‍🏫 For Educators & Parents:${NC}"
echo "  • Safe, educational approach to teaching laws"
echo "  • Age-appropriate content filtering"
echo "  • Focus on rehabilitation and learning"
echo "  • Constitutional education emphasis"
echo "  • Civic responsibility building"
echo ""
echo -e "${PURPLE}🔒 Safety & Privacy:${NC}"
echo "  • 100% Local processing (no external data sharing)"
echo "  • Educational purpose disclaimers"
echo "  • Age-appropriate content"
echo "  • Focus on positive learning outcomes"
echo "  • No promotion of illegal activities"
echo ""
echo -e "${CYAN}💡 Educational Tips:${NC}"
echo "  • Upload constitution and law textbooks for better learning"
echo "  • Ask scenario-based questions starting with 'What if...'"
echo "  • Select appropriate age group for tailored guidance"
echo "  • Focus on understanding rather than memorizing"
echo "  • Use this tool alongside formal legal education"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop the educational server${NC}"
echo ""
echo -e "${BLUE}🎯 Remember: Education is the best way to prevent problems!${NC}"
echo ""

# Wait for the process
wait $BACKEND_PID