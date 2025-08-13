<script lang="ts">
  import { onMount } from 'svelte';
  import AgentIcons from '$lib/components/AgentIcons.svelte';
  import AgentStatus from '$lib/components/AgentStatus.svelte';
  import ConversationManager from '$lib/components/ConversationManager.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import { conversationManager, currentAgentId } from '$lib/stores/conversationStore';

  interface Agent {
    id: number;
    name: string;
    role: string;
    description: string;
    specialty: string;
    personality: string;
    is_featured: boolean;
    key?: string;  // Backend agent key
    cost_data?: {
      total_cost_usd: number;
      total_calls: number;
      avg_cost_per_call: number;
      last_updated: string;
    };
  }

  interface Message {
    id: number | string;
    type: string;
    content: string;
    timestamp: Date;
    agents_used?: string[];
  }

  // Search functionality
  let searchQuery = '';
  let selectedSkill = '';
  
  // Conversation management
  let showConversationManager = false;
  
  // Dynamic AI agents list - loaded from API
  let allAgents: Agent[] = [];
  let isLoadingAgents = true;
  let loadingError: string | null = null;
  
  // Show hire new agent form
  let showHireForm = false;
  
  // Agent creation form data
  let newAgentForm = {
    name: '',
    role: '',
    description: '',
    specialty: '',
    personality: '',
    color: '#666666',
    tools: [] as string[],
    expertise_areas: [] as string[],
    additional_content: ''
  };
  let isCreatingAgent = false;
  let creationError: string | null = null;
  let creationSuccess = false;
  
  // Static fallback agents (kept for offline/error scenarios)
  const fallbackAgents: Agent[] = [
    {
      id: 1,
      name: "Ali",
      key: "ali_chief_of_staff",  // Backend agent key
      role: "Chief of Staff",
      description: "Strategic coordinator and master orchestrator",
      specialty: "Executive assistance, team coordination, strategic planning",
      personality: "Diplomatic, strategic, always sees the bigger picture",
      is_featured: true
    },
    {
      id: 2,
      name: "Amy",
      key: "amy_cfo",
      role: "CFO", 
      description: "Financial analysis and strategic planning",
      specialty: "Financial modeling, budgeting, investment analysis",
      personality: "Analytical, detail-oriented, fiscally responsible",
      is_featured: true
    },
    {
      id: 3,
      name: "Baccio",
      key: "baccio_tech_architect",
      role: "Tech Architect",
      description: "System architecture and technical strategy",
      specialty: "Cloud architecture, scalability, technical decision-making",
      personality: "Innovative, pragmatic, loves elegant solutions",
      is_featured: true
    }
  ];

  // Function to capitalize first letter of each specialty
  function capitalizeSpecialty(specialty: string): string {
    return specialty.split(', ').map(skill => 
      skill.charAt(0).toUpperCase() + skill.slice(1)
    ).join(', ');
  }

  // Extract unique skills for filter
  $: allSkills = [...new Set(allAgents.map(agent => agent.specialty.split(', ')).flat())]
    .map(skill => skill.charAt(0).toUpperCase() + skill.slice(1));

  // Featured agents (top 6)
  $: featuredAgents = allAgents.filter(agent => agent.is_featured);

  // Load agents from API
  async function loadAgentsFromAPI() {
    isLoadingAgents = true;
    loadingError = null;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agent-management/agents`);
      if (response.ok) {
        const data = await response.json();
        
        // Transform backend agent data to frontend format
        const transformedAgents = data.agents.map((backendAgent: any, index: number) => ({
          id: index + 1,
          name: backendAgent.name,
          key: backendAgent.key,
          role: backendAgent.description || 'AI Agent',
          description: backendAgent.description,
          specialty: backendAgent.expertise_count > 0 ? 'AI-powered specialist' : 'General AI assistant',
          personality: 'Intelligent, helpful, specialized',
          is_featured: index < 6 // First 6 are featured
        }));
        
        allAgents = transformedAgents;
        console.log(`✅ Loaded ${allAgents.length} agents from API`);
      } else {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to load agents from API:', error);
      loadingError = error instanceof Error ? error.message : 'Unknown error';
      
      // Fallback to static agents
      allAgents = fallbackAgents;
      console.log('📋 Using fallback agents');
    } finally {
      isLoadingAgents = false;
    }
  }

  // Filtered agents based on search
  $: filteredAgents = allAgents.filter(agent => {
    const matchesSearch = !searchQuery || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.specialty.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesSkill = !selectedSkill || 
      agent.specialty.toLowerCase().includes(selectedSkill.toLowerCase());
    
    return matchesSearch && matchesSkill;
  });

  let selectedAgent = fallbackAgents[0];
  
  onMount(() => {
    // Load agents and initialize
    (async () => {
      await loadAgentsFromAPI();
      
      // Initialize with first featured agent when available
      if (featuredAgents.length > 0) {
        selectedAgent = featuredAgents[0];
      }
    })();
  });
</script>

<svelte:head>
  <title>AI Team - platform.Convergio.io</title>
</svelte:head>

<!-- AI Agents Page -->
<div class="space-y-6">
  <!-- Header -->
  <div>
    <h1 class="text-lg font-medium text-gray-900">AI Team</h1>
    <p class="mt-1 text-xs text-gray-500">Your specialized AI agents powered by Microsoft AutoGen</p>
  </div>

  <div class="grid lg:grid-cols-5 gap-8">
    <!-- Agents List with integrated search -->
    <div class="lg:col-span-2">
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <!-- Search in header -->
        <div class="p-4 border-b border-gray-100 bg-gray-50">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-gray-900">AI Team</h3>
            <!-- Hire New Agent Button -->
            <button
              on:click={() => showHireForm = true}
              class="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center space-x-1"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              <span>Hire Agent</span>
            </button>
          </div>
          <div class="space-y-3">
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Search agents by name, role, or skills..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
            <select
              bind:value={selectedSkill}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">All Specialties</option>
              {#each allSkills.slice(0, 12) as skill}
                <option value={skill}>{skill}</option>
              {/each}
            </select>
          </div>
          
          <div class="flex items-center justify-between text-xs mt-3 pt-3 border-t border-gray-200">
            <div class="flex items-center space-x-2">
              <span class="text-gray-600">{filteredAgents.length} of {allAgents.length} available</span>
              {#if isLoadingAgents}
                <div class="flex items-center space-x-1 text-blue-600">
                  <div class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>Loading...</span>
                </div>
              {:else if loadingError}
                <div class="flex items-center space-x-1 text-red-600">
                  <div class="w-1.5 h-1.5 bg-red-500 rounded-full"></div>
                  <span>Fallback mode</span>
                </div>
              {/if}
            </div>
            <div class="flex items-center space-x-1 text-blue-600">
              <div class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Powered by AutoGen</span>
            </div>
          </div>
        </div>
        
        <!-- Agents List -->
        <div class="max-h-[500px] overflow-y-auto">
          <div class="divide-y divide-gray-100">
            {#each filteredAgents as agent}
              <button
                on:click={() => selectedAgent = agent}
                class="w-full p-3 hover:bg-gray-50 transition-colors text-left group {selectedAgent.id === agent.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''}"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center border border-gray-200 bg-white group-hover:border-blue-300 transition-colors">
                    <AgentIcons agentName={agent.name} size="w-4 h-4" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <div class="font-medium text-gray-900 text-sm">{agent.name}</div>
                    </div>
                    <div class="text-xs text-gray-500">{agent.role}</div>
                    <div class="text-xs text-gray-400 truncate mt-0.5">{capitalizeSpecialty(agent.specialty)}</div>
                  </div>
                  <div class="flex flex-col items-end space-y-1">
                    {#if agent.key}
                      <AgentStatus agentId={agent.key} agentName={agent.name} compact={true} />
                    {:else}
                      <div class="flex items-center space-x-1 px-2 py-1 bg-gray-100 rounded-full">
                        <div class="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        <span class="text-xs text-gray-500 font-medium">Ready</span>
                      </div>
                    {/if}
                  </div>
                </div>
              </button>
            {/each}
            
            {#if filteredAgents.length === 0}
              <div class="text-center py-8 text-gray-500">
                <div class="text-sm mb-2">No agents found</div>
                <button 
                  on:click={() => { searchQuery = ''; selectedSkill = ''; }}
                  class="text-blue-600 hover:text-blue-800 underline text-sm font-medium"
                >
                  Clear filters
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Right Side - Selected Agent Info -->
    <div class="lg:col-span-3">
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <div class="flex items-center space-x-3 mb-4">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center border border-blue-200 bg-white">
            <AgentIcons agentName={selectedAgent.name} size="w-5 h-5" />
          </div>
          <div class="flex-1">
            <div class="text-lg font-semibold text-gray-900">{selectedAgent.name}</div>
            <div class="text-sm text-blue-600">{selectedAgent.role}</div>
            <div class="text-xs text-gray-500 mt-1">{capitalizeSpecialty(selectedAgent.specialty)}</div>
          </div>
        </div>
        
        <div class="text-gray-700">
          <p class="mb-4">{selectedAgent.description}</p>
          <p class="text-sm text-gray-600"><strong>Personality:</strong> {selectedAgent.personality}</p>
          
          {#if isLoadingAgents}
            <div class="mt-4 text-center py-8">
              <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              <p class="mt-2 text-sm text-gray-600">Loading agents...</p>
            </div>
          {/if}
          
          {#if loadingError}
            <div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-sm text-red-700">
                <strong>Loading Error:</strong> {loadingError}
              </p>
              <p class="text-xs text-red-600 mt-1">Using fallback agents for now.</p>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Hire New Agent Modal -->
  {#if showHireForm}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full">
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900">Hire New Agent</h2>
            <button
              on:click={() => showHireForm = false}
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Modal Body -->
        <div class="px-6 py-6">
          <div class="text-center">
            <p class="text-gray-600">This feature will be available soon!</p>
            <p class="text-sm text-gray-500 mt-2">You'll be able to create custom AI agents here.</p>
          </div>
        </div>
      </div>
    </div>
  {/if}

</div>