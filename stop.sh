#!/bin/bash

# Stop script for AI-DevOps-Omni-Architect v43
# Stops the Streamlit app running in detached mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PID_FILE=".omni_architect.pid"
APP_NAME="streamlit"

echo -e "${GREEN}Stopping AI-DevOps-Omni-Architect...${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No PID file found. App may not be running.${NC}"
    
    # Try to find and kill any running Streamlit processes (v42 or v43)
    PIDS=$(pgrep -f "streamlit run ai-devops-Omni-Architect" || true)
    
    if [ -z "$PIDS" ]; then
        echo -e "${YELLOW}No running Streamlit processes found.${NC}"
        exit 0
    else
        echo -e "${YELLOW}Found running Streamlit processes: $PIDS${NC}"
        echo -e "${YELLOW}Attempting to stop them...${NC}"
        echo "$PIDS" | xargs kill -15 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        REMAINING=$(pgrep -f "streamlit run ai-devops-Omni-Architect" || true)
        if [ ! -z "$REMAINING" ]; then
            echo -e "${YELLOW}Force stopping remaining processes...${NC}"
            echo "$REMAINING" | xargs kill -9 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✓ Stopped all Streamlit processes${NC}"
        exit 0
    fi
fi

# Read PID from file
APP_PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$APP_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}Process $APP_PID is not running${NC}"
    rm "$PID_FILE"
    exit 0
fi

# Try graceful shutdown first
echo -e "${GREEN}Sending SIGTERM to process $APP_PID...${NC}"
kill -15 "$APP_PID" 2>/dev/null || true

# Wait for process to stop
TIMEOUT=10
COUNTER=0
while ps -p "$APP_PID" > /dev/null 2>&1 && [ $COUNTER -lt $TIMEOUT ]; do
    sleep 1
    COUNTER=$((COUNTER + 1))
    echo -n "."
done
echo ""

# Check if process stopped
if ps -p "$APP_PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}Process did not stop gracefully, forcing shutdown...${NC}"
    kill -9 "$APP_PID" 2>/dev/null || true
    sleep 1
fi

# Verify process is stopped
if ps -p "$APP_PID" > /dev/null 2>&1; then
    echo -e "${RED}✗ Failed to stop process $APP_PID${NC}"
    exit 1
else
    echo -e "${GREEN}✓ App stopped successfully${NC}"
    rm "$PID_FILE"
fi

# Clean up any orphaned Streamlit processes (v42 or v43)
ORPHANS=$(pgrep -f "streamlit run ai-devops-Omni-Architect" || true)
if [ ! -z "$ORPHANS" ]; then
    echo -e "${YELLOW}Cleaning up orphaned processes...${NC}"
    echo "$ORPHANS" | xargs kill -9 2>/dev/null || true
fi

echo -e "${GREEN}All processes stopped${NC}"

# Made with Bob
