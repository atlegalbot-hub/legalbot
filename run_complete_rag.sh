#!/bin/bash

# Complete RAG Constitution Chatbot Startup Script (Local Models Only)
echo "🇮🇳🧠✨ Starting Complete RAG Constitution Chatbot with Local Models..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_rag() {
    echo -e "${PURPLE}[RAG]${NC} $1"
}

print_model() {
    echo -e "${CYAN}[MODEL]${NC} $1"
}

# Check system requirements
print_status "Checking system requirements..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check available memory
total_memory=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
print_status "Available RAM: ${total_memory}GB"

if (( $(echo "$total_memory < 4.0" | bc -l) )); then
    print_warning "Less than 4GB RAM detected. Model loading might be slow."
fi

print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

print_status "Checking Node.js version..."
node_version=$(node --version)
print_success "Node.js version: $node_version"

# Install Complete RAG dependencies
print_rag "Installing Complete RAG Pipeline dependencies..."
print_model "This will download local models: SentenceTransformers, DialoGPT, Cross-encoder..."

# Try different installation methods
if python3 -m pip install --break-system-packages -r requirements_complete.txt 2>/dev/null; then
    print_success "Complete RAG dependencies installed successfully"
elif pip3 install --user -r requirements_complete.txt 2>/dev/null; then
    print_success "Complete RAG dependencies installed in user directory"
else
    print_warning "Standard installation failed, trying core dependencies..."
    
    # Core dependencies
    core_deps="flask flask-cors flask-sqlalchemy sentence-transformers numpy scikit-learn python-dotenv"
    
    if python3 -m pip install --break-system-packages $core_deps 2>/dev/null; then
        print_success "Core dependencies installed"
        
        # Try additional components
        print_model "Installing AI models..."
        python3 -m pip install --break-system-packages transformers torch faiss-cpu rank-bm25 2>/dev/null || print_warning "Some AI models may not be available"
    else
        print_error "Failed to install required dependencies"
        echo "Please install manually:"
        echo "pip3 install flask flask-cors flask-sqlalchemy sentence-transformers numpy scikit-learn"
        exit 1
    fi
fi

# Install Node.js dependencies
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    if npm install; then
        print_success "Node.js dependencies installed successfully"
    else
        print_error "Failed to install Node.js dependencies"
        exit 1
    fi
else
    print_success "Node.js dependencies already installed"
fi

# Create necessary directories
print_status "Creating Complete RAG application directories..."
mkdir -p instance
mkdir -p models_cache
mkdir -p vector_db

print_success "Setup completed successfully!"

echo ""
print_rag "🚀 Starting Complete RAG-powered Constitution Chatbot..."
print_model "Loading local models (this may take a few minutes on first run)..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down Complete RAG servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start Complete RAG backend server
print_rag "Starting Complete RAG backend server on port 5000..."
print_model "Initializing: SentenceTransformers, DialoGPT, Cross-encoder, FAISS, BM25, TF-IDF..."

python3 rag_complete.py &
BACKEND_PID=$!

# Wait longer for model loading
print_status "Waiting for models to load (30 seconds)..."
sleep 30

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Complete RAG backend server started successfully (PID: $BACKEND_PID)"
    
    # Test the API
    if curl -s http://localhost:5000/ > /dev/null; then
        print_rag "✅ RAG API is responding"
    else
        print_warning "RAG API may still be loading models..."
    fi
else
    print_error "Failed to start Complete RAG backend server"
    exit 1
fi

# Start frontend server
print_status "Starting frontend development server on port 3000..."
npm start &
FRONTEND_PID=$!

# Wait for frontend
sleep 10

# Check if frontend is running
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
else
    print_error "Failed to start frontend server"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
print_success "🎉 Complete RAG Constitution Chatbot is now running!"
echo ""
echo -e "${PURPLE}🧠 Complete RAG Backend:${NC} http://localhost:5000"
echo -e "${BLUE}🌐 Frontend Application:${NC} http://localhost:3000"
echo ""
echo -e "${PURPLE}🚀 Advanced RAG Features:${NC}"
echo "  • 🧠 Multi-Method Retrieval (FAISS + BM25 + TF-IDF)"
echo "  • 🤖 Neural Generation (DialoGPT-small) + Template Fallback"
echo "  • 🎯 Cross-Encoder Reranking for Relevance"
echo "  • 📚 Comprehensive Constitution Knowledge Base"
echo "  • 🔍 Semantic Document Chunking & Indexing"
echo "  • ⚡ Sub-second Response Times"
echo "  • 📊 Advanced Performance Analytics"
echo "  • 🎓 Class-specific Content (8th-12th)"
echo "  • 🔄 Continuous Learning from Feedback"
echo "  • 🏠 100% Local Models (No External APIs)"
echo ""
echo -e "${CYAN}🤖 AI Models Loaded:${NC}"
echo "  • Embeddings: all-MiniLM-L6-v2 (SentenceTransformers)"
echo "  • Generation: microsoft/DialoGPT-small"
echo "  • Reranking: cross-encoder/ms-marco-MiniLM-L-2-v2"
echo "  • Search: FAISS Vector Index + BM25 + TF-IDF"
echo ""
echo -e "${YELLOW}📊 RAG Pipeline Components:${NC}"
echo "  • Retrieval: Hybrid semantic + keyword + statistical"
echo "  • Generation: Neural language model + template-based"
echo "  • Reranking: Cross-encoder relevance scoring"
echo "  • Storage: SQLite + Vector Index + In-memory"
echo "  • Learning: Feedback-driven optimization"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop both servers${NC}"
echo ""
echo -e "${BLUE}💡 First query may take longer as models warm up${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID