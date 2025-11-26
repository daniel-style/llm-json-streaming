# FastAPI + Next.js LLM JSON Streaming Example

This example demonstrates how to stream structured JSON data from an LLM (Anthropic, OpenAI, or Google) using FastAPI as the backend and Next.js as the frontend.

## Structure

- `backend/`: FastAPI application using `llm-json-streaming`
- `frontend/`: Next.js application with a React component that renders the stream in real-time
- `start.sh`: Bash script to setup and run the project

## Prerequisites

- Python 3.9+
- Node.js 18+
- pnpm (install with `npm install -g pnpm`)
- API Key for Anthropic, OpenAI, or Google Gemini

## Quick Start

You can use the included `start.sh` script to automatically set up the environment and start both servers.

```bash
./start.sh
```

This script will:
1. Create a Python virtual environment in `backend/venv` (if needed)
2. Install Python dependencies (including the local `llm-json-streaming` package)
3. Install Node.js dependencies using `pnpm` (if needed)
4. Start the FastAPI backend on port 8000
5. Start the Next.js frontend on port 3000

## Manual Setup

If you prefer to run things manually without the script:

### 1. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# Install the root package in editable mode
pip install -e ../../../
```

Start the FastAPI server:

```bash
python main.py
```

The backend will run on `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies with pnpm:

```bash
pnpm install
```

Start the Next.js development server:

```bash
pnpm dev
```

The frontend will run on `http://localhost:3000`.

## Usage

1. Open `http://localhost:3000` in your browser.
2. Select your LLM Provider (e.g., Anthropic).
3. Enter your API Key (it is only sent to your local backend).
4. Modify the prompt if desired.
5. Click "Start Streaming".

You should see the "Live Rendered Task" component updating in real-time as the JSON fields are generated, along with the raw JSON stream log below it.

