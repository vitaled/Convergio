export interface Agent {
  agent_key: string;
  name: string;
  role?: string;
  status: 'active' | 'inactive' | 'busy' | 'error';
  capabilities: string[];
  performance_metrics?: {
    total_tasks: number;
    success_rate: number;
    avg_response_time: number;
  };
  cost_data?: {
    total_cost: number;
    cost_per_interaction: number;
  };
}

export interface SwarmStatus {
  active_agents: number;
  total_tasks: number;
  coordination_patterns: string[];
  performance_overview: {
    efficiency_score: number;
    collaboration_score: number;
    task_completion_rate: number;
  };
}

export interface AgentTask {
  task_id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  assigned_to: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
}

class AgentsService {
  private baseUrl = 'http://localhost:9000/api/v1';

  async getAgents(): Promise<Agent[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/list`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.agents || [];
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      throw error;
    }
  }

  async getSwarmStatus(): Promise<SwarmStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/swarm/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch swarm status:', error);
      throw error;
    }
  }

  async getAgentTasks(): Promise<AgentTask[]> {
    try {
      const response = await fetch(`${this.baseUrl}/swarm/tasks`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.tasks || [];
    } catch (error) {
      console.error('Failed to fetch agent tasks:', error);
      throw error;
    }
  }

  async getAgentProjects(): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/projects`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.projects || [];
    } catch (error) {
      console.error('Failed to fetch agent projects:', error);
      throw error;
    }
  }
}

export const agentsService = new AgentsService();