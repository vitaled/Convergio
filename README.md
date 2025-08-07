# 🚀 Convergio AI Platform

> **AI-powered business orchestration platform with 41+ specialized agents**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit-orange?style=for-the-badge&logo=svelte)](https://kit.svelte.dev/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.7.2-red?style=for-the-badge&logo=microsoft)](https://microsoft.github.io/autogen/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-blue.svg?style=for-the-badge)](LICENSE)

---

## 🎯 What is Convergio?

Convergio transforms how businesses operate by providing an AI-powered command center where users can manage complex organizations through intelligent agent orchestration. The platform democratizes access to high-level business expertise, making enterprise-grade capabilities available to startups and growing companies.

**Core Value:**
- **41+ Specialized AI Agents**: Expert-level assistance across all business functions
- **Real-time Collaboration**: Agents work together on complex multi-step tasks
- **Production Ready**: Built with enterprise security and scalability
- **Zero Learning Curve**: Natural language interface with intelligent task delegation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Redis 7+
- OpenAI API Key

### Installation
```bash
# 1. Clone repository
git clone https://github.com/Roberdan/Convergio.git
cd Convergio

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend setup
cd ../frontend
npm install

# 4. Environment configuration
# Copy .env.example to .env in both backend and frontend
# Add your OpenAI API key and database credentials

# 5. Start services
# Terminal 1: Backend
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev -- --port 4000
```

### Using Docker
```bash
# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:4000
# Backend API: http://localhost:9000
```

---

## 🎯 The Agentic Manifesto

> *"Human purpose. AI momentum."* — Milano, 23 June 2025

Convergio is built upon the foundational principles of **The Agentic Manifesto**, ensuring that our AI-powered platform serves humanity while maintaining ethical standards and inclusive design.

### Core Beliefs

#### 1. Intent is human, momentum is agent
- **Human Strategic Direction**: Users define goals, vision, and strategic decisions
- **AI Execution Power**: Agents provide the momentum to transform ideas into reality
- **Preserved Autonomy**: Humans maintain control over direction while AI accelerates execution

#### 2. Impact must reach every mind and body
- **Universal Accessibility**: WCAG 2.1 AA compliance ensures platform usability for all abilities
- **Inclusive Design**: Multi-language support and cultural sensitivity built-in
- **Democratized Expertise**: Enterprise-level capabilities accessible to startups and individuals

#### 3. Trust grows from transparent provenance
- **Explainable AI**: Every agent decision includes reasoning and source attribution
- **Audit Trail**: Complete logging of all interactions and decision points
- **Open Methodology**: Clear documentation of how agents reach conclusions

#### 4. Progress is judged by outcomes, not output
- **Results-Oriented Metrics**: Success measured by business impact, not activity volume
- **Quality over Quantity**: Focus on meaningful insights rather than information overload
- **ROI-Driven Development**: Features prioritized by user value and business outcomes

---

## 💜 Dedicated to Mario

> *"Every line of code, every design decision, every innovation - dedicated to Mario and his journey with FightTheStroke Foundation"*

Convergio is more than an AI platform - it's a testament to human resilience and the power of technology to amplify human potential. This platform was conceived and built with **Mario** as our guiding inspiration, ensuring that every feature serves not just business efficiency, but human dignity and empowerment.

### Mario's Influence on Platform Design

**Accessibility-First Architecture:**
- WCAG 2.1 AA compliance for every interface element
- Voice command integration for hands-free operation
- High contrast UI for visual clarity
- Complete keyboard navigation support
- Screen reader compatibility with full semantic markup

**AI Agents as Empowerment Tools:**
- Patient response patterns that adapt to user pace
- Encouraging feedback built into all interactions
- Gentle error handling that treats mistakes as learning opportunities
- Contextual help without overwhelming the user
- Celebration of progress, no matter how small

---

## 🏗️ Technical Architecture

### Backend Stack
- **Python 3.11+** with FastAPI and async/await patterns
- **AutoGen 0.7.2** for multi-agent orchestration
- **PostgreSQL 15+** with pgvector for vector search
- **Redis 7+** for caching and session management
- **JWT Authentication** with RSA-256 security

### Frontend Stack
- **SvelteKit** with TypeScript and TailwindCSS
- **Real-time WebSocket** connections for streaming responses
- **Responsive Design** with mobile-first approach
- **Dark Mode** support with user preference persistence

### AI & Security
- **41 Specialized Agents** with domain expertise
- **Multi-layer Security** with prompt injection protection
- **Digital Signatures** for agent authenticity
- **Real-time Cost Tracking** and optimization

---

## 🤖 AI Agent Ecosystem

### Ali - Chief of Staff (Master Orchestrator)
Central coordination agent that manages all 41+ specialized agents, provides CEO-ready responses, and handles intelligent task delegation with real-time access to business data.

### Specialized Agent Categories

**Strategic Leadership (15+ agents)**  
Amy (CFO), Sofia (Marketing), Sam (Startup Expert), Antonio (Strategy), Satya (Board of Directors)

**Technology & Engineering (12+ agents)**  
Baccio (Tech Architect), Marco (DevOps), Luca (Security), Jenny (Accessibility), Guardian (AI Security)

**Creative & Design (8+ agents)**  
Sara (UX/UI Designer), Jony (Creative Director), Riccardo (Storyteller), Stefano (Design Thinking)

**Business Operations (6+ agents)**  
Davide (Project Manager), Luke (Program Manager), Andrea (Customer Success), Fabio (Sales)

---

## 📊 Current Status

**✅ Production Ready**
- All 41 agents operational and tested
- Complete AutoGen 0.7.2 integration
- Multi-layer security framework implemented
- Real-time cost tracking and optimization
- Comprehensive test suite (100% backend tests passing)

**✅ Core Features Complete**
- Agent chat interface with persistent history
- CEO dashboard with real-time metrics
- Swarm coordination for multi-agent tasks
- Vector search with PostgreSQL pgvector
- JWT authentication and role-based access

---

## 🛡️ Security & Compliance

- **Multi-layer Security**: 6-tier validation framework
- **Digital Signatures**: RSA-2048 cryptographic agent verification  
- **Prompt Injection Protection**: Advanced attack pattern detection
- **WCAG 2.1 AA Compliance**: Full accessibility support
- **Audit Trail**: Complete logging of all interactions

---

## 📜 License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and development process.

---

**🎯 Convergio AI Platform: Transforming Business Operations Through Intelligent Agent Orchestration**

*Designed with ❤️ for Mario and the global community*