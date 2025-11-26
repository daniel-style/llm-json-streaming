#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting LLM JSON Streaming Example...${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# Setup Backend
echo -e "\n${GREEN}📦 Setting up Backend...${NC}"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing backend dependencies..."
pip install -r requirements.txt
pip install -e "$ROOT_DIR" # Install the local package in editable mode

# Start Backend in background
echo -e "${GREEN}🚀 Starting Backend Server (FastAPI)...${NC}"
python main.py &
BACKEND_PID=$!

# Setup Frontend
echo -e "\n${GREEN}📦 Setting up Frontend (pnpm)...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    pnpm install
fi

# Start Frontend in background
echo -e "${GREEN}🚀 Starting Frontend Server (Next.js)...${NC}"
pnpm dev &
FRONTEND_PID=$!

echo -e "\n${BLUE}✨ Services are running!${NC}"
echo -e "   Backend: http://localhost:8000"
echo -e "   Frontend: http://localhost:3000"
echo -e "\nPress Ctrl+C to stop both servers."

# Wait for both processes
wait

