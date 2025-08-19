<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { flip } from 'svelte/animate';
  import { dndzone } from 'svelte-dnd-action';
  
  export let projectId: string;
  export let columns: any[] = [];
  export let tasks: any[] = [];
  
  const dispatch = createEventDispatcher();
  
  let loading = true;
  let dragDisabled = false;
  let selectedTask: any = null;
  let showTaskModal = false;
  let aiAssistantOpen = false;
  let realTimeUpdates = true;
  
  // Modern glassmorphism colors
  const colors = {
    background: 'rgba(15, 23, 42, 1)',
    glass: 'rgba(255, 255, 255, 0.1)',
    glassBorder: 'rgba(255, 255, 255, 0.2)',
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    text: '#f8fafc',
    textSecondary: '#cbd5e1'
  };
  
  // Default columns with modern styling
  const defaultColumns = [
    {
      id: 'backlog',
      title: 'Backlog',
      color: '#64748b',
      icon: '📋',
      tasks: [],
      limit: null,
      description: 'Ideas and future tasks'
    },
    {
      id: 'planning',
      title: 'Planning',
      color: '#8b5cf6',
      icon: '🎯',
      tasks: [],
      limit: 5,
      description: 'Tasks being planned by AI agents'
    },
    {
      id: 'in_progress',
      title: 'In Progress',
      color: '#3b82f6',
      icon: '🚀',
      tasks: [],
      limit: 3,
      description: 'Active development'
    },
    {
      id: 'review',
      title: 'Review',
      color: '#f59e0b',
      icon: '👁️',
      tasks: [],
      limit: 4,
      description: 'Quality assurance'
    },
    {
      id: 'done',
      title: 'Done',
      color: '#10b981',
      icon: '✅',
      tasks: [],
      limit: null,
      description: 'Completed tasks'
    }
  ];
  
  // Mock tasks with AI integration
  const mockTasks = [
    {
      id: 'task1',
      title: 'Market Research Analysis',
      description: 'Comprehensive market analysis with competitive intelligence',
      priority: 'high',
      assignedAgent: 'Marcus PM',
      aiInsights: 'Market trends analysis completed, ready for strategic planning',
      tags: ['research', 'strategy'],
      estimatedHours: 24,
      actualHours: 18,
      dueDate: '2025-02-15',
      attachments: 3,
      comments: 7,
      status: 'planning',
      progress: 0.75
    },
    {
      id: 'task2',
      title: 'UX Design System',
      description: 'Create comprehensive design system and component library',
      priority: 'critical',
      assignedAgent: 'Sara UX Designer',
      aiInsights: 'Design patterns optimized for accessibility and modern UI trends',
      tags: ['design', 'frontend'],
      estimatedHours: 40,
      actualHours: 12,
      dueDate: '2025-03-01',
      attachments: 8,
      comments: 12,
      status: 'in_progress',
      progress: 0.30
    },
    {
      id: 'task3',
      title: 'API Architecture Design',
      description: 'Design scalable microservices architecture',
      priority: 'high',
      assignedAgent: 'Baccio Tech Architect',
      aiInsights: 'Microservices pattern recommended for optimal scalability',
      tags: ['backend', 'architecture'],
      estimatedHours: 32,
      actualHours: 8,
      dueDate: '2025-02-28',
      attachments: 5,
      comments: 3,
      status: 'in_progress',
      progress: 0.25
    },
    {
      id: 'task4',
      title: 'Performance Optimization',
      description: 'Optimize application performance and loading times',
      priority: 'medium',
      assignedAgent: 'Thor QA Guardian',
      aiInsights: 'Performance bottlenecks identified in data layer',
      tags: ['performance', 'optimization'],
      estimatedHours: 16,
      actualHours: 14,
      dueDate: '2025-02-20',
      attachments: 2,
      comments: 5,
      status: 'review',
      progress: 0.90
    },
    {
      id: 'task5',
      title: 'Security Audit',
      description: 'Complete security assessment and vulnerability testing',
      priority: 'critical',
      assignedAgent: 'Luca Security Expert',
      aiInsights: 'Zero critical vulnerabilities found, minor issues documented',
      tags: ['security', 'audit'],
      estimatedHours: 20,
      actualHours: 20,
      dueDate: '2025-01-30',
      attachments: 6,
      comments: 2,
      status: 'done',
      progress: 1.0
    }
  ];
  
  $: displayColumns = columns.length > 0 ? columns : defaultColumns;
  $: displayTasks = tasks.length > 0 ? tasks : mockTasks;
  
  // Distribute tasks to columns
  $: {
    displayColumns.forEach(column => {
      column.tasks = displayTasks.filter(task => task.status === column.id);
    });
  }
  
  onMount(async () => {
    await loadKanbanData();
    setupRealTimeUpdates();
    loading = false;
  });
  
  async function loadKanbanData() {
    try {
      const [columnsRes, tasksRes] = await Promise.all([
        fetch(`/api/v1/pm/projects/${projectId}/columns`),
        fetch(`/api/v1/pm/projects/${projectId}/tasks`)
      ]);
      
      if (columnsRes.ok) columns = await columnsRes.json();
      if (tasksRes.ok) tasks = await tasksRes.json();
    } catch (error) {
      console.error('Failed to load kanban data:', error);
    }
  }
  
  function setupRealTimeUpdates() {
    if (!realTimeUpdates) return;
    
    // Simulate real-time updates from AI agents
    setInterval(async () => {
      // Simulate AI agent updating task progress
      const randomTask = displayTasks[Math.floor(Math.random() * displayTasks.length)];
      if (randomTask && randomTask.status === 'in_progress' && Math.random() > 0.8) {
        randomTask.progress = Math.min(randomTask.progress + 0.05, 1.0);
        randomTask.aiInsights = `Progress updated by ${randomTask.assignedAgent} - ${Math.round(randomTask.progress * 100)}% complete`;
        displayTasks = [...displayTasks]; // Trigger reactivity
      }
    }, 10000);
  }
  
  function handleDndConsider(columnId: string, e: CustomEvent) {
    const { items } = e.detail;
    const column = displayColumns.find(col => col.id === columnId);
    if (column) {
      column.tasks = items;
      displayColumns = [...displayColumns];
    }
  }
  
  function handleDndFinalize(columnId: string, e: CustomEvent) {
    const { items } = e.detail;
    const column = displayColumns.find(col => col.id === columnId);
    if (column) {
      column.tasks = items;
      
      // Update task status
      items.forEach((task: any) => {
        if (task.status !== columnId) {
          task.status = columnId;
          updateTaskStatus(task.id, columnId);
        }
      });
      
      displayColumns = [...displayColumns];
    }
  }
  
  async function updateTaskStatus(taskId: string, newStatus: string) {
    try {
      await fetch(`/api/v1/pm/tasks/${taskId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return colors.danger;
      case 'high': return colors.warning;
      case 'medium': return colors.primary;
      case 'low': return colors.success;
      default: return colors.secondary;
    }
  }
  
  function openTaskModal(task: any) {
    selectedTask = task;
    showTaskModal = true;
  }
  
  function formatDueDate(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Overdue';
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    return `${diffDays} days left`;
  }
  
  async function askAliAssistance(task: any) {
    try {
      const response = await fetch('/api/v1/agents/ali/task-assistance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: task.id,
          project_id: projectId,
          assistance_type: 'optimization'
        })
      });
      
      if (response.ok) {
        const assistance = await response.json();
        task.aiInsights = assistance.recommendation;
        displayTasks = [...displayTasks];
      }
    } catch (error) {
      console.error('Failed to get Ali assistance:', error);
      task.aiInsights = `Ali is analyzing this task for optimization opportunities...`;
      displayTasks = [...displayTasks];
    }
  }
  
  function createNewTask() {
    const newTask = {
      id: `task_${Date.now()}`,
      title: 'New Task',
      description: 'Click to edit description',
      priority: 'medium',
      assignedAgent: 'Unassigned',
      aiInsights: 'Ready for AI agent assignment',
      tags: [],
      estimatedHours: 0,
      actualHours: 0,
      dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      attachments: 0,
      comments: 0,
      status: 'backlog',
      progress: 0
    };
    
    displayTasks = [...displayTasks, newTask];
    openTaskModal(newTask);
  }
</script>

<div class="modern-kanban-container">
  <!-- Header with AI Integration -->
  <div class="kanban-header">
    <div class="header-left">
      <h2 class="kanban-title">
        <span class="title-icon">🏗️</span>
        AI-Powered Kanban Board
      </h2>
      <p class="kanban-subtitle">Real-time collaboration with intelligent agents</p>
    </div>
    
    <div class="header-actions">
      <button 
        class="ai-assistant-btn"
        class:active={aiAssistantOpen}
        on:click={() => aiAssistantOpen = !aiAssistantOpen}
      >
        <span class="ai-icon">🤖</span>
        AI Assistant
      </button>
      
      <button class="new-task-btn" on:click={createNewTask}>
        <span class="plus-icon">+</span>
        New Task
      </button>
      
      <div class="real-time-indicator" class:active={realTimeUpdates}>
        <div class="pulse-dot"></div>
        Real-time
      </div>
    </div>
  </div>
  
  <!-- AI Assistant Panel -->
  {#if aiAssistantOpen}
    <div class="ai-assistant-panel">
      <div class="assistant-header">
        <h3>
          <span class="ai-icon">🧠</span>
          Ali - Chief of Staff
        </h3>
        <p>AI project insights and recommendations</p>
      </div>
      
      <div class="assistant-insights">
        <div class="insight-card">
          <div class="insight-type">OPTIMIZATION</div>
          <p>3 tasks can be parallelized to reduce timeline by 12 days</p>
          <button class="apply-btn">Apply Suggestion</button>
        </div>
        
        <div class="insight-card">
          <div class="insight-type">RESOURCE</div>
          <p>Sara UX Designer is overloaded - consider task redistribution</p>
          <button class="apply-btn">Reassign Tasks</button>
        </div>
        
        <div class="insight-card">
          <div class="insight-type">QUALITY</div>
          <p>Code review backlog detected - Thor QA Guardian available</p>
          <button class="apply-btn">Schedule Review</button>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Kanban Columns -->
  <div class="kanban-board" class:loading>
    {#each displayColumns as column (column.id)}
      <div class="kanban-column" style="border-top: 3px solid {column.color}">
        <!-- Column Header -->
        <div class="column-header">
          <div class="column-title">
            <span class="column-icon">{column.icon}</span>
            <span class="title-text">{column.title}</span>
            <span class="task-count">{column.tasks.length}</span>
            {#if column.limit}
              <span class="limit-indicator" class:warning={column.tasks.length >= column.limit}>
                /{column.limit}
              </span>
            {/if}
          </div>
          <p class="column-description">{column.description}</p>
        </div>
        
        <!-- Tasks Container -->
        <div 
          class="tasks-container"
          use:dndzone={{
            items: column.tasks,
            dragDisabled,
            dropTargetStyle: { outline: `2px dashed ${column.color}` }
          }}
          on:consider={(e) => handleDndConsider(column.id, e)}
          on:finalize={(e) => handleDndFinalize(column.id, e)}
        >
          {#each column.tasks as task (task.id)}
            <div 
              class="task-card" 
              animate:flip={{ duration: 300 }}
              on:click={() => openTaskModal(task)}
            >
              <!-- Task Header -->
              <div class="task-header">
                <div class="task-priority" style="background: {getPriorityColor(task.priority)}"></div>
                <div class="task-actions">
                  <button 
                    class="ai-action-btn"
                    on:click|stopPropagation={() => askAliAssistance(task)}
                    title="Ask Ali for assistance"
                  >
                    🤖
                  </button>
                </div>
              </div>
              
              <!-- Task Content -->
              <div class="task-content">
                <h4 class="task-title">{task.title}</h4>
                <p class="task-description">{task.description}</p>
                
                <!-- Tags -->
                {#if task.tags && task.tags.length > 0}
                  <div class="task-tags">
                    {#each task.tags as tag}
                      <span class="task-tag">{tag}</span>
                    {/each}
                  </div>
                {/if}
                
                <!-- Progress Bar -->
                {#if task.progress > 0}
                  <div class="progress-container">
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        style="width: {task.progress * 100}%; background: {getPriorityColor(task.priority)}"
                      ></div>
                    </div>
                    <span class="progress-text">{Math.round(task.progress * 100)}%</span>
                  </div>
                {/if}
                
                <!-- AI Insights -->
                {#if task.aiInsights}
                  <div class="ai-insights">
                    <span class="ai-icon">🧠</span>
                    <p>{task.aiInsights}</p>
                  </div>
                {/if}
              </div>
              
              <!-- Task Footer -->
              <div class="task-footer">
                <div class="assigned-agent">
                  <span class="agent-avatar">👤</span>
                  <span class="agent-name">{task.assignedAgent}</span>
                </div>
                
                <div class="task-meta">
                  <div class="due-date" class:overdue={new Date(task.dueDate) < new Date()}>
                    📅 {formatDueDate(task.dueDate)}
                  </div>
                  
                  <div class="task-stats">
                    {#if task.attachments > 0}
                      <span class="stat">📎 {task.attachments}</span>
                    {/if}
                    {#if task.comments > 0}
                      <span class="stat">💬 {task.comments}</span>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
        
        <!-- Add Task Button -->
        <button class="add-task-btn" on:click={createNewTask}>
          <span class="plus-icon">+</span>
          Add Task
        </button>
      </div>
    {/each}
  </div>
  
  <!-- Task Detail Modal -->
  {#if showTaskModal && selectedTask}
    <div class="modal-overlay" on:click={() => showTaskModal = false}>
      <div class="task-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>{selectedTask.title}</h3>
          <button class="close-btn" on:click={() => showTaskModal = false}>×</button>
        </div>
        
        <div class="modal-content">
          <div class="task-details-grid">
            <div class="detail-section">
              <label>Description</label>
              <textarea bind:value={selectedTask.description} rows="3"></textarea>
            </div>
            
            <div class="detail-section">
              <label>Assigned Agent</label>
              <select bind:value={selectedTask.assignedAgent}>
                <option>Marcus PM</option>
                <option>Sara UX Designer</option>
                <option>Baccio Tech Architect</option>
                <option>Dan Engineering GM</option>
                <option>Thor QA Guardian</option>
                <option>Luca Security Expert</option>
              </select>
            </div>
            
            <div class="detail-section">
              <label>Priority</label>
              <select bind:value={selectedTask.priority}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            
            <div class="detail-section">
              <label>Due Date</label>
              <input type="date" bind:value={selectedTask.dueDate} />
            </div>
            
            <div class="detail-section">
              <label>Progress</label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                bind:value={selectedTask.progress} 
              />
              <span>{Math.round(selectedTask.progress * 100)}%</span>
            </div>
            
            <div class="detail-section full-width">
              <label>AI Insights</label>
              <div class="ai-insights-display">
                <span class="ai-icon">🧠</span>
                <p>{selectedTask.aiInsights}</p>
              </div>
            </div>
          </div>
          
          <div class="modal-actions">
            <button class="action-btn secondary" on:click={() => showTaskModal = false}>
              Cancel
            </button>
            <button class="action-btn primary" on:click={() => showTaskModal = false}>
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .modern-kanban-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    min-height: 100vh;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }
  
  .modern-kanban-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
  
  .kanban-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
  }
  
  .kanban-title {
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .title-icon {
    font-size: 32px;
  }
  
  .kanban-subtitle {
    color: #cbd5e1;
    margin: 4px 0 0 44px;
    font-size: 14px;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .ai-assistant-btn {
    background: rgba(99, 102, 241, 0.2);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #6366f1;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .ai-assistant-btn.active {
    background: rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
  }
  
  .new-task-btn {
    background: rgba(16, 185, 129, 0.2);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .new-task-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
  }
  
  .real-time-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #cbd5e1;
    font-size: 14px;
  }
  
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
    animation: pulse 2s infinite;
  }
  
  .real-time-indicator.active .pulse-dot {
    background: #10b981;
  }
  
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
  
  .ai-assistant-panel {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
  }
  
  .assistant-header h3 {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .assistant-header p {
    color: #cbd5e1;
    font-size: 14px;
    margin-bottom: 16px;
  }
  
  .assistant-insights {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
  }
  
  .insight-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
  }
  
  .insight-type {
    font-size: 10px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  
  .insight-card p {
    color: #f8fafc;
    font-size: 14px;
    margin-bottom: 12px;
    line-height: 1.5;
  }
  
  .apply-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #6366f1;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .apply-btn:hover {
    background: rgba(99, 102, 241, 0.3);
  }
  
  .kanban-board {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 24px;
    position: relative;
    z-index: 1;
  }
  
  .kanban-column {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    min-height: 600px;
    display: flex;
    flex-direction: column;
  }
  
  .column-header {
    margin-bottom: 20px;
  }
  
  .column-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .column-icon {
    font-size: 18px;
  }
  
  .title-text {
    font-size: 16px;
    font-weight: 600;
    color: #f8fafc;
  }
  
  .task-count {
    background: rgba(255, 255, 255, 0.1);
    color: #cbd5e1;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }
  
  .limit-indicator {
    color: #cbd5e1;
    font-size: 12px;
  }
  
  .limit-indicator.warning {
    color: #f59e0b;
  }
  
  .column-description {
    color: #cbd5e1;
    font-size: 12px;
    margin: 0;
  }
  
  .tasks-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 200px;
  }
  
  .task-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
  }
  
  .task-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.25);
  }
  
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .task-priority {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  
  .task-actions {
    display: flex;
    gap: 8px;
  }
  
  .ai-action-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .ai-action-btn:hover {
    background: rgba(99, 102, 241, 0.3);
  }
  
  .task-title {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 600;
    margin: 0 0 8px 0;
    line-height: 1.3;
  }
  
  .task-description {
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.4;
    margin: 0 0 12px 0;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .task-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .task-tag {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 600;
  }
  
  .progress-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
  
  .progress-bar {
    flex: 1;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
  }
  
  .progress-text {
    color: #cbd5e1;
    font-size: 10px;
    font-weight: 600;
  }
  
  .ai-insights {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 12px;
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }
  
  .ai-insights p {
    color: #a78bfa;
    font-size: 11px;
    line-height: 1.4;
    margin: 0;
    font-style: italic;
  }
  
  .task-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }
  
  .assigned-agent {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .agent-avatar {
    font-size: 14px;
  }
  
  .agent-name {
    color: #cbd5e1;
    font-size: 11px;
    font-weight: 500;
  }
  
  .task-meta {
    text-align: right;
  }
  
  .due-date {
    color: #cbd5e1;
    font-size: 10px;
    margin-bottom: 4px;
  }
  
  .due-date.overdue {
    color: #fca5a5;
  }
  
  .task-stats {
    display: flex;
    gap: 8px;
  }
  
  .stat {
    color: #94a3b8;
    font-size: 10px;
  }
  
  .add-task-btn {
    background: rgba(255, 255, 255, 0.03);
    border: 2px dashed rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 16px;
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 16px;
  }
  
  .add-task-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.3);
  }
  
  .plus-icon {
    font-size: 18px;
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .task-modal {
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow: hidden;
  }
  
  .modal-header {
    background: rgba(99, 102, 241, 0.2);
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .modal-header h3 {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: #f8fafc;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
  }
  
  .modal-content {
    padding: 20px;
    overflow-y: auto;
    max-height: calc(90vh - 140px);
  }
  
  .task-details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .detail-section {
    display: flex;
    flex-direction: column;
  }
  
  .detail-section.full-width {
    grid-column: 1 / -1;
  }
  
  .detail-section label {
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .detail-section input,
  .detail-section select,
  .detail-section textarea {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 10px 12px;
    color: #f8fafc;
    font-size: 14px;
  }
  
  .detail-section input[type="range"] {
    margin-bottom: 8px;
  }
  
  .ai-insights-display {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
  }
  
  .ai-insights-display p {
    color: #a78bfa;
    font-size: 14px;
    line-height: 1.5;
    margin: 0;
    font-style: italic;
  }
  
  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }
  
  .action-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .action-btn.primary {
    background: #6366f1;
    color: white;
  }
  
  .action-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .action-btn:hover {
    transform: translateY(-2px);
  }
</style>