# AI Debate Club

An automated debate platform where users can engage in structured debates with AI opponents.

## Project Structure

```
|-- .env
|-- .env.example
|-- .gitignore
|-- .python-version
|-- Dockerfile
|-- LICENSE
|-- README.md
|-- app.py
|-- config.py
|-- docker-compose.yml
|-- docker-run.sh
|-- pyproject.toml
|-- run.sh
|-- server_debug.py
|-- topics_cache.json
|-- uv.lock
|-- db
  |-- chroma.sqlite3
|-- data
  |-- debates
|-- backend
  |-- __init__.py
  |-- config.py
  |-- agents
    |-- __init__.py
    |-- debate_manager.py
    |-- debate_setter.py
    |-- debater_agent.py
    |-- scorekeeper_agent.py
    |-- streaming_debate_manager.py
  |-- api
    |-- models.py
    |-- routes.py
  |-- components
    |-- loading_animation.py
  |-- server
    |-- __init__.py
    |-- api_routes.py
    |-- config.py
    |-- llm_api_client.py
    |-- orchestrator.py
    |-- workflow_manager.py
  |-- services
    |-- __init__.py
    |-- llm_service.py
  |-- data_sources
    |-- __init__.py
    |-- data_manager.py
    |-- fact_checker.py
    |-- kialo_scraper.py
    |-- scraper.py
    |-- wiki_scraper.py
  |-- utils
    |-- __init__.py
    |-- helpers.py
    |-- prompts.py
  |-- storage
    |-- __init__.py
    |-- dataframe.py
    |-- elasticsearch_store.py
    |-- vector_store.py
    |-- db
      |-- chroma.sqlite3
  |-- debate
    |-- llm
      |-- client.py
  |-- debate_system
    |-- __init__.py

```

## Features

- AI debater agents that argue pro and con positions on various topics
- Debate moderator that introduces topics
- Scorekeeper that evaluates arguments and determines a winner
- Fact-checking and fallacy detection
- Topic sourcing from kialo-edu.org and Wikipedia
- Vector storage of debate results
- Asynchronous debate orchestration
- Streamlit user interface
- Structured workflow management for debate stages
- Resilient LLM API integration with retry capability
- RESTful API endpoints for debate management
- Persistent storage of debate state and arguments

## API Endpoints

- `POST /orchestrate_debate`: Start a new debate
- `GET /debate/{debate_id}/status`: Get debate status
- `GET /debates`: List all debates

## Configuration

Environment variables:
- `LLM_API_URL`: LLM API endpoint (default: "https://openrouter.ai/api/v1")
- `LLM_API_KEY`: Your LLM API key
- `API_TIMEOUT`: API request timeout in seconds (default: 60.0)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI_debate_club.git
cd AI_debate_club
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
cp .env.example .env
```
Then edit the `.env` file to add your API keys.

## Docker Installation

For easy deployment, you can use Docker:

1. Make sure you have Docker and Docker Compose installed on your system.

2. Clone this repository:
```bash
git clone https://github.com/yourusername/AI_debate_club.git
cd AI_debate_club
```

4. Set up environment variables:
```bash
export LLM_API_KEY="your-api-key-here"
# Optional:
export LLM_API_URL="https://openrouter.ai/api/v1"
export API_TIMEOUT=60.0
export LOG_LEVEL=INFO
```

5. Run the development server:
```bash
uvicorn backend.api.routes:app --reload
```

## Testing

Run the debug script to test debate orchestration:
```bash
python server_debug.py
```

## Dependencies

- FastAPI: Web framework for building APIs
- Pydantic: Data validation using Python type annotations
- httpx: Async HTTP client
- tenacity: Retry library for robust API calls
- uvicorn: ASGI server implementation

## Project Status

Current features implemented:
- Basic debate orchestration
- LLM integration for argument generation
- Workflow management system
- State persistence
- RESTful API endpoints

Upcoming features:
- Real-time debate updates
- User authentication
- Debate history and analytics
- Enhanced argument generation
- Multiple LLM provider support

## License

MIT License - see LICENSE file for details