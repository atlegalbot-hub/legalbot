#!/bin/bash

# Constitution Chatbot with RAG Pipeline Startup Script
echo "🇮🇳🧠 Starting Constitution Chatbot with RAG Pipeline..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_success "Python version: $python_version"

print_status "Checking Node.js version..."
node_version=$(node --version)
print_success "Node.js version: $node_version"

# Install RAG dependencies
print_rag "Installing RAG Pipeline dependencies..."
if python3 -m pip install --break-system-packages -r rag_requirements.txt 2>/dev/null || pip3 install --user -r rag_requirements.txt; then
    print_success "RAG dependencies installed successfully"
else
    print_warning "Some RAG dependencies failed to install, trying core dependencies..."
    if python3 -m pip install --break-system-packages flask flask-cors flask-sqlalchemy sentence-transformers faiss-cpu numpy scikit-learn python-dotenv 2>/dev/null; then
        print_success "Core RAG dependencies installed"
    else
        print_error "Failed to install required dependencies"
        exit 1
    fi
fi

# Install Node.js dependencies if not already installed
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
print_status "Creating RAG application directories..."
mkdir -p instance
mkdir -p chroma_db

print_success "Setup completed successfully!"

echo ""
print_rag "🚀 Starting RAG-powered Constitution Chatbot..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down RAG servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start RAG backend server
print_rag "Starting RAG backend server on port 5000..."
python3 rag_app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "RAG backend server started successfully (PID: $BACKEND_PID)"
else
    print_error "Failed to start RAG backend server"
    exit 1
fi

# Start frontend server
print_status "Starting frontend development server on port 3000..."
npm start &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Check if frontend is running
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
else
    print_error "Failed to start frontend server"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
print_success "🎉 Constitution Chatbot with RAG Pipeline is now running!"
echo ""
echo -e "${PURPLE}🧠 RAG Backend API:${NC} http://localhost:5000"
echo -e "${BLUE}🌐 Frontend App:${NC} http://localhost:3000"
echo ""
echo -e "${PURPLE}🔥 RAG Features:${NC}"
echo "  • 🧠 Advanced Retrieval-Augmented Generation"
echo "  • 🔍 Hybrid Search (Dense Vector + Sparse Keyword)"
echo "  • 📚 Document Chunking & Semantic Indexing"
echo "  • 🎯 Context-Aware Response Generation"
echo "  • 📊 Real-time Relevance Scoring"
echo "  • 🚀 FAISS Vector Database + BM25 Ranking"
echo "  • 🎓 Class-specific Content (8th-12th)"
echo "  • 📈 Advanced Learning Analytics"
echo "  • ⚡ Fast Similarity Search"
echo "  • 🔄 Continuous Learning from Feedback"
echo ""
echo -e "${YELLOW}📊 RAG Pipeline Components:${NC}"
echo "  • Retrieval: FAISS + BM25 Hybrid Search"
echo "  • Embeddings: SentenceTransformer (all-MiniLM-L6-v2)"
echo "  • Generation: Context-aware templates"
echo "  • Reranking: Query-document relevance scoring"
echo "  • Storage: SQLite + Vector Index"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID