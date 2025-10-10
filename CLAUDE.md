# CLAUDE.md

This file provides guidance to Claude Code when working with this WebGIS project. It combines AI-powered natural language querying with spatial data visualization.

## Project Overview
- **Backend**: FastAPI with LangGraph/LangChain for AI-powered SQL query generation.
- **Frontend**: Vue3 with OpenLayers for interactive maps.
- **Database**: PostgreSQL with PostGIS for spatial data.
- **AI Integration**: DeepSeek LLM for natural language to SQL conversion.
- **Caching**: Hybrid caching with semantic similarity search.

## Project Structure
```
m_webgis_project/
├── m_WGP_vue3/              # Frontend (Vue3 + Vite)
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.js       # Vite configuration
│   └── src/                 # Frontend source code
├── python/                  # Backend (FastAPI)
│   └── sight_server/
│       ├── main.py          # FastAPI entry point
│       ├── config.py        # Configuration management
│       ├── requirements.txt # Backend dependencies
│       ├── core/
│       │   ├── agent.py     # SQL Query Agent
│       │   └── graph/
│       │       └── builder.py # LangGraph workflow
│       └── services/
│           └── query_cache_manager.py # Caching service
└── CLAUDE.md                # This file
```

## Development Commands

### Frontend (`m_WGP_vue3`)
```bash
cd m_WGP_vue3
npm install          # Install dependencies
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend (`python/sight_server`)
```bash
cd python/sight_server
pip install -r requirements.txt  # Install Python dependencies
uvicorn main:app --reload       # Start development server
```

## Key Technical Architecture

### 1. AI-Powered Query System
- **LangGraph Workflow**: Multi-step query generation with memory and checkpoints. See `python/sight_server/core/graph/builder.py`.
- **Intent Analysis**: Classifies queries as spatial vs. non-spatial, query vs. summary. See `python/sight_server/core/agent.py`.
- **Query Validation**: Validates generated SQL before execution.
- **Error Recovery**: Automatic retry mechanisms for failed queries.

### 2. Session Management
- **Multi-round Conversations**: Maintains context across user interactions.
- **Memory Persistence**: Stores conversation history and query results. See `python/sight_server/core/memory.py`.
- **Checkpoint System**: Allows workflow state persistence and recovery. See `python/sight_server/core/checkpoint.py`.

### 3. Caching Strategy
- **Semantic Similarity**: Uses embeddings to find similar cached queries.
- **Hybrid Cache**: Combines in-memory and database persistence. See `python/sight_server/core/query_cache_manager.py`.
- **External Cache Support**: Configurable cache backends.

### 4. Database Integration
- **PostgreSQL + PostGIS**: Spatial database with GIS extensions.
- **SQLAlchemy ORM**: Database abstraction layer. See `python/sight_server/core/database.py`.
- **Spatial Queries**: Native support for geographic operations.

## Important Configuration

### Environment Variables (`python/sight_server/.env`)
```
# Database
DATABASE_URL=postgresql://user:pass@host/db

# LLM Configuration
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL=3600

# Agent Settings
MAX_RETRY_COUNT=3
QUERY_TIMEOUT=30
```

### Key Configuration Files
- `python/sight_server/config.py`: Centralized configuration using `pydantic-settings`.
- `python/sight_server/main.py`: API endpoints and application setup.

## Core Components

### 1. SQL Query Agent (`python/sight_server/core/agent.py`)
- Implements the LangGraph workflow for query generation.
- Handles intent classification and query validation.
- Manages session state and conversation memory.

### 2. Graph Builder (`python/sight_server/core/graph/builder.py`)
- Constructs the LangGraph workflow with nodes and edges.
- Defines state transitions and node connections.
- Implements the checkpoint system for state persistence.

### 3. Query Cache Manager (`python/sight_server/core/query_cache_manager.py`)
- Manages query caching with semantic similarity.
- Supports multiple cache backends (in-memory, database).
- Handles cache invalidation and Time-To-Live (TTL).

## Development Patterns & Best Practices

### Code Style
- **Backend**: Follow FastAPI conventions with proper type hints.
- **Frontend**: Use Vue3 Composition API, preferably with TypeScript.

### Testing
- **API Tests**: Use `pytest` for FastAPI endpoints.
- **Agent Tests**: Test LangGraph workflows with mock LLM responses.
- **Cache Tests**: Verify cache hit/miss behavior.
- **Integration Tests**: End-to-end testing of the full query pipeline.

## Common Development Tasks

### Adding New Query Types
1. Update intent classification rules in `python/sight_server/core/agent.py`.
2. Add new workflow nodes or edges in `python/sight_server/core/graph/builder.py`.
3. Add or modify API endpoints in `python/sight_server/main.py`.
4. Create corresponding components in `m_WGP_vue3/src/components/`.

### Modifying Cache Strategy
1. Update cache settings in `python/sight_server/config.py`.
2. Modify `python/sight_server/core/query_cache_manager.py` for new caching logic.

## Important Notes

### Performance
- Caching is critical for good performance.
- Spatial queries can be resource-intensive; optimize them carefully.

### Security
- All user input is validated before being used in queries.
- API keys and other secrets are managed through environment variables.

### Error Handling
- The system uses structured logging for easier debugging.
- Graceful failure and retry logic are implemented for LLM API calls.

## Troubleshooting

- **Database**: Ensure PostgreSQL and PostGIS are correctly installed and the PostGIS extension is enabled.
- **LLM API**: Check your DeepSeek API key and rate limits.
- **Debugging**: Use LangGraph visualization tools for debugging complex query workflows. Check logs for detailed error information.
