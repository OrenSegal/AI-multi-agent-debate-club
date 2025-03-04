#!/bin/bash

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    log "GitHub CLI not found. Installing..."
    brew install gh
fi

# Login to GitHub CLI if not already logged in
if ! gh auth status &> /dev/null; then
    log "Logging into GitHub..."
    gh auth login
fi

# Create the repository on GitHub
log "Creating repository on GitHub..."
gh repo create ai-debate-club \
    --description "An automated debate platform where users can engage in structured debates with AI opponents" \
    --public \
    --source=. \
    --remote=origin \
    --push

# Initialize Git if not already initialized
if [ ! -d .git ]; then
    log "Initializing Git repository..."
    git init
fi

# Add all files
log "Adding files to repository..."
git add .

# Create initial commit
log "Creating initial commit..."
git commit -m "Initial commit"

# Push to main branch
log "Pushing to main branch..."
git push -u origin main

log "Repository creation complete!"
log "Repository URL: https://github.com/OrenSegal/ai-debate-club"
