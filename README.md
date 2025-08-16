# Curestry - AI Prompt Analysis & Optimization Platform

An intelligent platform for analyzing, validating, and optimizing prompts for Large Language Models (LLMs).

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd curestry
cp .env.example .env
# Add your OpenAI API key to .env

# Start development environment
cd infra
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Windows Users

Use the provided batch script:
```bash
dev up     # Start all services
dev logs   # View logs
dev down   # Stop services
dev help   # Show all commands
```

## Features

- **Multi-dimensional Analysis**: Semantic consistency, markup validation, vocabulary optimization
- **Smart Patch Generation**: Automated improvement suggestions with safe/risky categorization
- **Interactive Clarification**: Chat-based prompt refinement
- **Prompt Base Management**: Cross-prompt relationship tracking and conflict detection
- **Multi-format Support**: XML and Markdown prompt analysis

## Architecture

- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js + Tailwind CSS + shadcn/ui
- **LLM Integration**: OpenAI GPT-5 — nano for cheap tasks; mini for standard and premium tiers
- **Deployment**: Docker Compose

## Development

- `dev up` - Start all services
- `dev down` - Stop all services  
- `dev logs` - View service logs
- `dev ps` - Check container status

## License

MIT License - see LICENSE file for details.
