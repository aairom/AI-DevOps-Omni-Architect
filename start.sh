#!/bin/bash

# Start script for AI-DevOps-Omni-Architect v42
# Launches the Streamlit app in detached mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-devops-Omni-Architect_v42.py"
PORT=8501
LOG_FILE="omni_architect.log"
PID_FILE=".omni_architect.pid"

echo -e "${GREEN}Starting AI-DevOps-Omni-Architect v42...${NC}"

# Check if app is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}App is already running with PID $OLD_PID${NC}"
        echo -e "${YELLOW}Use ./stop.sh to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}Removing stale PID file${NC}"
        rm "$PID_FILE"
    fi
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Check if Streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo -e "${RED}Error: Streamlit is not installed${NC}"
    echo -e "${YELLOW}Run: pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Copy .env_template to .env and configure your API keys${NC}"
fi

# Start the app in detached mode
echo -e "${GREEN}Launching Streamlit app on port $PORT...${NC}"
nohup streamlit run "$APP_NAME" --server.port="$PORT" --server.headless=true > "$LOG_FILE" 2>&1 &

# Save PID
APP_PID=$!
echo "$APP_PID" > "$PID_FILE"

# Wait a moment to check if app started successfully
sleep 2

if ps -p "$APP_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ App started successfully!${NC}"
    echo -e "${GREEN}  PID: $APP_PID${NC}"
    echo -e "${GREEN}  URL: http://localhost:$PORT${NC}"
    echo -e "${GREEN}  Logs: $LOG_FILE${NC}"
    echo ""
    echo -e "${YELLOW}To stop the app, run: ./stop.sh${NC}"
    echo -e "${YELLOW}To view logs, run: tail -f $LOG_FILE${NC}"
else
    echo -e "${RED}✗ Failed to start app${NC}"
    echo -e "${RED}Check $LOG_FILE for errors${NC}"
    rm "$PID_FILE"
    exit 1
fi

# Made with Bob
