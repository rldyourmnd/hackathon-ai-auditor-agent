# Curestry - AI Prompt Analysis & Optimization Platform

## Product Overview

Curestry is an intelligent platform designed to analyze, validate, and optimize prompts for Large Language Models (LLMs). The system provides comprehensive analysis across multiple dimensions including semantic consistency, markup validation, vocabulary optimization, and contradiction detection.

## Core Value Proposition

- **Automated Prompt Quality Assessment**: Multi-dimensional analysis of prompt quality using various metrics
- **Smart Patch Generation**: Automated suggestions for improvements with safe/risky categorization
- **Consistency Management**: Cross-prompt relationship tracking and conflict detection
- **Interactive Clarification**: Chat-based prompt refinement through targeted questions
- **Multi-format Support**: Works with both XML and Markdown formatted prompts

## System Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Pydantic v2 for data validation
- **Database**: PostgreSQL with SQLAlchemy/SQLModel ORM
- **Cache**: Redis (optional)
- **Orchestration**: LangGraph for analysis pipeline management
- **LLM Integration**: Multi-provider support (OpenAI, Anthropic)

### Frontend (Next.js)
- **Framework**: Next.js with App Router
- **UI Library**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand
- **Code Editor**: Monaco Editor with syntax highlighting

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (optional)
- **Monitoring**: Health checks, basic metrics
- **CI/CD**: GitHub Actions with linting and testing

## Core Analysis Pipeline

### 1. Language & Translation Module
- **Language Detection**: Automatic prompt language identification
- **Translation**: Machine translation to English for analysis
- **Metadata**: Tracking of translation status

### 2. Markup Validation & Formatting
- **Format Detection**: XML/Markdown validation
- **Auto-fixing**: Safe markup repairs (closing tags, headers)
- **Quality Metrics**: Markup validity scores and fix counts

### 3. Vocabulary & Simplicity Analysis
- **Term Frequency**: Statistical analysis of vocabulary usage
- **Synonym Clustering**: Embedding-based term grouping
- **Canonicalization**: Standardization of terminology including tags/sections

### 4. Contradiction Detection
- **Intra-prompt**: LLM-based Natural Language Inference within single prompts
- **Inter-prompt**: Cross-document consistency checking in prompt-base

### 5. Semantic Entropy Measurement
- **Response Sampling**: Generate 8-12 responses with temperature 0.7
- **Embedding Analysis**: Vector clustering of responses
- **Metrics**: Entropy, spread, and cluster analysis

### 6. LLM-as-Judge Scoring
- **Rubric-based Evaluation**: Structured scoring with rationales
- **JSON Output**: Standardized score format without model reasoning exposure

### 7. Patch Generation Engine
- **Safe Patches**: Low-risk improvements (formatting, terminology)
- **Risky Patches**: Structural changes requiring review
- **Preview System**: Diff visualization and impact assessment

## API Endpoints

### Core Analysis
- `POST /analyze` - Comprehensive prompt analysis
- `POST /apply` - Apply selected patches
- `POST /clarify` - Interactive prompt refinement
- `GET /export/{id}.{md|xml}` - Export processed prompts
- `GET /report/{id}.json` - Detailed analysis reports

### Prompt Base Management
- `POST /prompt-base/add` - Add prompt to knowledge base
- `POST /prompt-base/check` - Consistency validation
- `GET /prompt-base/list` - Retrieve stored prompts

### System
- `GET /healthz` - Health check endpoint

## Key Features

### 1. Analysis Dashboard
- **Comprehensive Metrics**: All quality dimensions in single view
- **Visual Indicators**: Color-coded quality scores and trends
- **Patch Management**: Categorized improvement suggestions
- **Export Options**: Multiple format support (MD, XML, PDF)

### 2. Interactive Editor
- **Monaco Integration**: Professional code editing experience
- **Real-time Validation**: Live markup and syntax checking
- **Problem Highlighting**: Visual indication of detected issues
- **Preview Mode**: Side-by-side original/improved comparison

