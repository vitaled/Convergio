# 🤖 Job Description to Agent Generator

## Overview

This feature automatically converts senior-level job descriptions into Convergio AI agents using OpenAI's GPT-4 model.

## Features

### 1. Senior Level Extraction (`job_description_senior_filter.py`)
- Scans job descriptions for senior positions (IC6+, M6+, GM, VP, C-suite)
- Creates separate filtered files for each senior level
- Extracts only relevant content for each level from tables

### 2. AI Agent Generation (`job_description_to_agent_ai.py`)
- Uses OpenAI to intelligently create agent personalities
- Generates complete `.md` files with YAML frontmatter
- Creates professional agent names and descriptions
- Assigns appropriate tools based on profession
- Follows Convergio's agent format standards

## How It Works

### Automatic Agent Discovery
Convergio uses a `DynamicAgentLoader` that:
- Automatically scans the `backend/src/agents/definitions` directory
- Loads all `.md` files as agents
- Parses YAML frontmatter and agent content
- Creates AutoGen agents automatically
- No manual registration required!

### Adding New Agents
1. Place any `.md` file in `backend/src/agents/definitions`
2. The agent is automatically discovered on next system start
3. No code changes needed!

## Usage

### Generate All Senior Agents
```bash
python backend/scripts/generate_all_senior_agents.py
```

### Generate Limited Number (for testing)
```bash
python backend/src/services/job_description_to_agent_ai.py --limit 5
```

### Generate from Custom Directory
```bash
python backend/src/services/job_description_to_agent_ai.py \
  --input-dir /path/to/job/descriptions \
  --output-dir backend/src/agents/definitions
```

## Agent Format

Generated agents follow this structure:

```yaml
---
name: agent-name
description: Brief description (max 200 chars)
tools: ["Read", "WebFetch", "WebSearch", "Grep", "Glob"]
color: "#16A085"
---

You are **Agent Name** — role description...

## Security & Ethics Framework
...

## Core Identity
...

## Core Competencies
...

## Communication Protocols
...
```

## Tool Assignment

Tools are automatically assigned based on profession:
- **Technical**: Full development tools (Read, Write, Edit, Bash, etc.)
- **Finance**: Analysis tools (Read, WebFetch, WebSearch, Grep)
- **Management**: Organization tools (TodoWrite, Task)
- **Operations**: System tools (Bash, Glob, TodoWrite)

## Files Generated

- **Senior Job Descriptions**: `jobDescriptions/senior/`
- **Generated Agents**: `backend/src/agents/definitions/`
- **Results**: `ai_generation_results.json`

## Requirements

- OpenAI API key in `.env` file
- Python 3.8+
- Job descriptions in `jobDescriptions/md/`

## Cost Estimate

- Each agent generation uses ~3,000-4,000 tokens
- Approximate cost: $0.10-0.15 per agent with GPT-4

## Integration

New agents are automatically integrated into Convergio:
1. No code changes required
2. Agents appear in Ali's routing system
3. Available for orchestration immediately
4. Classified by tier automatically

## Example Output

From job description `FIN_TAX_CSP_IC6.md`:
→ Generated agent: `sophia-tax.md`

The agent will have:
- Professional name and role
- Comprehensive competencies
- Specialized methodologies
- Success metrics
- Integration guidelines