#!/bin/bash

# Automated Git Push Script with Rebase
# Safely commits and pushes changes to GitHub with automatic rebase

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BRANCH="main"
REMOTE="origin"

echo -e "${BLUE}=== Git Push Automation Script ===${NC}\n"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}Current branch: ${CURRENT_BRANCH}${NC}"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "\n${YELLOW}Uncommitted changes detected:${NC}"
    git status -s
    
    # Ask for commit message
    echo -e "\n${BLUE}Enter commit message (or press Ctrl+C to cancel):${NC}"
    read -r COMMIT_MSG
    
    if [[ -z "$COMMIT_MSG" ]]; then
        echo -e "${RED}Error: Commit message cannot be empty${NC}"
        exit 1
    fi
    
    # Stage all changes
    echo -e "\n${GREEN}Staging all changes...${NC}"
    git add -A
    
    # Show what will be committed
    echo -e "\n${YELLOW}Files to be committed:${NC}"
    git status -s
    
    # Commit changes
    echo -e "\n${GREEN}Committing changes...${NC}"
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✓ Changes committed${NC}"
else
    echo -e "${GREEN}✓ No uncommitted changes${NC}"
fi

# Fetch latest changes from remote
echo -e "\n${GREEN}Fetching latest changes from ${REMOTE}...${NC}"
git fetch "$REMOTE"

# Check if remote branch exists
if git ls-remote --exit-code --heads "$REMOTE" "$CURRENT_BRANCH" > /dev/null 2>&1; then
    # Remote branch exists, check if we need to rebase
    LOCAL=$(git rev-parse @)
    REMOTE_REF=$(git rev-parse "@{u}")
    BASE=$(git merge-base @ "@{u}")
    
    if [ "$LOCAL" = "$REMOTE_REF" ]; then
        echo -e "${GREEN}✓ Already up to date with remote${NC}"
    elif [ "$LOCAL" = "$BASE" ]; then
        echo -e "${YELLOW}Remote has new commits, pulling with rebase...${NC}"
        git pull --rebase "$REMOTE" "$CURRENT_BRANCH"
        echo -e "${GREEN}✓ Rebased successfully${NC}"
    elif [ "$REMOTE_REF" = "$BASE" ]; then
        echo -e "${GREEN}✓ Local is ahead of remote${NC}"
    else
        echo -e "${YELLOW}Branches have diverged, rebasing...${NC}"
        git pull --rebase "$REMOTE" "$CURRENT_BRANCH"
        echo -e "${GREEN}✓ Rebased successfully${NC}"
    fi
else
    echo -e "${YELLOW}Remote branch doesn't exist yet${NC}"
fi

# Push changes
echo -e "\n${GREEN}Pushing to ${REMOTE}/${CURRENT_BRANCH}...${NC}"
if git push "$REMOTE" "$CURRENT_BRANCH"; then
    echo -e "\n${GREEN}✓ Successfully pushed to ${REMOTE}/${CURRENT_BRANCH}${NC}"
    
    # Show the last commit
    echo -e "\n${BLUE}Last commit:${NC}"
    git log -1 --oneline --decorate
    
    # Show remote URL
    REMOTE_URL=$(git remote get-url "$REMOTE")
    echo -e "\n${BLUE}Remote repository:${NC} ${REMOTE_URL}"
else
    echo -e "\n${RED}✗ Failed to push changes${NC}"
    echo -e "${YELLOW}You may need to resolve conflicts or use 'git push --force-with-lease' if you've rebased${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== Push completed successfully ===${NC}"

# Made with Bob