### 3. Clarification System
- **Smart Questions**: AI-generated clarification requests
- **Chat Interface**: Interactive prompt refinement
- **Context Awareness**: Questions based on detected ambiguities
- **Iterative Improvement**: Multiple rounds of refinement

### 4. Prompt Base
- **Relationship Tracking**: Dependencies, overrides, conflicts
- **Consistency Monitoring**: Cross-prompt conflict detection
- **Version Management**: Prompt evolution tracking
- **Collaborative Features**: Shared prompt libraries

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy/SQLModel** - ORM
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **LangGraph** - Workflow orchestration
- **OpenAI/Anthropic APIs** - LLM integration

### Frontend
- **Node.js 18+**
- **Next.js 14** with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Monaco Editor** - Code editing
- **Zustand** - State management

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerization
- **PostgreSQL** - Primary database
- **Redis** - Caching (optional)
- **Nginx** - Reverse proxy
- **GitHub Actions** - CI/CD

## Environment Configuration

### Core Settings
```env
ENV=development|production
LOG_LEVEL=INFO
```

### Database & Cache
```env
POSTGRES_USER=curestry
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=curestry
DATABASE_URL=postgresql+psycopg://user:pass@db:5432/curestry
REDIS_URL=redis://redis:6379/0
```

### LLM Providers
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDINGS_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
```

### Analysis Configuration
```env
ENTROPY_N=8
ENTROPY_TEMP=0.7
```

### Frontend
```env
NEXT_PUBLIC_API_BASE=http://api:8000
```

## Project Structure

```
curestry/
├── backend/
│   └── app/
│       ├── main.py
│       ├── api/routers/
│       ├── core/config.py
│       ├── services/
│       │   ├── llm.py
│       │   └── embeddings.py
│       └── models/
├── frontend/
│   └── app/
│       ├── components/
│       ├── pages/
│       └── services/
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── nginx/
├── scripts/
├── .env.example
└── Makefile
```

## Quality Metrics

### Markup Quality
- **Validity Score**: Percentage of valid markup
- **Fix Count**: Number of auto-corrections applied
- **Consistency**: Uniform formatting across sections

### Semantic Quality
- **Entropy Score**: Response consistency measurement
- **Spread**: Variation in generated outputs
- **Cluster Count**: Number of distinct response patterns

### Content Quality
- **Contradiction Count**: Internal inconsistencies detected
- **Vocabulary Complexity**: Readability and term standardization
- **Judge Score**: LLM-evaluated overall quality

### Relationship Quality
- **Dependency Integrity**: Valid prompt relationships
- **Conflict Detection**: Cross-prompt inconsistencies
- **Coverage**: Completeness of prompt specifications

## Security & Observability

### Security
- **Rate Limiting**: Request throttling
- **Data Privacy**: Prompt content protection in logs
- **Environment Isolation**: Secure configuration management

### Monitoring
- **Health Checks**: Service availability monitoring
- **Request Logging**: Structured JSON logs
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Comprehensive error reporting

## Development Workflow

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd curestry
cp .env.example .env

# Start development environment
make up

# Run tests
make test

# Lint code
make lint
```

### Development Commands
- `make up` - Start all services
- `make down` - Stop all services  
- `make logs` - View service logs
- `make lint` - Run code linting
- `make test` - Execute test suite

## Demo Data

The system includes pre-configured demo prompts covering:
- **Coding Agent**: Software development assistance prompts
- **FAQ Agent**: Customer support automation prompts  
- **Content Writing**: Article and documentation generation prompts

Each demo case demonstrates different types of quality issues and improvement opportunities.

## Extensibility

### Plugin Architecture
- **Custom Metrics**: Extensible analysis modules
- **Provider Integration**: Additional LLM/embedding providers
- **Export Formats**: Custom output format support
- **UI Themes**: Customizable interface styling

### Integration Options
- **IDE Extensions**: VS Code/JetBrains plugin support
- **API Integration**: RESTful API for external tools
- **Webhook Support**: Event-driven integrations
- **Batch Processing**: Bulk prompt analysis capabilities
