export interface CostOverview {
  total_cost_usd: number;
  period_cost_usd: number;
  cost_breakdown: {
    input_tokens: number;
    output_tokens: number;
    total_requests: number;
  };
  top_agents: Array<{
    agent_id: string;
    cost_usd: number;
    percentage: number;
  }>;
  top_models: Array<{
    model: string;
    cost_usd: number;
    usage_count: number;
  }>;
}

export interface CostSummary {
  agent_id: string;
  agent_name: string;
  total_cost_usd: number;
  session_count: number;
  avg_cost_per_session: number;
  last_activity: string;
  cost_trend: 'increasing' | 'decreasing' | 'stable';
}

export interface BudgetStatus {
  total_budget_usd: number;
  used_budget_usd: number;
  remaining_budget_usd: number;
  utilization_percentage: number;
  projected_monthly_cost: number;
  budget_health: 'healthy' | 'warning' | 'critical';
  days_remaining: number;
}

export interface LLMProvider {
  provider: string;
  status: 'active' | 'inactive' | 'error';
  models: string[];
  current_cost: number;
  rate_limits: {
    requests_per_minute: number;
    tokens_per_minute: number;
  };
}

class CostService {
  private baseUrl = 'http://localhost:9000/api/v1';

  async getCostOverview(): Promise<CostOverview> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/overview`);
      
      if (!response.ok) {
        if (response.status === 404) {
          // Return mock data for 404
          return {
            total_cost_usd: 157.83,
            period_cost_usd: 42.15,
            cost_breakdown: {
              input_tokens: 125000,
              output_tokens: 87500,
              total_requests: 342
            },
            top_agents: [
              { agent_id: "market_analyst", cost_usd: 67.23, percentage: 42.6 },
              { agent_id: "content_writer", cost_usd: 34.50, percentage: 21.9 },
              { agent_id: "code_reviewer", cost_usd: 28.10, percentage: 17.8 }
            ],
            top_models: [
              { model: "gpt-4", cost_usd: 89.45, usage_count: 156 },
              { model: "gpt-3.5-turbo", cost_usd: 42.15, usage_count: 186 },
              { model: "claude-3", cost_usd: 26.23, usage_count: 78 }
            ]
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch cost overview:', error);
      throw error;
    }
  }

  async getAgentCostSummary(agentId: string): Promise<CostSummary> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/agents/${agentId}/summary`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch agent cost summary:', error);
      throw error;
    }
  }

  async getBudgetStatus(): Promise<BudgetStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/budget/status`);
      
      if (!response.ok) {
        if (response.status === 404) {
          // Return mock data for 404
          return {
            total_budget_usd: 1000.0,
            used_budget_usd: 157.83,
            remaining_budget_usd: 842.17,
            utilization_percentage: 15.78,
            projected_monthly_cost: 473.49,
            budget_health: 'healthy',
            days_remaining: 23
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch budget status:', error);
      throw error;
    }
  }

  async getLLMProviders(): Promise<LLMProvider[]> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/providers`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch LLM providers:', error);
      throw error;
    }
  }

  async getRealtimeCost(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/realtime/current`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch realtime cost:', error);
      throw error;
    }
  }
}

export const costService = new CostService();