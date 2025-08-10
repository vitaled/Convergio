<script lang="ts">
  import type { Project } from '$lib/services/dashboardService';
  import { createEventDispatcher } from 'svelte';
  
  export let project: Project;
  export let loading: boolean = false;

  const dispatch = createEventDispatcher();

  $: statusColor = {
    'planning': 'bg-yellow-100 text-yellow-800',
    'in-progress': 'bg-blue-100 text-blue-800',
    'review': 'bg-purple-100 text-purple-800',
    'completed': 'bg-green-100 text-green-800'
  }[project.status] || 'bg-gray-100 text-gray-800';

  $: priorityColor = {
    'low': 'bg-gray-100 text-gray-800',
    'medium': 'bg-blue-100 text-blue-800',
    'high': 'bg-orange-100 text-orange-800',
    'critical': 'bg-red-100 text-red-800'
  }[project.priority] || 'bg-gray-100 text-gray-800';

  $: progressColor = project.progress >= 80 ? 'bg-green-500' : 
                     project.progress >= 60 ? 'bg-blue-500' : 
                     project.progress >= 40 ? 'bg-yellow-500' : 
                     'bg-red-500';

  function handleClick() {
    dispatch('click', { project });
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
</script>

<div 
  class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer {loading ? 'opacity-60' : ''}"
  on:click={handleClick}
>
  <div class="flex items-start justify-between mb-4">
    <div class="flex-1">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">
        {loading ? '...' : (project.project_name || project.name)}
      </h3>
      <p class="text-sm text-gray-600 mb-3">
        {loading ? '...' : project.description}
      </p>
      
      <div class="flex items-center space-x-3 mb-3">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {statusColor}">
          {loading ? '...' : project.status.replace('-', ' ')}
        </span>
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {priorityColor}">
          {loading ? '...' : project.priority}
        </span>
        <span class="text-xs text-gray-500">
          {loading ? '...' : (project.project_type || project.type)}
        </span>
      </div>
    </div>
    
    <div class="text-right">
      <p class="text-sm text-gray-600">Due</p>
      <p class="text-sm font-medium text-gray-900">
        {loading ? '...' : formatDate(project.dueDate)}
      </p>
    </div>
  </div>

  <div class="space-y-3">
    <!-- Progress Bar -->
    <div>
      <div class="flex items-center justify-between text-sm mb-1">
        <span class="text-gray-600">Progress</span>
        <span class="font-medium text-gray-900">{loading ? '...' : project.progress}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div 
          class="h-2 rounded-full transition-all duration-300 {progressColor}"
          style="width: {loading ? '0%' : project.progress + '%'}"
        ></div>
      </div>
    </div>

    <!-- Budget and Revenue -->
    <div class="flex items-center justify-between text-sm">
      <div>
        <span class="text-gray-600">Budget:</span>
        <span class="font-medium text-gray-900 ml-1">
          {loading ? '...' : formatCurrency(project.budget)}
        </span>
      </div>
      <div>
        <span class="text-gray-600">Target:</span>
        <span class="font-medium text-gray-900 ml-1">
          {loading ? '...' : formatCurrency(project.revenue_target)}
        </span>
      </div>
    </div>

    <!-- Assigned Agents -->
    {#if project.assigned_agents && project.assigned_agents.length > 0}
      <div class="flex items-center space-x-2">
        <span class="text-xs text-gray-600">Agents:</span>
        <div class="flex -space-x-1">
          {#each project.assigned_agents.slice(0, 3) as agent, i}
            <div class="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs text-white font-medium">
              {agent.charAt(0).toUpperCase()}
            </div>
          {/each}
          {#if project.assigned_agents.length > 3}
            <div class="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-xs text-gray-600 font-medium">
              +{project.assigned_agents.length - 3}
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
