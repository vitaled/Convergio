# 🚀 Convergio AI Platform
*Human purpose. AI momentum.*

> **Imagine having a super-intelligent command center to manage your business projects, or even your entire company.**

[![CI/CD Pipeline](https://github.com/Roberdan/Convergio/actions/workflows/ci.yml/badge.svg)](https://github.com/Roberdan/Convergio/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit-orange?style=for-the-badge&logo=svelte)](https://kit.svelte.dev/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.7.2-red?style=for-the-badge&logo=microsoft)](https://microsoft.github.io/autogen/)
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue?style=for-the-badge)](LICENSE)
[![Quality Gate](https://img.shields.io/badge/Quality-Enterprise%20Grade-green?style=for-the-badge)](#)
[![Coverage](https://img.shields.io/badge/Coverage-Improving-yellow?style=for-the-badge)](#)

---

## 📚 Documentation

### Business Documentation
- Executive Summary: `docs/executive_summary.md`
- Design Brief: `docs/design_brief.md`
- Project Plan: `docs/project_plan.md`

### Technical Documentation
- **API Reference**: `docs/API_REFERENCE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Agent Optimization**: `backend/docs/AGENT_OPTIMIZATION.md` ✨ NEW
- Technical Gameplan: `docs/technical_gameplan.md`
- Data Science Plan: `docs/data_science_plan.md`

### Live Documentation
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc

---

## 🧾 Logs & Reports

- Performance tests and security audits write JSON reports to `logs/` (ignored by git).
- Default locations:
  - Performance quick test: `logs/performance-results-<timestamp>.json`
  - Security audit: `logs/security-audit-<timestamp>.json`
  - Shell performance suite: `logs/performance-results/` (tar + logs)
- Configuration:
  - Set `LOG_DIR` to override the base logs directory for Python tests.
  - Set `RESULTS_DIR` to override `logs/performance-results` in `scripts/run-performance-tests.sh`.
  - Directories are created automatically if missing.

---

## ⚙️ Model Configuration

- Default backend model: `gpt-5-nano` (cheapest default). Override with env `DEFAULT_AI_MODEL` or per-session in the app.
- Change per-session in the app under Settings → “Default OpenAI Model” (dropdown: gpt-5, gpt-5-mini, gpt-5-nano). The preference is stored per session and used for live OpenAI calls where applicable.
- Official model reference: https://platform.openai.com/docs/models
- Reminder for maintainers: "Roberdan aggiungi qualche info in piu qui, tipo costi, speed, reasoning, etc come dal sito".

---

## 🎯 What is Convergio?

**Convergio is not just software to keep track of things to do, but a platform that actively helps you make decisions, plan strategies, and get work done.**

Convergio transforms how businesses operate by providing an AI-powered command center where **you are the CEO and they are your team of specialists.** You provide the strategic direction, and 41+ specialized AI agents handle execution and analysis.

### 🌟 Core Innovation: A Team of AI Experts at Your Service

The heart of Convergio is its team of over **41 artificial intelligence "agents."** Think of them not as simple chatbots, but as digital colleagues, each with a specific specialization.

| Agent | Role | Specialization |
|-------|------|----------------|
| **Ali** | Chief of Staff | Your right-hand coordinator who orchestrates all other agents |
| **Amy** | CFO | Financial analysis and cost management |
| **Baccio** | Technology Architect | Software architecture and technical design |
| **Sofia** | Marketing Strategist | Marketing strategies and product launches |
| **Luca** | Security Expert | Security and protection protocols |
| **+36 others** | Various Specialists | Project management, HR, design, data analysis, and more |

---

## 🚀 Real-World Examples

### For Project Managers
> *"Prepare a complete plan for the launch of our new product 'Atlas', scheduled for the fourth quarter"*

**What happens:**
- **Ali** (orchestrator) assembles the perfect team
- **Project management agent** creates the timeline
- **Amy** (CFO) estimates the budget and resources
- **Sofia** (Marketing) prepares the launch strategy
- **Result:** A cohesive, comprehensive plan ready for execution

### For Business Strategists
> *"Analyze the feasibility of launching our service in Brazil"*

**What happens:**
- **Business strategy agent** analyzes the market landscape
- **Cultural coaching agent** provides local insights
- **Sales agent** develops market entry strategy
- **Result:** Complete market entry analysis with actionable recommendations

### For Startup Founders
> *"I need a pitch for investors for my fitness app idea"*

**What happens:**
- **Sam** (Y Combinator-inspired startup expert) structures the idea
- **Amy** (CFO) creates financial projections
- **Riccardo** (Storyteller) crafts compelling narrative
- **Result:** Investor-ready pitch deck with financial models

---

## 🔮 The Vision: Democratizing Entrepreneurship

Convergio's ambition goes beyond simple project assistance. **The vision is clear: a single person can manage an entire complex organization** by orchestrating these AI agents.

### Making Enterprise Capabilities Accessible
- **Marketing expertise** (not just for big companies)
- **Financial analysis** (available to startups and solopreneurs)
- **Strategic planning** (democratized for all business sizes)
- **Technical architecture** (enterprise-grade design for everyone)

---

## 🎯 The Agentic Manifesto

> *"Human purpose. AI momentum."* — Milano, 23 June 2025

Convergio is built upon the foundational principles of **The Agentic Manifesto**, ensuring our AI-powered platform serves humanity while maintaining ethical standards and inclusive design.

### What We Believe
1. **Intent is human, momentum is agent** — You set the direction, AI provides the execution power
2. **Impact must reach every mind and body** — Universal accessibility and inclusive design
3. **Trust grows from transparent provenance** — Every decision includes reasoning and attribution
4. **Progress is judged by outcomes, not output** — Results matter more than activity volume

### How We Act
1. **Humans stay accountable** for all decisions and effects
2. **Agents amplify capability**, never replace human identity
3. **We design from the edge first**: disability, language, connectivity
4. **Safety rails precede scale** — Security and ethics built-in
5. **Learn in small loops, ship value early** — Continuous improvement
6. **Bias is a bug** — we detect, test, and fix continuously

---

## 💜 Dedicated to Mario

> *"Every line of code, every design decision, every innovation - dedicated to Mario and his journey with FightTheStroke Foundation"*

Convergio is more than an AI platform - it's a testament to human resilience and the power of technology to amplify human potential. This platform was conceived and built with **Mario** as our guiding inspiration.

### Mario's Influence on Platform Design

**Accessibility-Inspired Design Philosophy:**
- **Mario-inspired design** focusing on clarity and simplicity
- **Clean interface** with intuitive navigation
- **Semantic HTML structure** as foundation for accessibility
- **Planned accessibility features** in development roadmap
- **User-centered design** with empathy-driven interface patterns

**AI Agents as Empowerment Tools:**
- Encouraging feedback built into all interactions
- Gentle error handling that treats mistakes as learning opportunities
- Contextual help without overwhelming the user
- Celebration of progress, no matter how small

---

## 🏗️ Technical Architecture

### Production-Ready Backend Stack
- **Python 3.11+** with FastAPI and async/await patterns
- **AutoGen 0.7.2** for sophisticated multi-agent orchestration
- **PostgreSQL 15+** with pgvector for semantic search
- **Redis 7+** for high-performance caching and session management
- **JWT RS256 Authentication** with military-grade security

### Modern Frontend Experience
- **SvelteKit** with TypeScript for type-safe development
- **TailwindCSS** with custom design system
- **Real-time WebSocket** connections for streaming agent responses
- **Responsive design** with mobile-first approach
- **Progressive Web App** capabilities

### AI & Security Infrastructure
- **41 Specialized Agents** with domain-specific expertise
- **Multi-layer security framework** with 6-tier validation
- **Digital signatures (RSA-2048)** for agent authenticity
- **Prompt injection protection** with advanced attack pattern detection
- **Real-time cost tracking** and optimization

---

## 🚀 Quick Start

### Prerequisiti
Python 3.11+
Node.js 18+
PostgreSQL 15+ con estensione pgvector
Redis 7+
OpenAI API Key

### Installazione & Avvio
```bash
# 1. Clona il repository
git clone https://github.com/Roberdan/Convergio.git
cd Convergio

# 2. Configura gli ambienti
# Copia .env.example in .env sia in backend che in frontend
# Inserisci la tua OpenAI API key e le credenziali del database
# (Opzionale) Imposta il modello di default nel backend/.env con `DEFAULT_AI_MODEL`.
# Di default usiamo `gpt-5-nano` (più economico). Puoi cambiarlo anche dalla pagina Settings del frontend.

# 3. Avvia tutto in locale
./start.sh
```

Questo comando gestisce automaticamente la virtualenv, installa le dipendenze e avvia il backend. Per la parte frontend, segui le istruzioni che appariranno a terminale.

---

> **Nota:** Docker, docker-compose e Makefile non sono più supportati o richiesti. Tutto lo sviluppo e la gestione locale avviene tramite `start.sh`. Per il deploy, segui la guida in `deployment/README.md`.

---

## 🤖 Meet Your AI Agent Ecosystem

### Ali - Chief of Staff (Master Orchestrator)
Central coordination agent that manages all 41+ specialized agents, provides CEO-ready responses, and handles intelligent task delegation with real-time access to your business data.

### Specialized Agent Categories

**Strategic Leadership Team (15+ agents)**  
Amy (CFO), Sofia (Marketing Director), Sam (Startup Expert), Antonio (Strategy Consultant), Satya (Board Advisor)

**Technology & Engineering Team (12+ agents)**  
Baccio (Tech Architect), Marco (DevOps Engineer), Luca (Security Specialist), Jenny (Accessibility Expert), Guardian (AI Security Validator)

**Creative & Design Team (8+ agents)**  
Sara (UX/UI Designer), Jony (Creative Director), Riccardo (Storyteller), Stefano (Design Thinking Facilitator)

**Business Operations Team (6+ agents)**  
Davide (Project Manager), Luke (Program Manager), Andrea (Customer Success), Fabio (Sales Director)

---

## 📊 Current Production Status

**✅ Core Platform Complete**
- All 41 agents operational and extensively tested
- Complete AutoGen 0.7.2 multi-agent orchestration
- Multi-layer security framework with digital signatures
- Real-time cost tracking and optimization engine
- Comprehensive test suite with 100% backend test coverage

**✅ Enterprise Features Ready**
- Agent chat interface with persistent conversation history
- CEO dashboard with real-time business metrics
- Swarm coordination for complex multi-agent tasks
- Vector search with PostgreSQL pgvector integration
- JWT authentication with role-based access control

**✅ Security & Quality**
- 6-tier security validation framework with Guardian AI
- RSA-2048 cryptographic agent verification system
- Advanced prompt injection attack protection
- Complete audit trail of all interactions
- Accessibility considerations built into design process

---

## 🛡️ Security & Compliance

- **Multi-layer Security**: 6-tier validation framework with Guardian AI
- **Digital Signatures**: RSA-2048 cryptographic agent verification
- **Prompt Injection Protection**: Advanced attack pattern detection
- **Accessibility Considerations**: Design process includes accessibility planning
- **Complete Audit Trail**: Every interaction logged and traceable
- **Enterprise Authentication**: JWT RS256 with bcrypt password hashing

---

## 🔮 Future Vision: The Augmented Enterprise

### AI Talent Marketplace
In our roadmap, you'll be able to:
- "Hire" specialized agents on-demand for specific projects
- Create custom agent combinations tailored to your business
- Scale your organization exponentially with AI amplification
- Access enterprise-level expertise regardless of company size

### Democratization of Business Intelligence
Making high-level capabilities accessible to everyone:
- **Strategic consulting** for solo entrepreneurs
- **Financial analysis** for small businesses
- **Market research** for startups
- **Technical architecture** for non-technical founders

---

## ⚖️ Core Values in Action

### 🔍 Transparency
Every agent decision includes full reasoning and source attribution. You can always ask "why" and get a complete explanation.

### 👤 Human Responsibility
Humans maintain final authority over all decisions. Agents propose and execute, but you always have the final say.

### 🌍 Inclusivity & Accessibility
The platform is designed from the ground up to be usable by everyone, breaking down barriers that hinder complex project management.

### 🚀 Outcome-Focused
Success is measured by business impact and human empowerment, not by features or activity metrics.

---

## 📜 License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and development process.

---

## 🏆 The Team

- **Roberto D'Angelo**: Papa, Microsoft Director, and platform visionary
- **Claude & OpenAI o3**: AI development partners
- **FightTheStroke Foundation**: The mission that drives our purpose
- **Mario**: The inspiration for every innovation
- **Global Community**: Contributors who believe in democratizing AI

---

**🎯 Convergio is not software that you *use*, but a team that you *direct*.**

*A platform designed to amplify your capabilities, giving you an entire team of digital experts ready to transform your vision into reality.*

**Designed with ❤️ for Mario and the global community**

---

*"Human purpose. AI momentum." - The Agentic Manifesto*
