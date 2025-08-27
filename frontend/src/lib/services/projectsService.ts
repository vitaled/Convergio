export interface Client {
  id: number;
  name: string;
  email: string;
  created_at?: string;
  updated_at?: string;
}

export interface Activity {
  id: number;
  title: string;
  description?: string;
  status: 'planning' | 'in-progress' | 'review' | 'completed';
  progress: number;
  created_at?: string;
  updated_at?: string;
}

export interface Engagement {
  id: number;
  title: string;
  description?: string;
  status: 'planning' | 'in-progress' | 'review' | 'completed' | 'on_hold';
  progress: number;
  created_at?: string;
  updated_at?: string;
}

export interface EngagementDetail {
  id: number;
  title: string;
  description?: string;
  status: 'planning' | 'in-progress' | 'review' | 'completed' | 'on_hold';
  progress: number;
  created_at?: string;
  updated_at?: string;
  activities: Activity[];
}

export interface ProjectOverview {
  total_engagements: number;
  status_breakdown: Record<string, number>;
  active_engagements: number;
  recent_engagements: Engagement[];
}

export interface EngagementCreate {
  title: string;
  description?: string;
  status?: string;
}

class ProjectsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:9000'}/api/v1`;

  async getProjectOverview(): Promise<ProjectOverview> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/overview`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch project overview:', error);
      throw error;
    }
  }

  async getClients(): Promise<Client[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/clients`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.clients || data; // Handle both formats
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      throw error;
    }
  }

  async getEngagements(): Promise<Engagement[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.engagements || data; // Handle both formats
    } catch (error) {
      console.error('Failed to fetch engagements:', error);
      throw error;
    }
  }

  async getClient(id: number): Promise<Client> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/clients/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch client:', error);
      throw error;
    }
  }

  async getEngagement(id: number): Promise<Engagement> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch engagement:', error);
      throw error;
    }
  }

  async getEngagementDetails(id: number): Promise<EngagementDetail> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements/${id}/details`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch engagement details:', error);
      throw error;
    }
  }

  async getActivities(): Promise<Activity[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/activities`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.activities || data; // Handle both formats
    } catch (error) {
      console.error('Failed to fetch activities:', error);
      throw error;
    }
  }

  async createEngagement(engagement: EngagementCreate): Promise<Engagement> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(engagement)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to create engagement:', error);
      throw error;
    }
  }
}

export const projectsService = new ProjectsService();