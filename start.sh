#!/bin/bash

# Start script for AI-DevOps-Omni-Architect v44
# Launches the Streamlit app in detached mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_VERSION="${1:-v44}"  # Default to v44, can specify v42/v43 as argument
APP_NAME="ai-devops-Omni-Architect_${APP_VERSION}.py"
PORT=8501
LOG_FILE="omni_architect.log"
PID_FILE=".omni_architect.pid"

echo -e "${GREEN}Starting AI-DevOps-Omni-Architect ${APP_VERSION}...${NC}"

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

# Check if app file exists
if [ ! -f "$APP_NAME" ]; then
    echo -e "${RED}Error: $APP_NAME not found${NC}"
    if [ "$APP_VERSION" = "v44" ]; then
        echo -e "${YELLOW}Trying v43 as fallback...${NC}"
        APP_NAME="ai-devops-Omni-Architect_v43.py"
        APP_VERSION="v43"
        if [ ! -f "$APP_NAME" ]; then
            echo -e "${YELLOW}Trying v42 as fallback...${NC}"
            APP_NAME="ai-devops-Omni-Architect_v42.py"
            APP_VERSION="v42"
            if [ ! -f "$APP_NAME" ]; then
                echo -e "${RED}Error: No application file found${NC}"
                exit 1
            fi
        fi
    else
        exit 1
    fi
fi

# Start the app in detached mode
echo -e "${GREEN}Launching Streamlit app on port $PORT...${NC}"
if [ "$APP_VERSION" = "v44" ]; then
    echo -e "${BLUE}📈 Using v44 with Advanced Monitoring Dashboard${NC}"
elif [ "$APP_VERSION" = "v43" ]; then
    echo -e "${BLUE}⚡ Using v43 with Async Operations${NC}"
fi
nohup streamlit run "$APP_NAME" --server.port="$PORT" --server.headless=true > "$LOG_FILE" 2>&1 &

# Save PID
APP_PID=$!
echo "$APP_PID" > "$PID_FILE"

# Wait a moment to check if app started successfully
sleep 2

if ps -p "$APP_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ App started successfully!${NC}"
    echo -e "${GREEN}  Version: ${APP_VERSION}${NC}"
    echo -e "${GREEN}  PID: $APP_PID${NC}"
    echo -e "${GREEN}  URL: http://localhost:$PORT${NC}"
    echo -e "${GREEN}  Logs: $LOG_FILE${NC}"
    echo ""
    if [ "$APP_VERSION" = "v44" ]; then
        echo -e "${BLUE}📈 Monitoring Dashboard: Available${NC}"
        echo -e "${BLUE}⚡ Async Mode: Available${NC}"
        echo -e "${BLUE}🤝 Ensemble: Available${NC}"
        echo -e "${BLUE}🔌 WebSocket: Available${NC}"
    elif [ "$APP_VERSION" = "v43" ]; then
        echo -e "${BLUE}⚡ Async Mode: Available${NC}"
        echo -e "${BLUE}🤝 Ensemble: Available${NC}"
        echo -e "${BLUE}🔌 WebSocket: Available${NC}"
    fi
    echo ""
    echo -e "${YELLOW}To stop the app, run: ./stop.sh${NC}"
    echo -e "${YELLOW}To view logs, run: tail -f $LOG_FILE${NC}"
    echo -e "${YELLOW}To switch versions, run: ./start.sh v42, ./start.sh v43, or ./start.sh v44${NC}"
else
    echo -e "${RED}✗ Failed to start app${NC}"
    echo -e "${RED}Check $LOG_FILE for errors${NC}"
    rm "$PID_FILE"
    exit 1
fi

# Made with Bob
