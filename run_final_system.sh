#!/bin/bash

# FINAL COMPLETE Educational Law & Constitution RAG Chatbot Startup Script
# Complete system with all requested features for 8th-12th grade students
# 100% FREE, Scenario-Based Learning, Constitutional Education, Self-Learning

echo "🎓⚖️ Starting COMPLETE Educational Law & Constitution RAG Chatbot..."

# Enhanced colors for better visual feedback
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BOLD}${BLUE}[SYSTEM]${NC} $1"
}

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

print_feature() {
    echo -e "${BOLD}${GREEN}[FEATURE]${NC} $1"
}

# System header
clear
echo ""
echo -e "${BOLD}${PURPLE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${PURPLE}🎓⚖️  COMPLETE EDUCATIONAL LAW & CONSTITUTION RAG CHATBOT  ⚖️🎓${NC}"
echo -e "${BOLD}${PURPLE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}${CYAN}🏛️ Perfect for 8th-12th Grade Students Learning Indian Constitution & Law System${NC}"
echo -e "${BOLD}${GREEN}💰 100% FREE • 🎭 Scenario-Based Learning • 🛡️ Safe & Educational • 🧠 Self-Learning${NC}"
echo ""
echo -e "${BOLD}${BLUE}📚 COMPLETE FEATURES:${NC}"
echo -e "${GREEN}  ✅ Advanced RAG Pipeline with FAISS, BM25, TF-IDF Search${NC}"
echo -e "${GREEN}  ✅ Interactive Scenario-Based Learning ('What if I...' questions)${NC}"
echo -e "${GREEN}  ✅ Age-Appropriate Responses (Child/Teen/Adult)${NC}"
echo -e "${GREEN}  ✅ PDF Upload & Processing (Constitution, Law Books)${NC}"
echo -e "${GREEN}  ✅ Search History & Learning Analytics${NC}"
echo -e "${GREEN}  ✅ Self-Learning & Response Optimization${NC}"
echo -e "${GREEN}  ✅ Constitutional Education & Rights Learning${NC}"
echo -e "${GREEN}  ✅ Educational Safety & Responsible AI${NC}"
echo ""

# Educational notice
print_warning "📋 EDUCATIONAL PURPOSE ONLY"
echo "This chatbot is designed for educational learning about laws, constitution, and civic responsibility."
echo "It teaches students about consequences through safe, interactive scenarios."
echo "Always consult legal professionals for real legal situations."
echo ""

# System requirements check
print_header "Checking System Requirements..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

# Check available memory
available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}' 2>/dev/null || echo "Unknown")
print_status "Available memory: ${available_memory}GB"

# Install dependencies
print_edu "Installing Complete Educational Law RAG Dependencies..."
print_law "All components are FREE, open-source, and safe for educational use!"

echo ""
echo -e "${BOLD}${BLUE}📦 Installing Advanced Educational Components:${NC}"
echo "  🧠 SentenceTransformers (Advanced AI embeddings)"
echo "  🔍 FAISS (Vector search for semantic understanding)"
echo "  📄 PyPDF2 + pdfplumber (Constitution & law book processing)"
echo "  🎭 GPT-2 (Educational response generation)"
echo "  ⚖️ Advanced RAG pipeline (Multi-method search)"
echo "  📊 Learning analytics & self-improvement"
echo "  🛡️ Educational safety & age-appropriate responses"
echo ""

# Enhanced installation with better error handling
install_dependencies() {
    local method=$1
    local desc=$2
    
    print_status "Trying installation method: $desc"
    
    case $method in
        "pip_break")
            python3 -m pip install --break-system-packages -r requirements_final.txt 2>/dev/null
            ;;
        "pip_user")
            pip3 install --user -r requirements_final.txt 2>/dev/null
            ;;
        "pip_normal")
            pip install -r requirements_final.txt 2>/dev/null
            ;;
        "pip3_user")
            pip3 install --user -r requirements_final.txt 2>/dev/null
            ;;
        "core_only")
            python3 -m pip install --break-system-packages flask flask-cors flask-sqlalchemy PyPDF2 pdfplumber sentence-transformers transformers torch numpy scikit-learn nltk faiss-cpu rank-bm25 2>/dev/null
            ;;
    esac
}

# Try different installation methods
installation_success=false

methods=(
    "pip_break:Python pip with system packages override"
    "pip_user:Python pip user installation"
    "pip_normal:Standard pip installation"
    "pip3_user:Pip3 user installation"
    "core_only:Core components only"
)

for method_desc in "${methods[@]}"; do
    method="${method_desc%%:*}"
    desc="${method_desc##*:}"
    
    if install_dependencies "$method" "$desc"; then
        print_success "$desc - Installation successful!"
        installation_success=true
        break
    else
        print_warning "$desc - Failed, trying next method..."
    fi
done

