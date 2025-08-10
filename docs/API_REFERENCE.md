# Convergio API Reference

## Overview

The Convergio Unified Backend provides a comprehensive REST API for managing AI agents, workflows, talent resources, and vector search capabilities.

**Base URL**: `http://localhost:9000`  
**API Version**: v1  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Authentication

Most endpoints require authentication via JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Health & Status

#### GET /
Returns service information and status.

**Response**:
```json
{
  "service": "Convergio Unified Backend",
  "version": "2.0.0",
  "status": "🚀 Running",
  "environment": "development",
  "features": [...]
}
```

### Agents API

#### GET /api/agents
List all available AI agents.

**Query Parameters**:
- `status` (optional): Filter by status (active, inactive)
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "agents": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "status": "active",
      "capabilities": []
    }
  ],
  "total": 0
}
```

#### POST /api/agents/execute
Execute an agent with specific instructions.

**Request Body**:
```json
{
  "agent_id": "string",
  "prompt": "string",
  "context": {},
  "parameters": {}
}
```

**Response**:
```json
{
  "execution_id": "string",
  "status": "running",
  "result": {},
  "metadata": {}
}
```

### Workflows API

#### GET /api/workflows
List available workflows.

**Response**:
```json
{
  "workflows": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "steps": [],
      "status": "active"
    }
  ]
}
```

#### POST /api/workflows/execute
Execute a workflow.

**Request Body**:
```json
{
  "workflow_id": "string",
  "input_data": {},
  "configuration": {}
}
```

### Talents API

#### GET /api/talents
List talent resources.

**Response**:
```json
{
  "talents": [
    {
      "id": "string",
      "name": "string",
      "skills": [],
      "availability": "available"
    }
  ]
}
```

### Vector Search API

#### POST /api/vector/search
Perform semantic search.

**Request Body**:
```json
{
  "query": "string",
  "top_k": 10,
  "filters": {}
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "string",
      "score": 0.95,
      "content": "string",
      "metadata": {}
    }
  ]
}
```

#### POST /api/vector/embed
Generate embeddings for text.

**Request Body**:
```json
{
  "text": "string",
  "model": "all-MiniLM-L6-v2"
}
```

### Cost Management API

#### GET /api/costs
Get cost analytics.

**Query Parameters**:
- `start_date`: ISO date string
- `end_date`: ISO date string
- `group_by`: daily, weekly, monthly

**Response**:
```json
{
  "total_cost": 0,
  "breakdown": {
    "agents": 0,
    "storage": 0,
    "compute": 0
  },
  "timeline": []
}
```

### WebSocket Endpoints

#### WS /ws/stream
Real-time streaming connection for agent responses.

**Message Format**:
```json
{
  "type": "message|error|complete",
  "data": {},
  "timestamp": "ISO-8601"
}
```

## Error Responses

All endpoints follow a consistent error format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "ISO-8601"
  }
}
```

### Common Error Codes

- `400` - Bad Request: Invalid input parameters
- `401` - Unauthorized: Missing or invalid authentication
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server-side error

## Rate Limiting

Sensitive endpoints are rate-limited:
- `/api/login`: 10 requests per minute
- `/api/agents/execute`: 100 requests per minute
- `/api/costs`: 100 requests per minute

## Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## SDK Examples

### Python
```python
import requests

base_url = "http://localhost:9000"
headers = {"Authorization": "Bearer <token>"}

# Get agents
response = requests.get(f"{base_url}/api/agents", headers=headers)
agents = response.json()

# Execute agent
data = {
    "agent_id": "agent-1",
    "prompt": "Analyze this data"
}
response = requests.post(f"{base_url}/api/agents/execute", 
                         json=data, headers=headers)
```

### JavaScript/TypeScript
```typescript
const baseUrl = "http://localhost:9000";
const headers = {
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
};

// Get agents
const response = await fetch(`${baseUrl}/api/agents`, { headers });
const agents = await response.json();

// Execute agent
const data = {
  agent_id: "agent-1",
  prompt: "Analyze this data"
};
const response = await fetch(`${baseUrl}/api/agents/execute`, {
  method: "POST",
  headers,
  body: JSON.stringify(data)
});
```

## Changelog

### Version 2.0.0 (Current)
- Unified backend architecture
- Enhanced AI agent orchestration
- Improved vector search capabilities
- WebSocket streaming support
- Security enhancements

## Support

For API support and questions:
- GitHub Issues: [github.com/convergio/backend/issues](https://github.com/convergio/backend/issues)
- Documentation: [/docs](http://localhost:9000/docs)
- Email: api-support@convergio.com