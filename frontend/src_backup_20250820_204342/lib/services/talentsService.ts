export interface Talent {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  is_admin?: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TalentHierarchy {
  talent: Talent;
  subordinates: Talent[];
  hierarchy_level: number;
}

class TalentsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:9000'}/api/v1`;

  async getTalents(): Promise<Talent[]> {
    try {
      const response = await fetch(`${this.baseUrl}/talents`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch talents:', error);
      throw error;
    }
  }

  async getTalent(id: number): Promise<Talent> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch talent:', error);
      throw error;
    }
  }

  async getTalentHierarchy(id: number): Promise<TalentHierarchy> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}/hierarchy`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch talent hierarchy:', error);
      throw error;
    }
  }
}

export const talentsService = new TalentsService();