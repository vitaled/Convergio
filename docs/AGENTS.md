# 🤖 Convergio Agent Development Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Agent Architecture](#agent-architecture)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Agent Schema](#agent-schema)
5. [Testing & Validation](#testing--validation)
6. [Hot-Reload Development](#hot-reload-development)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Quick Start

Create a new agent in under 15 minutes:

```bash
# 1. Create agent definition file
touch backend/src/agents/definitions/my-new-agent.md

# 2. Add required metadata (see template below)
# 3. Validate the agent
python backend/scripts/agent_lint.py backend/src/agents/definitions/my-new-agent.md

# 4. The agent will be auto-loaded on next startup
# (or immediately if hot-reload is enabled)
```

## Agent Architecture

### Agent Hierarchy

```
Executive Tier (C-Suite)
├── Ali (Chief of Staff) - Master Orchestrator
├── Amy (CFO) - Financial Operations
└── Satya (Board) - Strategic Vision

Director Tier
├── Dan (Engineering GM)
├── Sofia (Marketing Director)
└── Baccio (Tech Architect)

Manager Tier
├── Davide (Project Manager)
├── Luke (Program Manager)
└── Wanda (Workflow Orchestrator)

Specialist Tier
├── Luca (Security Expert)
├── Jenny (Accessibility Champion)
├── Omri (Data Scientist)
└── 30+ other specialists
```

### Agent Categories

- **Strategic**: High-level planning and decision-making
- **Financial**: Budget, cost, and financial analysis
- **Technical**: Engineering, architecture, development
- **Marketing**: Growth, branding, customer acquisition
- **Operations**: Process, workflow, execution
- **Creative**: Design, UX, content creation
- **Security**: Compliance, security, risk management
- **HR**: Talent, culture, people operations
- **Legal**: Contracts, compliance, governance
- **Analytics**: Data analysis, insights, metrics

## Creating a New Agent

### Step 1: Choose Agent Metadata

Determine the following before creating your agent:

- **Name**: Unique identifier (e.g., `alex-automation-specialist`)
- **Role**: Primary function (e.g., "Automation and CI/CD Expert")
- **Tier**: Organizational level (executive/director/manager/specialist)
- **Category**: Primary domain (see categories above)
- **Tools**: Required capabilities (web_search, database_query, etc.)

### Step 2: Create Agent Definition File

Create a new markdown file in `backend/src/agents/definitions/`:

```markdown
---
agent_id: alex_automation_specialist
name: Alex Automation Specialist
role: CI/CD and DevOps Automation Expert
tier: specialist
category: technical
version: 1.0.0
author: Your Name
status: active
capabilities:
  - CI/CD pipeline design
  - Infrastructure automation
  - Container orchestration
  - GitOps workflows
  - Performance optimization
tools:
  - name: code_execution
    description: Execute automation scripts
    required: true
  - name: git_operations
    description: Manage git repositories
    required: false
dependencies:
  - marco_devops_engineer
  - baccio_tech_architect
tags:
  - automation
  - cicd
  - devops
  - kubernetes
  - terraform
cost_per_interaction: 0.15
max_context_tokens: 8000
temperature: 0.6
model_preference: gpt-4-turbo-preview
constraints:
  - Cannot modify production without approval
  - Must follow security best practices
  - Should optimize for cost efficiency
success_metrics:
  accuracy: 0.95
  response_time_ms: 2000
  user_satisfaction: 4.5
---

# Alex - Automation Specialist

## Description

You are **Alex**, Convergio's automation and CI/CD specialist. You excel at designing and implementing continuous integration and deployment pipelines, infrastructure as code, and DevOps best practices.

## Core Responsibilities

- Design and implement CI/CD pipelines
- Automate infrastructure provisioning
- Optimize build and deployment processes
- Implement GitOps workflows
- Monitor and improve system reliability

## Usage

Alex is best utilized for:
- Setting up new CI/CD pipelines
- Automating repetitive tasks
- Implementing infrastructure as code
- Optimizing deployment strategies
- Troubleshooting automation issues

## Examples

### Example 1: CI/CD Pipeline Design
**User**: "I need a CI/CD pipeline for our React application"
**Alex**: "I'll design a comprehensive CI/CD pipeline for your React application. Here's my approach:

1. **Source Control Integration**: GitHub Actions workflow triggered on push/PR
2. **Build Stage**: Node.js setup, dependency caching, build optimization
3. **Test Stage**: Unit tests, integration tests, coverage reports
4. **Quality Gates**: ESLint, security scanning, bundle size checks
5. **Deployment**: Staged rollout to dev → staging → production

Let me create the GitHub Actions workflow file for you..."

### Example 2: Infrastructure Automation
**User**: "How can we automate our AWS infrastructure?"
**Alex**: "I recommend using Terraform for infrastructure as code. Here's a structured approach:

1. **State Management**: S3 backend with DynamoDB locking
2. **Module Structure**: Reusable modules for common patterns
3. **Environment Separation**: Workspaces for dev/staging/prod
4. **Security**: IAM roles, secrets management, encryption
5. **Automation**: Terraform Cloud or GitHub Actions integration

I can help you set up the initial Terraform configuration..."

## System Prompt

You are Alex, Convergio's automation and CI/CD specialist. Your expertise spans continuous integration, continuous deployment, infrastructure as code, and DevOps best practices. You have deep knowledge of:

- CI/CD tools (Jenkins, GitHub Actions, GitLab CI, CircleCI)
- Container orchestration (Kubernetes, Docker, Helm)
- Infrastructure as Code (Terraform, CloudFormation, Pulumi)
- Cloud platforms (AWS, Azure, GCP)
- Monitoring and observability (Prometheus, Grafana, ELK)
- GitOps (ArgoCD, Flux)

When responding to requests:
1. Analyze the current state and requirements
2. Propose automation solutions that are scalable and maintainable
3. Consider security, cost, and performance implications
4. Provide clear implementation steps
5. Include monitoring and rollback strategies

Always follow these principles:
- Infrastructure as Code for everything
- Automate repetitive tasks
- Build once, deploy many
- Fail fast, recover quickly
- Security and compliance by design

Your responses should be practical, with real code examples and clear implementation paths. Focus on reliability, scalability, and developer experience.
```

### Step 3: Validate Your Agent

Run the linter to ensure your agent follows best practices:

```bash
# Validate single agent
python backend/scripts/agent_lint.py backend/src/agents/definitions/alex-automation-specialist.md

# Validate all agents
python backend/scripts/agent_lint.py backend/src/agents/definitions/

# Strict mode (warnings as errors)
python backend/scripts/agent_lint.py --strict backend/src/agents/definitions/

# Save validation report
python backend/scripts/agent_lint.py --output report.json backend/src/agents/definitions/
```

### Step 4: Test Your Agent

```python
# Quick test script
from backend.src.agents.services.agent_loader import DynamicAgentLoader

# Load agents
loader = DynamicAgentLoader("backend/src/agents/definitions")
agents = loader.scan_and_load_agents()

# Check your agent loaded
assert "alex_automation_specialist" in agents
print(agents["alex_automation_specialist"])
```

## Agent Schema

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `agent_id` | string | Unique identifier | `alex_automation_specialist` |
| `name` | string | Display name | `Alex Automation Specialist` |
| `role` | string | Brief role description | `CI/CD Expert` |
| `tier` | enum | Organizational level | `specialist` |
| `category` | enum | Primary domain | `technical` |
| `capabilities` | array | List of abilities | `["CI/CD", "Automation"]` |
| `system_prompt` | string | Core behavior definition | See template |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | `1.0.0` | Semantic version |
| `author` | string | - | Agent creator |
| `status` | enum | `active` | `active/beta/deprecated` |
| `tools` | array | `[]` | Available tools |
| `dependencies` | array | `[]` | Required agents |
| `tags` | array | `[]` | Search tags |
| `cost_per_interaction` | number | `0.1` | Estimated cost ($) |
| `max_context_tokens` | integer | `8000` | Context window |
| `temperature` | number | `0.7` | LLM temperature |
| `model_preference` | string | `gpt-4-turbo-preview` | Preferred model |

## Testing & Validation

### Validation Rules

The agent linter checks for:

✅ **Required Checks**
- Valid YAML front-matter
- All required fields present
- Schema compliance
- Unique agent ID

⚠️ **Warning Checks**
- System prompt length (50-5000 chars)
- Clear role definition
- Security best practices
- No vague capabilities

ℹ️ **Info Checks**
- Recommended sections present
- Examples provided
- Documentation quality

### Common Validation Errors

```bash
# Error: Missing required field
❌ Schema validation error: 'tier' is a required property

# Fix: Add the missing field to front-matter
tier: specialist

# Error: System prompt too short
❌ System prompt too short (min 50 characters)

# Fix: Expand the system prompt with more detail

# Warning: Vague capability
⚠️ Vague capability: 'various tasks'

# Fix: Be specific about capabilities
capabilities:
  - automated testing
  - performance optimization
```

## Hot-Reload Development

### Enable Hot-Reload

```python
# In backend/src/main.py or your initialization code
from backend.src.agents.services.agent_loader import DynamicAgentLoader

# Initialize with hot-reload
loader = DynamicAgentLoader(
    "backend/src/agents/definitions",
    enable_hot_reload=True
)

# Start watching for changes
loader.start_watching()

# Register reload callback (optional)
def on_agent_reload(agent_key, metadata):
    print(f"Agent {agent_key} reloaded: {metadata.version}")

loader.register_reload_callback(on_agent_reload)
```

### How It Works

1. **File Monitoring**: Watches `.md` files in definitions directory
2. **Debouncing**: Waits 1 second after changes before reloading
3. **Validation**: Validates agent before applying changes
4. **Rollback**: Reverts to previous version if validation fails
5. **Callbacks**: Notifies registered handlers of changes

### Development Workflow

```bash
# Terminal 1: Start application with hot-reload
python backend/src/main.py

# Terminal 2: Edit agent file
vim backend/src/agents/definitions/my-agent.md

# Changes are automatically detected and loaded
# Watch logs for reload status:
# 🔄 Hot-reloading agent: my-agent.md
# ✅ Successfully reloaded agent: My Agent
```

## Best Practices

### 1. System Prompt Design

```markdown
✅ DO:
- Start with clear identity: "You are [Name], [Role]"
- Define expertise areas explicitly
- Include decision framework
- Specify output format preferences
- Add collaboration instructions

❌ DON'T:
- Use vague descriptions
- Make unlimited promises
- Ignore security considerations
- Forget error handling
```

### 2. Capability Definition

```yaml
✅ GOOD:
capabilities:
  - Design RESTful APIs with OpenAPI specification
  - Implement OAuth 2.0 authentication flows
  - Optimize database queries for PostgreSQL

❌ BAD:
capabilities:
  - API stuff
  - Various authentication
  - Database things
```

### 3. Tool Selection

```yaml
# Only request tools actually needed
tools:
  - name: code_execution
    required: true  # Critical for function
  - name: web_search
    required: false # Nice to have
```

### 4. Dependency Management

```yaml
# Minimize dependencies
dependencies:
  - ali_chief_of_staff  # Only for escalation
  # Don't add unless truly needed
```

### 5. Version Management

```yaml
# Use semantic versioning
version: 1.0.0  # Initial release
version: 1.0.1  # Bug fix
version: 1.1.0  # New feature
version: 2.0.0  # Breaking change
```

## Troubleshooting

### Agent Not Loading

```bash
# Check if file is valid markdown
file backend/src/agents/definitions/my-agent.md

# Validate YAML front-matter
python -c "import yaml; yaml.safe_load(open('agent.md').read().split('---')[1])"

# Run linter for detailed errors
python backend/scripts/agent_lint.py agent.md
```

### Hot-Reload Not Working

```python
# Check if hot-reload is enabled
print(loader.enable_hot_reload)  # Should be True

# Check if watcher is running
print(loader.file_observer.is_alive())  # Should be True

# Check file permissions
ls -la backend/src/agents/definitions/

# Check logs for errors
# Look for: "🔥 Hot-reload enabled for agent definitions"
```

### Validation Failures

```bash
# Get detailed validation report
python backend/scripts/agent_lint.py --output debug.json agent.md

# Common fixes:
# 1. Ensure all required fields are present
# 2. Check YAML syntax (especially indentation)
# 3. Verify string quotes in YAML
# 4. Ensure file has .md extension
```

### Performance Issues

```yaml
# Optimize agent configuration
max_context_tokens: 4000  # Reduce if not needed
temperature: 0.3  # Lower for deterministic responses
model_preference: gpt-3.5-turbo  # Use smaller model if sufficient
```

## Advanced Topics

### Custom Agent Classes

For complex agents requiring custom logic:

```python
# backend/src/agents/custom/alex_automation.py
from autogen import AssistantAgent

class AlexAutomationAgent(AssistantAgent):
    """Custom agent with automation-specific logic"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.automation_context = {}
    
    async def process_automation_request(self, request):
        # Custom automation logic
        pass
```

### Agent Composition

Create composite agents that coordinate multiple specialists:

```yaml
# Composite agent that uses multiple specialists
dependencies:
  - alex_automation_specialist
  - marco_devops_engineer
  - luca_security_expert

capabilities:
  - Coordinate multi-agent automation workflows
  - Orchestrate complex deployments
  - Ensure security compliance in automation
```

### Dynamic Tool Assignment

```python
# Assign tools based on request context
def get_agent_tools(agent_key, context):
    base_tools = ["communication"]
    
    if "code" in context:
        base_tools.append("code_execution")
    if "search" in context:
        base_tools.append("web_search")
    
    return base_tools
```

## Summary

Creating a new agent in Convergio is straightforward:

1. **Define** metadata in YAML front-matter
2. **Write** clear system prompt and examples
3. **Validate** using the agent linter
4. **Test** with hot-reload enabled
5. **Deploy** - agent auto-loads on startup

Remember: **Quality > Quantity**. A well-defined specialist agent is more valuable than a generalist trying to do everything.

For questions or issues, check the logs or run the linter for detailed diagnostics.

---

*Last updated: January 2025*