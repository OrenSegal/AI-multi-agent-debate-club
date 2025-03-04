#!/bin/bash

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file and add your API keys before continuing."
    exit 1
fi

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose up --build -d

# Show container status
echo "Container status:"
docker-compose ps

echo ""
echo "AI Debate Club is now running on http://localhost:8501"
echo "Press Ctrl+C to stop viewing logs. The application will continue running in the background."

# Show logs
docker-compose logs -f
