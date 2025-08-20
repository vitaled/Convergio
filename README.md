# 🚀 Convergio — AI Command Center powered by Multi‑Agent Orchestration
Human purpose. AI momentum.

> Convergio turns a team’s intent into coordinated execution by orchestrating 40+ specialized AI agents. You set the goal; the system assembles experts (finance, architecture, PM, security, design, analytics) to plan, decide, and deliver.

[![CI/CD Pipeline](https://github.com/Roberdan/Convergio/actions/workflows/ci.yml/badge.svg)](https://github.com/Roberdan/Convergio/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit-orange?style=for-the-badge&logo=svelte)](https://kit.svelte.dev/)
[![Microsoft AutoGen](https://img.shields.io/badge/Microsoft%20AutoGen-0.7.x-red?style=for-the-badge&logo=microsoft)](https://github.com/microsoft/autogen)
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue?style=for-the-badge)](LICENSE)

---

## 🗞️ What this is (and why it matters)

- Convergio is a unified, production‑leaning reference implementation of a multi‑agent platform built on top of Microsoft AutoGen. It is one of the first large‑scale, end‑to‑end implementations of AutoGen in an open repository, showing how to compose dozens of purpose‑built agents into reliable workflows. See Microsoft AutoGen on GitHub: https://github.com/microsoft/autogen
- Our north star is the Agentic Manifesto and inclusive design. Start here:
  - Agentic Manifesto: AgenticManifesto/AgenticManifesto.md
  - What is Convergio: AgenticManifesto/WhatIsConvergio.md
  - Built for Mario — AI‑First Interface: AgenticManifesto/💜 For Mario - AI-First Interface.md
- Communication meets engineering: this README is both a product primer and a practical guide to run the stack locally.

---

## 🏗️ Architecture (truth, no buzzwords)

- Backend: FastAPI (Python 3.11), SQLAlchemy 2.x (async), PostgreSQL, Redis, Prometheus metrics
- Frontend: SvelteKit + TypeScript + TailwindCSS (dev server on port 4000, proxy to backend 9000)
- AI Orchestration: Multi‑agent system using Microsoft AutoGen 0.7.x (autogen-core, autogen-agentchat, autogen-ext)
- Streaming & coordination: internal streaming orchestrator with typed protocols and runners
- Security: security headers, CORS, JWT scaffolding (RS256), optional rate‑limit middleware (currently disabled in code)

No Docker/Kubernetes manifests are provided in this repo. Local developer setup runs with system Postgres + Redis or containers you manage yourself.

### Key capabilities

- Multi‑agent conversations with tool use, memory, and specialization
- GraphFlow for generating workflows from natural language
- Cost tracking, analytics endpoints, and observability hooks
- Vector search utilities for RAG‑style enrichment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
  

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Roberdan/Convergio.git
cd convergio
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment (see example below)
# Initialize DB with provided SQL (see commands below)
# Start backend
uvicorn src.main:app --reload --port 9000
```

3. **Frontend Setup**
```bash
cd frontend
npm install

# Start frontend (dev server on :4000)
npm run dev
```

4. **Access the application**
- Frontend: http://localhost:4000
- Backend API: http://localhost:9000
- API Documentation: http://localhost:9000/docs

---

## 📚 Documentation

### Core Documentation
- **Implementation Report**: [docs/IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md) - Complete implementation details
- **System Verification**: [docs/COMPREHENSIVE_VERIFICATION_REPORT_AUG2025.md](docs/COMPREHENSIVE_VERIFICATION_REPORT_AUG2025.md)
- **Agent Definitions**: [docs/AGENTS.md](docs/AGENTS.md) - All 48 agents documented
- **Database Schema**: [docs/DataBaseSchema.md](docs/DataBaseSchema.md)
- **Security System**: [docs/SECURE_COST_SYSTEM_VERIFICATION.md](docs/SECURE_COST_SYSTEM_VERIFICATION.md)

### Agent System
- **Agent Definitions**: backend/src/agents/definitions/
- **Orchestrators & resilience**: backend/src/agents/orchestrators/
- **Ali Proactive Intelligence**: backend/src/agents/ali_ceo.py

### Enterprise Features
- **Cost Management**: [docs/cost-tracking-system.md](docs/cost-tracking-system.md)
- **Multi-tenancy**: Complete SaaS platform with Stripe billing
- **Real Data Integrations**: [docs/REAL_DATA_INTEGRATIONS.md](docs/REAL_DATA_INTEGRATIONS.md)
- **Security Compliance**: OWASP Top 10 compliance and comprehensive audit trail

### Live Documentation
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc

---

## 🤖 Multi‑agent ecosystem

Convergio features a comprehensive multi‑agent system of specialized agents organized into functional domains:

### Leadership & Strategy (6 agents)
- **Ali** - Chief of Staff & Proactive Intelligence Engine
- **Amy** - Chief Financial Officer
- **Satya** - Board of Directors Representative  
- **Antonio** - Strategy Expert
- **Matteo** - Strategic Business Architect
- **Domik** - McKinsey Strategic Decision Maker

### Project Management & Operations (8 agents)
- **Davide** - Project Manager
- **Oliver** - Project Manager
- **Marcus** - Project Manager
- **Luke** - Program Manager
- **Wanda** - Workflow Orchestrator
- **Taskmaster** - Strategic Task Decomposition Master
- **Dave** - Change Management Specialist
- **Xavier** - Coordination Patterns Expert

### Technology & Engineering (6 agents)
- **Dan** - Engineering General Manager
- **Baccio** - Tech Architect
- **Marco** - DevOps Engineer
- **Luca** - Security Expert
- **Guardian** - AI Security Validator
- **Thor** - Quality Assurance Guardian

### Data & Analytics (6 agents)
- **Angela** - Data Analyst
- **Ethan** - Data Analyst
- **Ethan IC6** - Senior Data Analyst
- **Omri** - Data Scientist
- **Ava** - Analytics Insights Virtuoso
- **Diana** - Performance Dashboard Expert

### Business Development & Sales (4 agents)
- **Fabio** - Sales & Business Development
- **Michael** - Venture Capitalist
- **Wiz** - Investor & Venture Capital
- **Sam** - Startup Expert

### Human Resources & Culture (4 agents)
- **Giulia** - HR Talent Acquisition
- **Coach** - Team Coach
- **Behice** - Cultural Coach
- **Jenny** - Inclusive Accessibility Champion

### Creative & Communication (5 agents)
- **Sara** - UX/UI Designer
- **Jony** - Creative Director
- **Riccardo** - Storyteller
- **Steve** - Executive Communication Strategist
- **Sofia** - Marketing Strategist

### Customer Success & Compliance (5 agents)
- **Andrea** - Customer Success Manager
- **Elena** - Legal Compliance Expert
- **Dr. Enzo** - Healthcare Compliance Manager
- **Sophia** - Government Affairs
- **Enrico** - Business Process Engineer

### AI & Optimization (4 agents)
- **PO** - Prompt Optimizer
- **Marcus** - Context Memory Keeper
- **Socrates** - First Principles Reasoning
- **Stefano** - Design Thinking Facilitator

Each agent is powered by advanced AI capabilities including:
- **Context-aware reasoning** with per-turn RAG
- **Tool execution** with intelligent selection
- **Memory persistence** across conversations
- **Security validation** and compliance checks
- **Cost optimization** and rate limiting
- **Real-time collaboration** and coordination

---

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test
npm run test:e2e

# Security tests
pytest tests/security/ -v

# Performance tests
pytest tests/performance/ -v

# Golden scenario tests (12+ scenarios)
pytest tests/integration/test_scenarios/ -v
```

### Notes

## 🧪 Test scripts by category

To run targeted test categories without the full `test.sh`, use these scripts from the repo root:

- Backend unit: `./01_test_backend_unit.sh`
- Backend integration: `./02_test_backend_integration.sh`
- Backend E2E: `./03_test_backend_e2e.sh`
- Security: `./04_test_security.sh`
- Performance: `./05_test_performance.sh`
- Frontend unit (Vitest): `./06_test_frontend_unit.sh`
- Frontend Storybook: `./07_test_frontend_storybook.sh`
- Frontend E2E (Playwright): `./08_test_frontend_e2e.sh`
- Master test runner: `./09_test_master_runner.sh`
- Go tests (backend): `./10_test_go_backend.sh`
- Top-level Python tests: `./11_test_backend_top_level.sh`

Tips:
- Continue-on-error: `FAIL_FAST=false ./01_test_backend_unit.sh`
- Verbose logs (where supported): `VERBOSE=true ...`
---

## ⚙️ Environment variables (backend/.env)

Minimal set to get running locally:

```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Security (generate strong JWT secret for production)
JWT_SECRET=your_super_secure_jwt_secret_that_should_be_very_long_and_random_at_least_64_chars
JWT_ALGORITHM=RS256

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=convergio_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Network Configuration
DEFAULT_HOST=localhost
FRONTEND_PORT=4000
BACKEND_PORT=9000
API_PORT=9000
ADMIN_PORT=9001

# User Configuration
DEFAULT_USER_ID=system_user
DEFAULT_ANONYMOUS_USER=system_anonymous
DEFAULT_TEST_USER=system_test_user

# Feature Configuration
REFERENCE_AGENT_TRUNCATE_LENGTH=3000
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE_API=100

# AI providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GRAPHFLOW=true

# Health Monitoring
HEALTH_CHECK_ENABLED=true
LOG_LEVEL=INFO
```

> 📝 **Note**: For a complete list of all available environment variables with detailed explanations, see `.env.example` in the project root.

---

## 🤝 Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- Python: Black + Ruff + mypy
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits specification
- Tests: Required for all new features

---

## 📊 Observability & performance

- Prometheus metrics exposed at /metrics
- Structured logs (JSON) via structlog; configure via LOG_LEVEL, LOG_FORMAT
- Connection pooling for Postgres and Redis; tune via DB_* and REDIS_* settings

---

## 📄 License

This project is licensed under the Business Source License 1.1 - see the [LICENSE](LICENSE) file for details.

After the change date (2027-01-01), this software will be available under the Apache 2.0 license.

---

## 🙏 Acknowledgments

- Microsoft AutoGen team for the amazing multi-agent framework
- OpenAI for GPT models powering our agents
- The open-source community for invaluable tools and libraries

---

## 📞 Support

- Issues: https://github.com/Roberdan/Convergio/issues
- Discussions: https://github.com/Roberdan/Convergio/discussions

---

## 🚀 Roadmap

### Q4 2025
- [ ] Advanced AI agents marketplace
- [ ] Mobile applications (iOS/Android)
- [ ] Advanced workflow templates library
- [ ] Enhanced multi-language support

### Q1 2026
- [ ] AI model fine-tuning capabilities
- [ ] Advanced analytics dashboard
- [ ] Enterprise SSO integration
- [ ] Compliance certifications (SOC2, ISO)

---

**Built with ❤️ by the Convergio Team**

*Making AI work for humans, not the other way around.*