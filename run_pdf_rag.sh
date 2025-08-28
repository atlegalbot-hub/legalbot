#!/bin/bash

# FREE PDF RAG Chatbot Startup Script
# 100% Free and Open Source - Perfect for Budget-Conscious Users!

echo "💰🤖 Starting FREE PDF RAG Chatbot - Zero Cost Solution!"

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

print_free() {
    echo -e "${PURPLE}[FREE]${NC} $1"
}

print_money() {
    echo -e "${CYAN}[BUDGET]${NC} $1"
}

# Welcome message
echo ""
echo "🎉 Welcome to the FREE PDF RAG Chatbot!"
echo "💸 Total Cost: $0.00 - Everything is FREE!"
echo "🔒 Privacy: 100% Local Processing"
echo "📚 Features: Upload PDFs + AI Chat"
echo ""

# Check system requirements
print_status "Checking system requirements..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

# Check available memory
if command -v free &> /dev/null; then
    total_memory=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    print_status "Available RAM: ${total_memory}GB"
    
    if (( $(echo "$total_memory < 2.0" | bc -l 2>/dev/null || echo "0") )); then
        print_warning "Less than 2GB RAM detected. Model loading might be slower."
        print_free "Don't worry - all models are lightweight and FREE!"
    fi
fi

# Install FREE dependencies
print_free "Installing 100% FREE dependencies..."
print_money "Cost: $0.00 (All open source!)"

echo ""
echo "📦 Installing FREE components:"
echo "  • Flask (Web framework)"
echo "  • PyPDF2 + pdfplumber (PDF processing)"
echo "  • SentenceTransformers (AI embeddings)"
echo "  • GPT-2 (Text generation)"
echo "  • FAISS (Vector search)"
echo "  • NLTK (Text processing)"
echo "  • scikit-learn (ML utilities)"
echo ""

# Try different installation methods
if python3 -m pip install --break-system-packages -r requirements_free.txt 2>/dev/null; then
    print_success "All FREE dependencies installed successfully!"
elif pip3 install --user -r requirements_free.txt 2>/dev/null; then
    print_success "All FREE dependencies installed in user directory!"
else
    print_warning "Standard installation failed, trying core components..."
    
    # Core components
    core_deps="flask flask-cors flask-sqlalchemy PyPDF2 pdfplumber sentence-transformers transformers torch numpy scikit-learn nltk"
    
    if python3 -m pip install --break-system-packages $core_deps 2>/dev/null; then
        print_success "Core FREE components installed!"
        
        # Try additional components
        print_free "Installing additional FREE AI models..."
        python3 -m pip install --break-system-packages faiss-cpu rank-bm25 2>/dev/null || print_warning "Some AI components may not be available"
    else
        print_error "Installation failed. Please try manual installation:"
        echo ""
        echo "Manual installation commands:"
        echo "pip3 install flask flask-cors flask-sqlalchemy"
        echo "pip3 install PyPDF2 pdfplumber"
        echo "pip3 install sentence-transformers transformers torch"
        echo "pip3 install numpy scikit-learn nltk"
        echo ""
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating application directories..."
mkdir -p uploaded_pdfs
mkdir -p instance
mkdir -p models_cache

print_success "Setup completed successfully!"

echo ""
print_free "🚀 Starting your FREE PDF RAG Chatbot..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down FREE PDF RAG Chatbot..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start the FREE PDF RAG backend
print_free "Starting FREE PDF RAG backend server on port 5000..."
print_money "Running cost: $0.00/hour (FREE forever!)"

python3 pdf_rag_chatbot.py &
BACKEND_PID=$!

# Wait for startup
print_status "Waiting for FREE AI models to load (30 seconds)..."
sleep 30

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "FREE PDF RAG backend started successfully (PID: $BACKEND_PID)"
    
    # Test the API
    if curl -s http://localhost:5000/ > /dev/null; then
        print_free "✅ FREE RAG API is responding!"
    else
        print_warning "API may still be loading FREE models..."
    fi
else
    print_error "Failed to start FREE PDF RAG backend"
    exit 1
fi

echo ""
print_success "🎉 FREE PDF RAG Chatbot is now running!"
echo ""
echo -e "${PURPLE}🌐 Access your chatbot:${NC} http://localhost:5000"
echo ""
echo -e "${CYAN}💰 Cost Breakdown:${NC}"
echo "  • PDF Processing: FREE (PyPDF2 + pdfplumber)"
echo "  • AI Embeddings: FREE (SentenceTransformers)"
echo "  • Text Generation: FREE (GPT-2)"
echo "  • Vector Search: FREE (FAISS)"
echo "  • Web Interface: FREE (Flask)"
echo "  • Total Monthly Cost: $0.00"
echo ""
echo -e "${PURPLE}🚀 Features Available:${NC}"
echo "  • 📄 Upload Multiple PDFs"
echo "  • 🤖 AI-Powered Chat with Your Documents"
echo "  • 🔍 Multi-Method Search (Semantic + Keyword + Statistical)"
echo "  • 📊 Real-time Performance Metrics"
echo "  • 🔒 100% Private (No Data Leaves Your Machine)"
echo "  • 💾 Persistent Document Storage"
echo "  • ⚡ Fast Response Times"
echo ""
echo -e "${BLUE}📚 How to Use:${NC}"
echo "  1. Open http://localhost:5000 in your browser"
echo "  2. Upload your PDF files"
echo "  3. Start chatting with your documents!"
echo ""
echo -e "${GREEN}💡 Tips for Best Results:${NC}"
echo "  • Use text-based PDFs (not scanned images)"
echo "  • Ask specific questions about your documents"
echo "  • Upload related documents for better context"
echo "  • Try different phrasings if you don't get good results"
echo ""
echo -e "${YELLOW}⚠️  Note:${NC} First query may take longer as AI models warm up"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop the server${NC}"
echo ""

# Wait for the process
wait $BACKEND_PID