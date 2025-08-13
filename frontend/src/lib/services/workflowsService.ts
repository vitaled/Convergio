export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'draft';
  steps: WorkflowStep[];
  created_at: string;
  updated_at: string;
  execution_count: number;
  success_rate: number;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: string;
  configuration: any;
  order: number;
}

export interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  result?: any;
  error_message?: string;
  current_step?: string;
  progress_percentage: number;
}

export interface RecentExecution {
  execution_id: string;
  workflow_name: string;
  status: string;
  started_at: string;
  duration: number;
  success_rate: number;
}

class WorkflowsService {
  private baseUrl = 'http://localhost:9000/api/v1';

  async getWorkflows(): Promise<Workflow[]> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.workflows || [];
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
      throw error;
    }
  }

  async getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/execution/${executionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch workflow execution:', error);
      throw error;
    }
  }

  async getRecentExecutions(): Promise<RecentExecution[]> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/executions/recent`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.executions || [];
    } catch (error) {
      console.error('Failed to fetch recent executions:', error);
      throw error;
    }
  }

  async getWorkflowDetails(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/${workflowId}/details`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch workflow details:', error);
      throw error;
    }
  }
}

export const workflowsService = new WorkflowsService();