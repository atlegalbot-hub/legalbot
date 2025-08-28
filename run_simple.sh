#!/bin/bash

# Constitution Chatbot Startup Script (Simplified Version)
echo "🇮🇳 Starting Constitution Chatbot (Simplified Version)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

print_status "Installing core Python dependencies..."
if python3 -m pip install --break-system-packages flask flask-cors flask-sqlalchemy python-dotenv 2>/dev/null || pip3 install --user flask flask-cors flask-sqlalchemy python-dotenv; then
    print_success "Python dependencies installed successfully"
else
    print_error "Failed to install Python dependencies"
    exit 1
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
print_status "Creating application directories..."
mkdir -p instance

print_success "Setup completed successfully!"

echo ""
echo "🚀 Starting the application..."
echo ""

# Function to handle cleanup
cleanup() {
    print_warning "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start backend server (simplified version)
print_status "Starting backend server on port 5000..."
python3 app_simple.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Backend server started successfully (PID: $BACKEND_PID)"
else
    print_error "Failed to start backend server"
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
print_success "🎉 Constitution Chatbot is now running!"
echo ""
echo -e "${BLUE}📊 Backend API:${NC} http://localhost:5000"
echo -e "${BLUE}🌐 Frontend App:${NC} http://localhost:3000"
echo ""
echo -e "${YELLOW}📚 Features:${NC}"
echo "  • ✅ Comprehensive Constitution knowledge base"
echo "  • ✅ Self-learning AI with feedback system"
echo "  • ✅ Complete search history with analytics"
echo "  • ✅ Class-specific content (8th-12th)"
echo "  • ✅ Performance optimization tracking"
echo "  • ✅ Beautiful modern UI with animations"
echo "  • ✅ Responsive design for all devices"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID