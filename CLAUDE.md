# WebGIS Project - CLAUDE.md

This document provides essential information for working with this WebGIS project that combines AI-powered natural language querying with spatial data visualization.

## Project Overview

This is a sophisticated WebGIS application with:
- **Backend**: FastAPI with LangGraph/LangChain for AI-powered SQL query generation
- **Frontend**: Vue3 with OpenLayers for interactive maps
- **Database**: PostgreSQL with PostGIS for spatial data
- **AI Integration**: DeepSeek LLM for natural language to SQL conversion
- **Caching**: Hybrid caching with semantic similarity search

## Project Structure

```
m_webgis_project/
├── m_WGP_vue3/          # Frontend (Vue3 + Vite)
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── python/              # Backend (FastAPI)
│   └── sight_server/
│       ├── main.py      # FastAPI entry point
│       ├── config.py    # Configuration management
│       ├── requirements.txt
│       ├── core/
│       │   ├── agent.py # SQL Query Agent
│       │   └── graph/
│       │       └── builder.py # LangGraph workflow
│       └── services/
│           └── query_cache_manager.py
└── README.md
```

## Development Commands

### Frontend (Vue3)
```bash
cd m_WGP_vue3
npm install          # Install dependencies
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend (FastAPI)
```bash
cd python/sight_server
pip install -r requirements.txt  # Install Python dependencies
uvicorn main:app --reload       # Start development server
```

## Key Technical Architecture

### 1. AI-Powered Query System
- **LangGraph Workflow**: Multi-step query generation with memory and checkpoints
- **Intent Analysis**: Classifies queries as spatial vs non-spatial, query vs summary
- **Query Validation**: Validates generated SQL before execution
- **Error Recovery**: Automatic retry mechanisms for failed queries

### 2. Session Management
- **Multi-round Conversations**: Maintains context across user interactions
- **Memory Persistence**: Stores conversation history and query results
- **Checkpoint System**: Allows workflow state persistence and recovery

### 3. Caching Strategy
- **Semantic Similarity**: Uses embeddings to find similar cached queries
- **Hybrid Cache**: Combines in-memory and database persistence
- **External Cache Support**: Configurable cache backends

### 4. Database Integration
- **PostgreSQL + PostGIS**: Spatial database with GIS extensions
- **SQLAlchemy ORM**: Database abstraction layer
- **Spatial Queries**: Native support for geographic operations

## Important Configuration

### Environment Variables
```python
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
- **config.py**: Centralized configuration using pydantic-settings
- **main.py**: API endpoints and application setup
- **agent.py**: Core AI agent implementation

## Core Components

### 1. SQL Query Agent (`core/agent.py`)
- Implements LangGraph workflow for query generation
- Handles intent classification and query validation
- Manages session state and conversation memory

### 2. Graph Builder (`core/graph/builder.py`)
- Constructs the LangGraph workflow
- Defines state transitions and node connections
- Implements checkpoint system for state persistence

### 3. Query Cache Manager (`services/query_cache_manager.py`)
- Manages query caching with semantic similarity
- Supports multiple cache backends
- Handles cache invalidation and TTL

## Development Patterns

### Code Style Guidelines
- **Backend**: Follow FastAPI conventions with proper type hints
- **Frontend**: Use Vue3 Composition API with TypeScript
- **Database**: Use SQLAlchemy ORM with proper session management
- **AI Components**: Implement proper error handling and retry logic

### Testing Strategy
- **API Tests**: Test FastAPI endpoints with proper fixtures
- **Agent Tests**: Test LangGraph workflows with mock LLM responses
- **Cache Tests**: Verify cache hit/miss behavior
- **Integration Tests**: End-to-end testing of query pipeline

## Common Development Tasks

### Adding New Query Types
1. Update intent classification in `agent.py`
2. Add new workflow nodes in `graph/builder.py`
3. Update API endpoints in `main.py`
4. Add corresponding frontend components

### Modifying Cache Strategy
1. Update cache configuration in `config.py`
2. Modify `query_cache_manager.py` for new cache logic
3. Update cache invalidation rules

### Extending Frontend Components
1. Add new Vue components in `m_WGP_vue3/src/components/`
2. Update routing and state management
3. Add corresponding API calls to backend

## Important Notes

### Performance Considerations
- Query caching significantly improves response times
- Spatial queries can be resource-intensive
- LLM API calls should be rate-limited
- Database connections should be properly pooled

### Security Considerations
- SQL injection protection through parameterized queries
- API rate limiting for LLM endpoints
- Proper input validation for all user queries
- Secure handling of API keys and credentials

### Error Handling Patterns
- Implement comprehensive logging for debugging
- Use structured error responses from API
- Handle LLM API failures gracefully
- Implement fallback mechanisms for critical failures

## Troubleshooting

### Common Issues
1. **Database Connection**: Verify PostgreSQL and PostGIS installation
2. **LLM API**: Check DeepSeek API key and rate limits
3. **Cache Issues**: Verify Redis/alternative cache service
4. **Spatial Queries**: Ensure PostGIS extensions are enabled

### Debugging Tips
- Enable debug logging in configuration
- Use LangGraph visualization for workflow debugging
- Check cache hit rates for performance issues
- Monitor API response times and error rates

---

This project represents a sophisticated integration of modern web technologies with AI-powered spatial data analysis. The architecture supports complex multi-step query workflows while maintaining performance through intelligent caching and session management.