if [ "$installation_success" = false ]; then
    print_error "All automatic installation methods failed."
    echo ""
    echo -e "${BOLD}${YELLOW}📋 Manual Installation Required:${NC}"
    echo "Please run these commands manually:"
    echo ""
    echo "1. pip3 install flask flask-cors flask-sqlalchemy"
    echo "2. pip3 install PyPDF2 pdfplumber"
    echo "3. pip3 install sentence-transformers transformers torch"
    echo "4. pip3 install numpy scikit-learn nltk"
    echo "5. pip3 install faiss-cpu rank-bm25"
    echo ""
    echo "Then run this script again."
    exit 1
fi

print_success "All educational dependencies installed successfully!"

# Create necessary directories
print_status "Creating educational application directories..."
mkdir -p uploaded_pdfs
mkdir -p instance
mkdir -p educational_scenarios
mkdir -p logs
mkdir -p exports

print_success "Educational application directories created!"

# Combine Python files
print_status "Preparing complete educational system..."

# Create the main application file with all components
cat > complete_educational_system.py << 'EOF'
# Import the main application and additional components
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import main application
from final_complete_chatbot import *

# Import additional API routes
try:
    from api_routes import *
    print("✅ Additional API routes loaded")
except ImportError as e:
    print(f"⚠️ Some API routes may not be available: {e}")

# Import additional methods
try:
    exec(open('additional_methods.py').read())
    print("✅ Additional methods loaded")
except Exception as e:
    print(f"⚠️ Some advanced features may not be available: {e}")

if __name__ == '__main__':
    print("🚀 Starting Complete Educational Law & Constitution RAG Chatbot...")
    print("🎓 All features loaded and ready for student education!")
    
    with app.app_context():
        db.create_all()
        complete_rag.load_existing_documents()
    
    app.run(debug=True, port=5000, host='0.0.0.0')
EOF

print_success "Complete educational system prepared!"

echo ""
print_edu "🚀 Starting Complete Educational Law & Constitution Chatbot..."
print_law "Loading: RAG Pipeline, Scenarios, Self-Learning, Analytics..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down Complete Educational Law Chatbot..."
    kill $BACKEND_PID 2>/dev/null
    print_success "Educational system stopped safely."
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start the complete educational system
print_edu "Initializing Complete Educational RAG Backend on port 5000..."
print_law "Loading: AI Models, Educational Scenarios, Constitutional Knowledge..."

python3 complete_educational_system.py &
BACKEND_PID=$!

# Enhanced startup monitoring
print_status "Loading educational models and preparing system (45 seconds)..."

for i in {1..45}; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Educational system startup failed!"
        exit 1
    fi
    
    case $((i % 15)) in
        5) echo -n "🧠 Loading AI models... " ;;
        10) echo -n "📚 Preparing educational scenarios... " ;;
        0) echo -n "⚖️ Initializing legal knowledge base... " ;;
        *) echo -n "." ;;
    esac
    
    sleep 1
done

echo ""

# Verify backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Complete Educational Law backend started successfully (PID: $BACKEND_PID)"
    
    # Test the API
    sleep 5
    if curl -s http://localhost:5000/ > /dev/null 2>&1; then
        print_success "✅ Educational Law API is responding and ready!"
    else
        print_warning "⚠️ Educational API may still be loading AI models..."
    fi
else
    print_error "❌ Failed to start Complete Educational Law backend"
    exit 1
fi

