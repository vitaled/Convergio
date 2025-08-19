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
    personality: ''
  };
  let isCreatingAgent = false;
  let creationError: string | null = null;
  let creationSuccess = false;
  
  // AI Generated agent preview
  let generatedAgent: any = null;
  let isGeneratingAgent = false;
  let showPreview = false;

  // Reset form
  function resetAgentForm() {
    newAgentForm = {
      name: '',
      role: '',
      description: '',
      specialty: '',
      personality: ''
    };
    creationError = null;
    creationSuccess = false;
    showPreview = false;
    generatedAgent = null;
    isGeneratingAgent = false;
    isCreatingAgent = false;
  }

  // Cancel agent creation
  function cancelAgentCreation() {
    resetAgentForm();
    showHireForm = false;
  }

  // Generate agent using AI
  async function generateAgent() {
    isGeneratingAgent = true;
    creationError = null;
    generatedAgent = null;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      
      const response = await fetch(`${apiUrl}/api/v1/agents/generate-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          basic_info: {
            name: newAgentForm.name,
            role: newAgentForm.role,
            description: newAgentForm.description,
            specialty: newAgentForm.specialty,
            personality: newAgentForm.personality
          },
          existing_agents: allAgents.slice(0, 10) // Send sample of existing agents for context
        })
      });

      if (response.ok) {
        const result = await response.json();
        generatedAgent = result.agent;
        showPreview = true;
        console.log('Agent generated:', generatedAgent);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to generate agent: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to generate agent:', error);
      creationError = error instanceof Error ? error.message : 'Failed to generate agent with AI';
    } finally {
      isGeneratingAgent = false;
    }
  }

  // Create the final agent after review
  async function createFinalAgent() {
    isCreatingAgent = true;
    creationError = null;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      
      const response = await fetch(`${apiUrl}/api/v1/agents/create-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent_data: generatedAgent
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Agent created successfully:', result);
        
        creationSuccess = true;
        
        // Reload agents to include the new one
        setTimeout(async () => {
          await loadAgentsFromAPI();
          resetAgentForm();
          showHireForm = false;
          showPreview = false;
          generatedAgent = null;
        }, 1500);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to create agent: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to create final agent:', error);
      creationError = error instanceof Error ? error.message : 'Failed to create agent';
    } finally {
      isCreatingAgent = false;
    }
  }

  // Back to editing
  function backToEdit() {
    showPreview = false;
    generatedAgent = null;
  }
  
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

  // Helper functions to get simple agent data
  function getSimpleRole(key: string): string {
    const roleMap: Record<string, string> = {
      'ali_chief_of_staff': 'Chief of Staff',
      'amy_cfo': 'CFO',
      'baccio_tech_architect': 'Tech Architect',
      'sofia_marketing_strategist': 'Marketing Strategist',
      'luca_security_expert': 'Security Expert',
      'giulia_hr_talent_acquisition': 'HR Director',
      'marco_devops_engineer': 'Operations Director',
      'elena_legal_compliance_expert': 'Legal Advisor',
      'davide_project_manager': 'Project Manager',
      'omri_data_scientist': 'Data Scientist',
      'dan_engineering_gm': 'DevOps Engineer',
      'andrea_customer_success_manager': 'Sales Director',
      'sara_ux_ui_designer': 'UX Designer',
      'riccardo_storyteller': 'Content Creator',
      'matteo_strategic_business_architect': 'Financial Analyst',
      'satya_board_of_directors': 'CEO Advisor',
      'antonio_strategy_expert': 'Innovation Manager',
      'diana_performance_dashboard': 'Quality Assurance'
    };
    return roleMap[key] || 'AI Agent';
  }

  function getSimpleDescription(key: string): string {
    const descMap: Record<string, string> = {
      'ali_chief_of_staff': 'Strategic coordinator and master orchestrator',
      'amy_cfo': 'Financial analysis and strategic planning',
      'baccio_tech_architect': 'System architecture and technical strategy',
      'sofia_marketing_strategist': 'Marketing campaigns and growth strategies',
      'luca_security_expert': 'Cybersecurity and risk management',
      'giulia_hr_talent_acquisition': 'Human resources and talent management',
      'marco_devops_engineer': 'Operational excellence and process optimization',
      'elena_legal_compliance_expert': 'Legal compliance and risk management',
      'davide_project_manager': 'Project coordination and delivery management',
      'omri_data_scientist': 'Data analysis and machine learning insights',
      'dan_engineering_gm': 'Infrastructure and deployment automation',
      'andrea_customer_success_manager': 'Revenue generation and customer acquisition',
      'sara_ux_ui_designer': 'User experience and interface design',
      'riccardo_storyteller': 'Content strategy and brand storytelling',
      'matteo_strategic_business_architect': 'Advanced financial modeling and forecasting',
      'satya_board_of_directors': 'Executive strategy and business transformation',
      'antonio_strategy_expert': 'Innovation strategies and emerging technologies',
      'diana_performance_dashboard': 'Quality management and process improvement'
    };
    return descMap[key] || 'AI-powered specialist';
  }

  function getSimpleSpecialty(key: string): string {
    const specMap: Record<string, string> = {
      'ali_chief_of_staff': 'Executive assistance, team coordination, strategic planning',
      'amy_cfo': 'Financial modeling, budgeting, investment analysis',
      'baccio_tech_architect': 'Cloud architecture, scalability, technical decision-making',
      'sofia_marketing_strategist': 'Brand positioning, digital marketing, customer acquisition',
      'luca_security_expert': 'Security audits, risk assessment, compliance',
      'giulia_hr_talent_acquisition': 'Recruitment, team development, organizational culture',
      'marco_devops_engineer': 'Operations management, process improvement, supply chain',
      'elena_legal_compliance_expert': 'Corporate law, contracts, compliance, intellectual property',
      'davide_project_manager': 'Agile methodologies, team coordination, timeline management',
      'omri_data_scientist': 'Predictive analytics, data mining, ML algorithms, statistical analysis',
      'dan_engineering_gm': 'CI/CD, cloud infrastructure, monitoring, containerization',
      'andrea_customer_success_manager': 'B2B sales, customer relationship management, pipeline optimization',
      'sara_ux_ui_designer': 'User research, wireframing, prototyping, accessibility',
      'riccardo_storyteller': 'Content marketing, copywriting, brand voice, SEO',
      'matteo_strategic_business_architect': 'Financial planning, investment analysis, budget forecasting',
      'satya_board_of_directors': 'Strategic planning, digital transformation, C-suite advisory',
      'antonio_strategy_expert': 'Innovation management, emerging tech, R&D strategy',
      'diana_performance_dashboard': 'QA processes, compliance, continuous improvement'
    };
    return specMap[key] || 'General AI assistance, problem solving';
  }

  function getSimplePersonality(key: string): string {
    const persMap: Record<string, string> = {
      'ali_chief_of_staff': 'Diplomatic, strategic, always sees the bigger picture',
      'amy_cfo': 'Analytical, detail-oriented, fiscally responsible',
      'baccio_tech_architect': 'Innovative, pragmatic, loves elegant solutions',
      'sofia_marketing_strategist': 'Creative, data-driven, customer-focused',
      'luca_security_expert': 'Vigilant, thorough, security-first mindset',
      'giulia_hr_talent_acquisition': 'Empathetic, people-focused, culture builder',
      'marco_devops_engineer': 'Efficient, systematic, results-driven',
      'elena_legal_compliance_expert': 'Meticulous, analytical, risk-aware',
      'davide_project_manager': 'Organized, collaborative, deadline-focused',
      'omri_data_scientist': 'Curious, methodical, insight-driven',
      'dan_engineering_gm': 'Reliable, automation-focused, performance-oriented',
      'andrea_customer_success_manager': 'Persuasive, relationship-focused, target-driven',
      'sara_ux_ui_designer': 'Empathetic, creative, user-centered',
      'riccardo_storyteller': 'Creative, strategic, brand-conscious',
      'matteo_strategic_business_architect': 'Analytical, detail-oriented, numbers-focused',
      'satya_board_of_directors': 'Visionary, decisive, transformation-focused',
      'antonio_strategy_expert': 'Forward-thinking, creative, technology-savvy',
      'diana_performance_dashboard': 'Meticulous, quality-focused, systematic'
    };
    return persMap[key] || 'Intelligent, helpful, specialized';
  }

  // Load agents from API
  async function loadAgentsFromAPI() {
    isLoadingAgents = true;
    loadingError = null;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agent-management/agents`);
      if (response.ok) {
        const data = await response.json();
        
        // The backend now returns an array directly, not wrapped in {agents: [...]}
        const agentsArray = Array.isArray(data) ? data : (data.agents || []);
        
        // Transform backend agent data to frontend format with proper names and descriptions
        const transformedAgents = agentsArray.map((backendAgent: any, index: number) => {
          // Convert backend name to proper display name (ethan-ic6da -> Ethan)
          const displayName = backendAgent.name.split('-')[0].charAt(0).toUpperCase() + 
                              backendAgent.name.split('-')[0].slice(1);
          
          // Use backend data or fallback to helper functions
          const role = backendAgent.tier || getSimpleRole(backendAgent.id);
          const description = backendAgent.role || getSimpleDescription(backendAgent.id);
          const specialty = backendAgent.category || getSimpleSpecialty(backendAgent.id);
          const personality = getSimplePersonality(backendAgent.id);
          
          return {
            id: index + 1,
            name: displayName,
            key: backendAgent.id, // backend uses 'id' not 'key'
            role: role,
            description: description,
            specialty: specialty,
            personality: personality,
            is_featured: index < 6 // First 6 are featured
          };
        });
        
        // Sort agents so Ali is first
        transformedAgents.sort((a, b) => {
          // Ali Chief of Staff should be first
          if (a.key && a.key.includes('ali-chief-of-staff')) return -1;
          if (b.key && b.key.includes('ali-chief-of-staff')) return 1;
          
          // Then by alphabetical order of display name
          return a.name.localeCompare(b.name);
        });
        
        allAgents = transformedAgents;
        console.log(`✅ Loaded ${allAgents.length} agents from API (Ali first)`);
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

  // Extract unique skills for filter (reactive)
  $: allSkills = [...new Set(allAgents.map(agent => agent.specialty.split(', ')).flat())]
    .map(skill => skill.charAt(0).toUpperCase() + skill.slice(1));

  // Featured agents (reactive)
  $: featuredAgents = allAgents.filter(agent => agent.is_featured);

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

  let currentMessage = '';
  let messages: Message[] = [];
  let selectedAgent = fallbackAgents[0];
  let isLoading = false;
  let messagesContainer: HTMLElement;
  
  // View Mode variables
  let isOversightMode = false;
  let oversightIterations: any[] = [];
  let websocket: WebSocket | null = null;

  // Auto-scroll function
  function scrollToBottom() {
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTo({
          top: messagesContainer.scrollHeight,
          behavior: 'smooth'
        });
      }, 100);
    }
  }

  // Watch messages changes to auto-scroll
  $: if (messages.length > 0) {
    scrollToBottom();
  }

  function selectAgent(agent: Agent) {
    selectedAgent = agent;
    showConversationManager = true;
    
    // Switch conversation context
    if (agent.key) {
      conversationManager.switchToAgent(agent.key);
      currentAgentId.set(agent.key);
    }
    
    // Load existing conversation or create welcome message
    const conversation = conversationManager.getConversation?.(agent.key || agent.name.toLowerCase());
    if (conversation && conversation.messages.length > 0) {
      // Convert conversation messages to local format
      messages = conversation.messages.map(msg => ({
        id: msg.id,
        type: msg.type === 'user' ? 'user' : 'ai',
        content: msg.content,
        timestamp: msg.timestamp,
        agents_used: []
      }));
    } else {
      // Start with empty conversation - agent will introduce itself intelligently if needed
      messages = [];
    }
  }

  async function sendMessage() {
    if (!currentMessage.trim()) return;
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentMessage.trim(),
      timestamp: new Date()
    };
    messages = [...messages, userMessage];
    
    // Save user message to conversation store
    if (selectedAgent?.key) {
      conversationManager.addMessage(selectedAgent.key, {
        agentId: selectedAgent.key,
        agentName: selectedAgent.name,
        content: userMessage.content,
        timestamp: userMessage.timestamp,
        type: 'user',
        status: 'sent'
      });
    }
    
    const messageToSend = currentMessage.trim();
    currentMessage = '';
    isLoading = true;
    
    // Check if we're in Oversight Mode with Ali
    if (isOversightMode && selectedAgent?.name === 'Ali') {
      await sendOversightModeMessage(messageToSend);
    } else {
      await sendExecutiveModeMessage(messageToSend);
    }
  }

  async function sendExecutiveModeMessage(messageToSend: string) {
    try {
      const response = await fetch('http://localhost:9000/api/v1/agents/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: `[${selectedAgent?.role || 'Agent'} ${selectedAgent?.name || 'Unknown'}] ${messageToSend}`,
          user_id: 'user-agent-interaction',
          context: {
            agent_id: selectedAgent?.id || 0,
            agent_name: selectedAgent?.key || selectedAgent?.name || 'unknown',  // Use backend key
            agent_role: selectedAgent?.role || 'Agent',
            agent_specialty: selectedAgent?.specialty || 'General assistance'
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: result.response,
          timestamp: new Date(),
          agents_used: result.agents_used
        }];
      } else {
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: `I'm experiencing some technical difficulties. Let me get back to you with a comprehensive response shortly.`,
          timestamp: new Date()
        }];
      }
    } catch (error) {
      console.error('Agent conversation error:', error);
      messages = [...messages, {
        id: Date.now() + 1,
        type: 'ai', 
        content: `I'm having trouble connecting right now. Please try again, and I'll coordinate with the team to provide you with the insights you need.`,
        timestamp: new Date()
      }];
    } finally {
      isLoading = false;
      
      // Save conversation to store
      if (selectedAgent?.key && messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.type === 'ai') {
          conversationManager.addMessage(selectedAgent.key, {
            agentId: selectedAgent.key,
            agentName: selectedAgent.name,
            content: lastMessage.content,
            timestamp: lastMessage.timestamp,
            type: 'agent',
            status: 'sent'
          });
        }
      }
    }
  }

  async function sendOversightModeMessage(messageToSend: string) {
    try {
      // Clear previous oversight iterations
      oversightIterations = [];
      
      // Start WebSocket connection for real-time agent updates
      const conversationId = `oversight-${Date.now()}`;
      const wsUrl = `ws://localhost:9000/api/v1/agents/ws/conversation/${conversationId}`;
      
      websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected for oversight mode');
        // Send conversation start message
        websocket?.send(JSON.stringify({
          type: 'start_conversation',
          message: messageToSend,
          user_id: 'debug-user',
          context: {
            agent_id: selectedAgent?.id || 0,
            agent_name: selectedAgent?.name || 'Unknown',
            agent_role: selectedAgent?.role || 'Agent'
          }
        }));
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        switch (data.type) {
          case 'connection_established':
            console.log('Oversight mode connection established');
            break;
            
          case 'conversation_started':
            console.log('Oversight conversation started');
            break;
            
          case 'agent_status':
          case 'agent_response':
            // Add or update agent iteration
            oversightIterations = [...oversightIterations, data];
            break;
            
          case 'conversation_completed':
            isLoading = false;
            // Add final Ali response to regular messages
            messages = [...messages, {
              id: Date.now() + 1,
              type: 'ai',
              content: data.final_response,
              timestamp: new Date(),
              agents_used: data.agents_used || []
            }];
            websocket?.close();
            break;
            
          case 'error':
            console.error('WebSocket error:', data.message);
            isLoading = false;
            messages = [...messages, {
              id: Date.now() + 1,
              type: 'ai',
              content: `Oversight mode error: ${data.message}`,
              timestamp: new Date()
            }];
            break;
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        isLoading = false;
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: `Oversight mode connection failed. Falling back to executive mode.`,
          timestamp: new Date()
        }];
      };
      
    } catch (error) {
      console.error('Oversight mode error:', error);
      isLoading = false;
      // Fallback to executive mode
      await sendExecutiveModeMessage(messageToSend);
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  onMount(() => {
    // Load agents and initialize
    (async () => {
      await loadAgentsFromAPI();
      
      // Initialize conversations for all agents
      allAgents.forEach(agent => {
        if (agent.key) {
          conversationManager.initializeConversation(agent.key, agent.name);
        }
      });
      
      // Initialize with first featured agent when available (after reactive updates)
      setTimeout(() => {
        if (featuredAgents.length > 0) {
          selectedAgent = featuredAgents[0];
          selectAgent(featuredAgents[0]);
        } else if (allAgents.length > 0) {
          selectedAgent = allAgents[0];
          selectAgent(allAgents[0]);
        }
      }, 100);
    })();
  });
</script>

<svelte:head>
  <title>AI Team - platform.Convergio.io</title>
</svelte:head>

<!-- AI Agents Page -->
<div class="min-h-screen bg-gray-50 space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-lg font-medium text-gray-900">AI Team</h1>
      <p class="mt-1 text-sm text-gray-700">Your specialized AI agents powered by Microsoft AutoGen</p>
    </div>
  </div>

  <div class="grid lg:grid-cols-5 gap-8">
    <!-- Agents List with integrated search -->
    <div class="lg:col-span-2">
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <!-- Search in header -->
        <div class="p-4 border-b border-gray-200 bg-gray-50">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-md font-medium text-gray-900">AI Team</h3>
            <!-- Hire New Agent Button -->
            <button
              on:click={() => showHireForm = true}
              on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? (e.preventDefault(), showHireForm = true) : null}
              class="btn-primary btn-sm flex items-center space-x-1"
              aria-label="Hire new AI agent"
              tabindex="0"
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
              class="input-field"
              aria-label="Search agents by name, role, or skills"
              role="searchbox"
            />
            <select
              bind:value={selectedSkill}
              class="input-field"
              aria-label="Filter agents by specialty"
              role="combobox"
            >
              <option value="">All Specialties</option>
              {#each allSkills.slice(0, 12) as skill}
                <option value={skill}>{skill}</option>
              {/each}
            </select>
          </div>
          
          <div class="flex items-center justify-between text-xs mt-3 pt-3 border-t border-gray-300">
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
          <div class="divide-y divide-gray-200">
            {#each filteredAgents as agent}
              <button
                on:click={() => selectAgent(agent)}
                on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), selectAgent(agent)) : null}
                class="w-full p-3 hover:bg-blue-50 transition-colors text-left group {selectedAgent.id === agent.id ? 'bg-blue-100 border-r-4 border-blue-500' : ''}"
                aria-label="Select {agent.name} - {agent.role}"
                aria-pressed="{selectedAgent.id === agent.id}"
                  tabindex="0"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center border-2 border-gray-300 bg-gray-100 group-hover:border-blue-400 transition-colors">
                    <AgentIcons agentName={agent.name} size="w-4 h-4" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="body-md font-semibold text-gray-900">{agent.name}</div>
                    <div class="body-sm text-blue-600">{agent.role}</div>
                    <div class="caption text-gray-600 truncate mt-0.5">{agent.description}</div>
                  </div>
                  {#if agent.key}
                    <AgentStatus agentId={agent.key} agentName={agent.name} compact={true} />
                  {:else}
                    <div class="flex items-center space-x-1 px-2 py-1 bg-green-100 rounded-full">
                      <div class="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      <span class="caption text-green-700 font-medium">Ready</span>
                    </div>
                  {/if}
                </div>
              </button>
            {/each}
            
            {#if filteredAgents.length === 0}
              <div class="text-center py-8 text-gray-600">
                <div class="body-md mb-2">No agents found</div>
                <button 
                  on:click={() => { searchQuery = ''; selectedSkill = ''; }}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), searchQuery = '', selectedSkill = '') : null}
                  class="text-blue-600 hover:text-blue-700 underline body-sm font-medium"
                  aria-label="Clear search filters"
                      tabindex="0"
                >
                  Clear filters
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Enlarged Chat Interface -->
    <div class="lg:col-span-3">
      <div class="bg-white border border-gray-200 rounded-lg h-[600px] flex flex-col">
        <!-- Chat Header -->
        <div class="px-6 py-4 border-b border-gray-200 bg-blue-50">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center border-2 border-blue-300 bg-white">
                <AgentIcons agentName={selectedAgent?.name || ''} size="w-5 h-5" />
              </div>
              <div class="flex-1">
                <div class="text-md font-medium text-gray-900">{selectedAgent?.name || 'Loading...'}</div>
                <div class="text-sm text-blue-600">{selectedAgent?.role || ''}</div>
                <div class="text-xs text-gray-600 mt-1">{selectedAgent?.description || ''}</div>
              </div>
            </div>
            
            <!-- Executive/Oversight Mode Toggle (only for Ali) -->
            {#if selectedAgent?.name === 'Ali'}
              <div class="flex items-center space-x-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
                <span class="text-xs font-medium text-gray-600">View:</span>
                <button
                  on:click={() => isOversightMode = false}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), isOversightMode = false) : null}
                  class="px-3 py-1 text-xs font-medium rounded transition-colors {!isOversightMode ? 'bg-blue-500 text-white shadow-sm' : 'text-gray-600 hover:text-blue-600'}"
                  aria-label="Switch to Executive view mode"
                  aria-pressed="{!isOversightMode}"
                      tabindex="0"
                >
                  Executive
                </button>
                <button
                  on:click={() => isOversightMode = true}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), isOversightMode = true) : null}
                  class="px-3 py-1 text-xs font-medium rounded transition-colors {isOversightMode ? 'bg-purple-500 text-white shadow-sm' : 'text-gray-600 hover:text-purple-600'}"
                  aria-label="Switch to Oversight view mode"
                  aria-pressed="{isOversightMode}"
                      tabindex="0"
                >
                  Oversight
                </button>
              </div>
            {/if}
          </div>
        </div>

        <!-- Messages / Oversight Timeline -->
        <div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-6 space-y-4">
          
          {#if !isOversightMode || selectedAgent?.name !== 'Ali'}
            <!-- Executive Mode: Regular Messages -->
            {#each messages as message}
              <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-lg">
                  {#if message.type === 'user'}
                    <div class="bg-blue-500 text-white p-4 rounded-xl rounded-br-sm">
                      <div class="font-medium mb-1 opacity-75 text-sm">You</div>
                      <div class="text-sm leading-relaxed">
                        <MarkdownRenderer content={message.content} />
                      </div>
                    </div>
                  {:else}
                    <div class="bg-gray-50 p-4 rounded-xl rounded-bl-sm border">
                      <div class="flex items-center space-x-2 mb-2">
                        <AgentIcons agentName={selectedAgent?.name || ''} size="w-4 h-4" />
                        <span class="font-medium text-gray-900 text-sm">{selectedAgent?.name || ''}</span>
                        <span class="text-xs text-blue-600">• {selectedAgent?.role || ''}</span>
                      </div>
                      <div class="text-gray-800 text-sm leading-relaxed">
                        <MarkdownRenderer content={message.content} />
                      </div>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
            
            {#if isLoading}
              <div class="flex justify-start">
                <div class="bg-gray-50 p-4 rounded-xl border max-w-lg">
                  <div class="flex items-center space-x-2 mb-2">
                    <AgentIcons agentName={selectedAgent?.name || ''} size="w-4 h-4" />
                    <span class="text-sm text-gray-600">{selectedAgent?.name || 'Agent'} is thinking...</span>
                  </div>
                  <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                </div>
              </div>
            {/if}
          {:else}
            <!-- Oversight Mode: Timeline with Agent Iterations -->
            <div class="oversight-timeline">
              <h3 class="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                <div class="w-2 h-2 bg-purple-600 rounded-full mr-2 animate-pulse"></div>
                Oversight Mode: Team Coordination Timeline
              </h3>
              
              <!-- User Message -->
              {#each messages.filter(m => m.type === 'user') as userMessage}
                <div class="timeline-item mb-6">
                  <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-bold">You</span>
                    </div>
                    <div class="flex-1 bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                      <div class="font-medium text-blue-900 text-sm mb-1">Your Request</div>
                      <div class="text-blue-800 text-sm">
                        <MarkdownRenderer content={userMessage.content} />
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
              
              <!-- Agent Iterations -->
              {#each oversightIterations as iteration, i}
                <div class="timeline-item mb-4 relative">
                  <!-- Timeline connector -->
                  {#if i < oversightIterations.length - 1}
                    <div class="absolute left-4 top-12 w-0.5 h-8 bg-gray-200"></div>
                  {/if}
                  
                  <div class="flex items-start space-x-3">
                    <!-- Agent Avatar with Status -->
                    <div class="relative">
                      <div class="w-8 h-8 rounded-full flex items-center justify-center border-2" style="background-color: {iteration.color}20; border-color: {iteration.color}">
                        <AgentIcons agentName={iteration.agent_name} size="w-4 h-4" />
                      </div>
                      
                      <!-- Status Indicator -->
                      {#if iteration.status === 'thinking'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                      {:else if iteration.status === 'completed'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full">
                          <svg class="w-2 h-2 text-white absolute top-0.5 left-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                          </svg>
                        </div>
                      {:else if iteration.status === 'active'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
                      {/if}
                    </div>
                    
                    <!-- Agent Content -->
                    <div class="flex-1 border-l-4 p-3 rounded-r-lg" style="background-color: {iteration.color}05; border-left-color: {iteration.color}">
                      <div class="flex items-center space-x-2 mb-2">
                        <span class="font-medium text-sm" style="color: {iteration.color}">{iteration.agent_name}</span>
                        <span class="text-xs text-gray-500">{iteration.agent_role}</span>
                        <div class="text-xs px-2 py-1 rounded-full" style="background-color: {iteration.color}20; color: {iteration.color}">
                          Turn {iteration.turn}
                        </div>
                      </div>
                      
                      {#if iteration.status === 'thinking'}
                        <div class="text-sm text-gray-600 italic">{iteration.message || `${iteration.agent_name} is analyzing your request...`}</div>
                      {:else}
                        <div class="text-sm text-gray-800">{iteration.content}</div>
                      {/if}
                      
                      <div class="text-xs text-gray-400 mt-2">
                        {new Date(iteration.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
              
              <!-- Loading state in oversight mode -->
              {#if isLoading}
                <div class="timeline-item mb-4">
                  <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center animate-pulse">
                      <AgentIcons agentName="Ali" size="w-4 h-4" />
                    </div>
                    <div class="flex-1 bg-gray-50 border-l-4 border-gray-200 p-3 rounded-r-lg">
                      <div class="text-sm text-gray-600">Ali is coordinating the team response...</div>
                      <div class="flex space-x-1 mt-2">
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Enhanced Input -->
        <div class="p-6 border-t border-gray-200 bg-gray-50">
          <div class="flex space-x-3">
            <textarea
              bind:value={currentMessage}
              on:keydown={handleKeyPress}
              placeholder="Ask {selectedAgent?.name || 'the agent'} about strategy, analysis, or anything in their expertise area..."
              class="flex-1 input-field resize-none"
              rows="2"
              disabled={isLoading}
              aria-label="Type your message to {selectedAgent?.name || 'the agent'}"
            ></textarea>
            <button
              on:click={sendMessage}
              on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !(!currentMessage.trim() || isLoading) ? (e.preventDefault(), sendMessage()) : null}
              disabled={!currentMessage.trim() || isLoading}
              class="btn-primary px-6 py-3"
              aria-label="Send message to {selectedAgent?.name || 'agent'}"
            >
              Send
            </button>
          </div>
          <div class="text-xs text-gray-600 mt-2">
            Press Shift+Enter for new line, Enter to send
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Hire New Agent Modal -->
  {#if showHireForm}
    <div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-content max-w-md">
        <!-- Modal Header -->
        <div class="modal-header">
          <div class="flex items-center justify-between">
            <h2 id="modal-title" class="text-lg font-medium text-gray-900">Hire New Agent</h2>
            <button
              on:click={() => showHireForm = false}
              on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), showHireForm = false) : null}
              class="text-gray-600 hover:text-gray-900 transition-colors"
              aria-label="Close modal"
              tabindex="0"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          {#if !showPreview}
            <!-- Initial Form -->
            <form on:submit|preventDefault={generateAgent} class="space-y-4">
              <!-- Agent Name -->
              <div>
                <label for="agent-name" class="form-label">
                  Agent Name *
                </label>
                <input
                  id="agent-name"
                  type="text"
                  bind:value={newAgentForm.name}
                  placeholder="e.g., Mario, Elena, Giorgio..."
                  class="input-field"
                  required
                />
              </div>

              <!-- Role -->
              <div>
                <label for="agent-role" class="form-label">
                  Role *
                </label>
                <input
                  id="agent-role"
                  type="text"
                  bind:value={newAgentForm.role}
                  placeholder="e.g., Marketing Manager, Data Analyst..."
                  class="input-field"
                  required
                />
              </div>

              <!-- Description -->
              <div>
                <label for="agent-description" class="form-label">
                  Description *
                </label>
                <textarea
                  id="agent-description"
                  bind:value={newAgentForm.description}
                  placeholder="Brief description of what this agent does..."
                  rows="2"
                  class="input-field resize-none"
                  required
                ></textarea>
              </div>

              <!-- Specialty -->
              <div>
                <label for="agent-specialty" class="form-label">
                  Specialty *
                </label>
                <input
                  id="agent-specialty"
                  type="text"
                  bind:value={newAgentForm.specialty}
                  placeholder="e.g., Social media, financial planning..."
                  class="input-field"
                  required
                />
              </div>

              <!-- Personality -->
              <div>
                <label for="agent-personality" class="form-label">
                  Personality
                </label>
                <input
                  id="agent-personality"
                  type="text"
                  bind:value={newAgentForm.personality}
                  placeholder="e.g., Creative, analytical, detail-oriented..."
                  class="input-field"
                />
              </div>

              <!-- Error Messages -->
              {#if creationError}
                <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p class="text-sm text-red-700">{creationError}</p>
                </div>
              {/if}

              <!-- Buttons -->
              <div class="flex space-x-3 pt-4">
                <button
                  type="button"
                  on:click={cancelAgentCreation}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isGeneratingAgent ? (e.preventDefault(), cancelAgentCreation()) : null}
                  class="btn-secondary flex-1"
                  disabled={isGeneratingAgent}
                  aria-label="Cancel agent creation"
                    >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="btn-primary flex-1"
                  disabled={isGeneratingAgent}
                  aria-label="Generate agent with AI"
                    >
                  {#if isGeneratingAgent}
                    <div class="flex items-center justify-center space-x-2">
                      <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>AI Creating...</span>
                    </div>
                  {:else}
                    ✨ Generate with AI
                  {/if}
                </button>
              </div>
              
              <div class="caption text-center pt-2">
                AI will create a complete job description aligned with your team
              </div>
            </form>
            
          {:else}
            <!-- AI Generated Preview -->
            <div class="space-y-6">
              <div class="text-center">
                <div class="inline-flex items-center space-x-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium mb-4">
                  <span>🤖</span>
                  <span>AI Generated Agent</span>
                </div>
              </div>
              
              {#if generatedAgent}
                <!-- Agent Preview Card -->
                <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div class="flex items-center space-x-3 mb-3">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-lg" 
                         style="background-color: {generatedAgent.color || '#6366f1'}">
                      {generatedAgent.name?.charAt(0) || 'A'}
                    </div>
                    <div>
                      <h3 class="font-semibold text-gray-900">{generatedAgent.name}</h3>
                      <p class="text-sm text-blue-600">{generatedAgent.role}</p>
                    </div>
                  </div>
                  
                  <div class="space-y-3 text-sm">
                    <div>
                      <span class="font-medium text-gray-700">Description:</span>
                      <p class="text-gray-600 mt-1">{generatedAgent.description}</p>
                    </div>
                    
                    <div>
                      <span class="font-medium text-gray-700">Specialty:</span>
                      <p class="text-gray-600 mt-1">{generatedAgent.specialty}</p>
                    </div>
                    
                    <div>
                      <span class="font-medium text-gray-700">Personality:</span>
                      <p class="text-gray-600 mt-1">{generatedAgent.personality}</p>
                    </div>
                    
                    {#if generatedAgent.tools && generatedAgent.tools.length > 0}
                      <div>
                        <span class="font-medium text-gray-700">Tools:</span>
                        <div class="flex flex-wrap gap-1 mt-1">
                          {#each generatedAgent.tools.slice(0, 3) as tool}
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">{tool}</span>
                          {/each}
                          {#if generatedAgent.tools.length > 3}
                            <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">+{generatedAgent.tools.length - 3} more</span>
                          {/if}
                        </div>
                      </div>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- Success Messages -->
              {#if creationSuccess}
                <div class="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p class="text-sm text-green-700">Agent created successfully!</p>
                </div>
              {/if}

              <!-- Error Messages -->
              {#if creationError}
                <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p class="text-sm text-red-700">{creationError}</p>
                </div>
              {/if}

              <!-- Action Buttons -->
              <div class="flex space-x-3">
                <button
                  type="button"
                  on:click={backToEdit}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isCreatingAgent ? (e.preventDefault(), backToEdit()) : null}
                  class="btn-secondary flex-1"
                  disabled={isCreatingAgent}
                  aria-label="Go back to edit agent details"
                    >
                  ← Edit Details
                </button>
                <button
                  type="button"
                  on:click={createFinalAgent}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isCreatingAgent ? (e.preventDefault(), createFinalAgent()) : null}
                  class="btn-primary flex-1 bg-green-500 hover:bg-green-600 disabled:bg-green-300"
                  disabled={isCreatingAgent}
                  aria-label="Hire this agent"
                    >
                  {#if isCreatingAgent}
                    <div class="flex items-center justify-center space-x-2">
                      <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Creating...</span>
                    </div>
                  {:else}
                    ✅ Hire This Agent
                  {/if}
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}

</div>