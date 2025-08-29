#!/bin/bash

# 🎓⚖️ FINAL Complete Educational Law & Constitution RAG Chatbot
# ONE-CLICK STARTUP SCRIPT - Everything You Need!

clear
echo "🎓⚖️ Starting FINAL Complete Educational Law & Constitution RAG Chatbot..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${PURPLE}🎓⚖️  FINAL COMPLETE EDUCATIONAL LAW RAG CHATBOT  ⚖️🎓${NC}"
echo -e "${BOLD}${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}${GREEN}✅ ALL YOUR REQUESTED FEATURES IMPLEMENTED:${NC}"
echo -e "${GREEN}  🎭 Scenario-Based Learning ('What if I do that crime?')${NC}"
echo -e "${GREEN}  📚 PDF Upload & Processing (Your own documents)${NC}"
echo -e "${GREEN}  📊 Complete Search History & Analytics${NC}"
echo -e "${GREEN}  🧠 Self-Learning & Response Optimization${NC}"
echo -e "${GREEN}  👶👦👧 Age-Appropriate Responses${NC}"
echo -e "${GREEN}  🏛️ Constitutional Education & Rights Learning${NC}"
echo -e "${GREEN}  💰 100% FREE & Open Source${NC}"
echo -e "${GREEN}  🎨 Beautiful Web Interface${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Install dependencies with multiple fallback methods
install_deps() {
    # Try different installation methods
    methods=(
        "python3 -m pip install --break-system-packages"
        "pip3 install --user"
        "pip install"
        "python -m pip install --user"
    )
    
    deps="flask flask-cors flask-sqlalchemy PyPDF2 pdfplumber sentence-transformers transformers torch numpy scikit-learn nltk faiss-cpu rank-bm25"
    
    for method in "${methods[@]}"; do
        echo "Trying: $method"
        if $method $deps 2>/dev/null; then
            echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
            return 0
        fi
    done
    
    echo -e "${YELLOW}⚠️ Automatic installation failed. Please install manually:${NC}"
    echo "pip3 install flask flask-cors flask-sqlalchemy PyPDF2 pdfplumber sentence-transformers transformers torch numpy scikit-learn nltk faiss-cpu rank-bm25"
    echo ""
    echo "Then run: python3 COMPLETE_FINAL_CHATBOT.py"
    return 1
}

install_deps

# Create necessary directories
mkdir -p uploaded_pdfs
mkdir -p instance

echo ""
echo -e "${BLUE}🚀 Starting Complete Educational System...${NC}"
echo ""

# Start the complete system
python3 COMPLETE_FINAL_CHATBOT.py &
BACKEND_PID=$!

# Wait for startup
echo -e "${YELLOW}⏳ Loading AI models and educational scenarios (30 seconds)...${NC}"
sleep 30

# Check if running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo ""
    echo -e "${BOLD}${GREEN}🎉 SUCCESS! Your Complete Educational Law Chatbot is Ready!${NC}"
    echo ""
    echo -e "${BOLD}${BLUE}🌐 Access Your Chatbot: http://localhost:5000${NC}"
    echo ""
    echo -e "${BOLD}${YELLOW}🎭 FEATURES READY TO USE:${NC}"
    echo ""
    echo -e "${PURPLE}📚 Document Processing:${NC}"
    echo "  • Upload PDFs: Constitution, law books, legal guides"
    echo "  • Intelligent text extraction and chunking"
    echo "  • Auto-classification of document types"
    echo ""
    echo -e "${PURPLE}🎭 Scenario-Based Learning:${NC}"
    echo "  • Ask: 'What happens if I steal something?'"
    echo "  • Ask: 'What if I cyberbully someone online?'"
    echo "  • Ask: 'What are consequences of underage drinking?'"
    echo "  • Age-appropriate responses for children/teens/adults"
    echo ""
    echo -e "${PURPLE}🧠 Advanced RAG Pipeline:${NC}"
    echo "  • FAISS semantic search with SentenceTransformers"
    echo "  • BM25 keyword search for precise matching"
    echo "  • TF-IDF statistical search for relevance"
    echo "  • GPT-2 neural generation with educational templates"
    echo ""
    echo -e "${PURPLE}📊 Learning & Analytics:${NC}"
    echo "  • Complete search history preservation"
    echo "  • Learning progress tracking"
    echo "  • Self-improvement from user feedback"
    echo "  • Educational effectiveness monitoring"
    echo ""
    echo -e "${PURPLE}🏛️ Constitutional Education:${NC}"
    echo "  • Indian Constitution deep-dive learning"
    echo "  • Fundamental rights and duties education"
    echo "  • Civic responsibility and character building"
    echo "  • Legal awareness for responsible citizenship"
    echo ""
    echo -e "${PURPLE}🛡️ Educational Safety:${NC}"
    echo "  • Age-appropriate content filtering"
    echo "  • Educational disclaimers on all responses"
    echo "  • No promotion of illegal activities"
    echo "  • Professional guidance recommendations"
    echo ""
    echo -e "${BOLD}${GREEN}🎯 PERFECT FOR:${NC}"
    echo -e "${GREEN}  👨‍🎓 Students (8th-12th grade)${NC} - Interactive legal education"
    echo -e "${GREEN}  👨‍🏫 Teachers & Educators${NC} - Curriculum support and engagement"
    echo -e "${GREEN}  👨‍👩‍👧‍👦 Parents${NC} - Safe tool for family legal discussions"
    echo -e "${GREEN}  🏫 Schools${NC} - Civics education and character building"
    echo ""
    echo -e "${BOLD}${BLUE}💡 EXAMPLE QUESTIONS TO TRY:${NC}"
    echo ""
    echo -e "${YELLOW}🎭 Scenario Questions:${NC}"
    echo '  • "What happens if I take someone'\''s bicycle without permission?"'
    echo '  • "What are the consequences of cyberbullying someone?"'
    echo '  • "What if I drive without a license?"'
    echo '  • "What happens if I damage public property?"'
    echo ""
    echo -e "${YELLOW}🏛️ Constitutional Questions:${NC}"
    echo '  • "What are my fundamental rights as a student?"'
    echo '  • "Explain Article 21 of the Indian Constitution"'
    echo '  • "What is the Right to Education?"'
    echo '  • "How does the Constitution protect children?"'
    echo ""
    echo -e "${YELLOW}📚 General Legal Questions:${NC}"
    echo '  • "What laws protect me from bullying?"'
    echo '  • "How can I protect my privacy online?"'
    echo '  • "What should I do if someone harasses me?"'
    echo '  • "How can I be a good citizen?"'
    echo ""
    echo -e "${BOLD}${RED}Press Ctrl+C to stop the educational server${NC}"
    echo ""
    echo -e "${BOLD}${GREEN}🎓 Enjoy learning about laws, rights, and civic responsibility! 🏛️${NC}"
    
    # Wait for the process
    wait $BACKEND_PID
else
    echo -e "${RED}❌ Failed to start the educational system${NC}"
    exit 1
fi