echo ""
echo -e "${BOLD}${GREEN}🎉 COMPLETE EDUCATIONAL LAW & CONSTITUTION CHATBOT IS NOW RUNNING!${NC}"
echo ""
echo -e "${BOLD}${PURPLE}🌐 Access Your Complete Educational Chatbot:${NC} ${BOLD}${CYAN}http://localhost:5000${NC}"
echo ""
echo -e "${BOLD}${BLUE}🎓 COMPLETE EDUCATIONAL FEATURES AVAILABLE:${NC}"
echo ""
echo -e "${CYAN}📚 Document Processing & Analysis:${NC}"
echo "  • Advanced PDF upload with intelligent text extraction"
echo "  • Constitutional documents, law books, legal guides"
echo "  • Auto-classification (Constitution/Law/Educational)"
echo "  • Smart text chunking with content-type detection"
echo ""
echo -e "${CYAN}🎭 Interactive Scenario-Based Learning:${NC}"
echo "  • 'What happens if...' educational scenarios"
echo "  • Age-appropriate consequences (Child/Teen/Adult)"
echo "  • Real legal scenarios with educational focus"
echo "  • Property theft, cyberbullying, traffic violations"
echo "  • Privacy rights, academic integrity, substance abuse"
echo ""
echo -e "${CYAN}🧠 Advanced AI & Search:${NC}"
echo "  • Multi-method RAG: FAISS + BM25 + TF-IDF"
echo "  • Semantic understanding with SentenceTransformers"
echo "  • GPT-2 neural response generation"
echo "  • Educational template fallback system"
echo ""
echo -e "${CYAN}📊 Learning Analytics & Self-Improvement:${NC}"
echo "  • Comprehensive search history preservation"
echo "  • Learning progress tracking and analytics"
echo "  • Self-learning from user feedback"
echo "  • Response optimization over time"
echo "  • Educational effectiveness monitoring"
echo ""
echo -e "${CYAN}⚖️ Constitutional & Legal Education:${NC}"
echo "  • Indian Constitution deep-dive learning"
echo "  • Fundamental rights and duties education"
echo "  • Legal procedures and civic responsibilities"
echo "  • Age-appropriate legal consequence education"
echo ""
echo -e "${CYAN}🛡️ Educational Safety & Responsibility:${NC}"
echo "  • Educational purpose disclaimers on all responses"
echo "  • Age-appropriate content filtering"
echo "  • No promotion of illegal activities"
echo "  • Professional legal consultation recommendations"
echo "  • Positive citizenship and character building focus"
echo ""
echo -e "${BOLD}${GREEN}🎯 EXAMPLE EDUCATIONAL INTERACTIONS:${NC}"
echo ""
echo -e "${YELLOW}🎭 Scenario-Based Learning:${NC}"
echo "  • 'What happens if I take someone's bicycle without permission?'"
echo "  • 'What are the consequences of cyberbullying someone online?'"
echo "  • 'What if I drive a motorbike without a license?'"
echo "  • 'What happens if I share someone's private photos?'"
echo ""
echo -e "${YELLOW}🏛️ Constitutional Education:${NC}"
echo "  • 'What are my fundamental rights as a student?'"
echo "  • 'Explain Article 21 of the Indian Constitution'"
echo "  • 'What is the Right to Education?'"
echo "  • 'How does the Constitution protect children?'"
echo ""
echo -e "${YELLOW}📚 Legal Learning:${NC}"
echo "  • 'What laws protect me from bullying?'"
echo "  • 'How can I protect my privacy online?'"
echo "  • 'What should I do if someone harasses me?'"
echo "  • 'How can I be a good citizen in my community?'"
echo ""
echo -e "${BOLD}${BLUE}👨‍🏫 FOR EDUCATORS & PARENTS:${NC}"
echo ""
echo -e "${GREEN}🎓 Educational Benefits:${NC}"
echo "  • Safe environment for learning about laws and consequences"
echo "  • Age-appropriate content with educational disclaimers"
echo "  • Character building through legal education"
echo "  • Civic responsibility and citizenship development"
echo "  • Interactive learning more engaging than traditional methods"
echo ""
echo -e "${GREEN}📋 Curriculum Integration:${NC}"
echo "  • Supports civics and social studies education"
echo "  • Constitutional literacy development"
echo "  • Legal awareness and rights education"
echo "  • Discussion starters for classroom conversations"
echo "  • Assessment tool for legal knowledge"
echo ""
echo -e "${GREEN}🔒 Safety Assurance:${NC}"
echo "  • 100% educational focus with clear disclaimers"
echo "  • No encouragement of illegal activities"
echo "  • Professional guidance recommendations"
echo "  • Age-appropriate response filtering"
echo "  • Positive learning outcomes emphasis"
echo ""
echo -e "${BOLD}${PURPLE}🔒 PRIVACY & SAFETY:${NC}"
echo "  • 100% Local processing (no external data sharing)"
echo "  • Educational safety with age-appropriate content"
echo "  • No promotion of illegal activities"
echo "  • Focus on positive learning outcomes"
echo "  • Professional consultation recommendations"
echo ""
echo -e "${BOLD}${CYAN}💡 EDUCATIONAL USAGE TIPS:${NC}"
echo "  • Upload constitutional and legal textbooks for better responses"
echo "  • Select appropriate age group for tailored guidance"
echo "  • Ask scenario-based questions starting with 'What if...'"
echo "  • Explore different legal topics and constitutional rights"
echo "  • Use learning analytics to track educational progress"
echo "  • Encourage responsible citizenship through law education"
echo ""
echo -e "${BOLD}${GREEN}🎯 LEARNING OUTCOMES:${NC}"
echo "  • Enhanced constitutional and legal literacy"
echo "  • Better understanding of rights and responsibilities"
echo "  • Improved decision-making through consequence awareness"
echo "  • Stronger civic values and character development"
echo "  • Prevention of problems through early education"
echo ""
echo -e "${BOLD}${RED}Press Ctrl+C to stop the educational server${NC}"
echo ""
echo -e "${BOLD}${BLUE}🎓 Remember: Education is the best foundation for a responsible, law-abiding life!${NC}"
echo -e "${BOLD}${GREEN}📚 Every question you ask builds your knowledge and character!${NC}"
echo ""

# Real-time system monitoring
monitor_system() {
    while true; do
        sleep 30
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Educational system unexpectedly stopped!"
            exit 1
        fi
    done
}

# Start monitoring in background
monitor_system &
MONITOR_PID=$!

# Wait for the main process
wait $BACKEND_PID

# Clean up monitor
kill $MONITOR_PID 2>/dev/null

print_success "Complete Educational Law & Constitution RAG Chatbot session ended."
echo "Thank you for using our educational system for legal learning! 🎓⚖️"