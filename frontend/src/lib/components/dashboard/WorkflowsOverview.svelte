<script lang="ts">
  import { onMount } from 'svelte';
  import { workflowsService, type Workflow, type RecentExecution } from '$lib/services/workflowsService';

  let workflows: Workflow[] = [];
  let recentExecutions: RecentExecution[] = [];
  let loading = true;
  let error: string | null = null;

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'running': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'cancelled': return 'text-gray-600 bg-gray-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'active': return 'text-green-600 bg-green-50';
      case 'inactive': return 'text-gray-600 bg-gray-50';
      case 'draft': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
  }

  async function loadWorkflowsData() {
    try {
      loading = true;
      error = null;
      
      const [workflowsData, executionsData] = await Promise.all([
        workflowsService.getWorkflows(),
        workflowsService.getRecentExecutions()
      ]);
      
      workflows = workflowsData || [];
      recentExecutions = executionsData || [];
    } catch (err) {
      console.error('Failed to load workflows data:', err);
      error = 'Failed to load workflows data';
    } finally {
      loading = false;
    }
  }

  onMount(loadWorkflowsData);

  $: activeWorkflows = workflows.filter(w => w.status === 'active');
  $: totalExecutions = workflows.reduce((sum, w) => sum + w.execution_count, 0);
  $: avgSuccessRate = workflows.length > 0 
    ? workflows.reduce((sum, w) => sum + w.success_rate, 0) / workflows.length 
    : 0;
</script>

<div class="bg-white border border-gray-200 rounded">
  <div class="px-4 py-3 border-b border-gray-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-gray-900">Workflows & Automation</h3>
      <button 
        on:click={loadWorkflowsData}
        class="text-xs text-gray-500 hover:text-gray-700 flex items-center space-x-1"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>
  </div>

  <div class="p-4">
    {#if loading}
      <div class="animate-pulse space-y-4">
        <div class="grid grid-cols-3 gap-4 mb-6">
          {#each Array(3) as _}
            <div class="bg-gray-100 p-4 rounded">
              <div class="w-16 h-6 bg-gray-200 rounded mb-1"></div>
              <div class="w-12 h-4 bg-gray-200 rounded"></div>
            </div>
          {/each}
        </div>
        {#each Array(5) as _}
          <div class="flex items-center space-x-3 p-3 border border-gray-100 rounded">
            <div class="w-8 h-8 bg-gray-200 rounded"></div>
            <div class="flex-1">
              <div class="w-32 h-4 bg-gray-200 rounded mb-1"></div>
              <div class="w-48 h-3 bg-gray-200 rounded"></div>
            </div>
            <div class="w-16 h-4 bg-gray-200 rounded"></div>
          </div>
        {/each}
      </div>
    {:else if error}
      <div class="text-center text-red-600">
        <p>{error}</p>
        <button 
          on:click={loadWorkflowsData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Workflow Stats -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded">
          <p class="text-2xl font-bold text-blue-600">{workflows.length}</p>
          <p class="text-sm text-blue-600">Total Workflows</p>
        </div>
        <div class="bg-green-50 p-4 rounded">
          <p class="text-2xl font-bold text-green-600">{activeWorkflows.length}</p>
          <p class="text-sm text-green-600">Active</p>
        </div>
        <div class="bg-purple-50 p-4 rounded">
          <p class="text-2xl font-bold text-purple-600">{avgSuccessRate.toFixed(1)}%</p>
          <p class="text-sm text-purple-600">Avg Success Rate</p>
        </div>
      </div>

      <!-- Workflows List -->
      {#if workflows.length > 0}
        <div class="mb-6">
          <h4 class="text-xs font-medium text-gray-700 mb-3">Active Workflows</h4>
          <div class="space-y-3">
            {#each workflows.slice(0, 5) as workflow}
              <div class="flex items-center justify-between p-3 border border-gray-100 rounded hover:bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded flex items-center justify-center">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900">{workflow.name}</p>
                    <p class="text-xs text-gray-500">
                      {workflow.description} • {workflow.steps?.length || 0} steps
                    </p>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <div class="text-right">
                    <p class="text-xs text-gray-500">
                      {workflow.execution_count} executions
                    </p>
                    <p class="text-xs text-gray-500">
                      {workflow.success_rate.toFixed(1)}% success
                    </p>
                  </div>
                  <span class="text-xs px-2 py-1 rounded-full {getStatusColor(workflow.status)}">
                    {workflow.status}
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Recent Executions -->
      {#if recentExecutions.length > 0}
        <div>
          <h4 class="text-xs font-medium text-gray-700 mb-3">Recent Executions</h4>
          <div class="space-y-2">
            {#each recentExecutions.slice(0, 6) as execution}
              <div class="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <div>
                  <p class="text-sm font-medium text-gray-900">{execution.workflow_name}</p>
                  <p class="text-xs text-gray-500">
                    {formatDate(execution.started_at)} • {formatDuration(execution.duration)}
                  </p>
                </div>
                <div class="flex items-center space-x-2">
                  <span class="text-xs text-gray-500">
                    {execution.success_rate.toFixed(1)}%
                  </span>
                  <span class="text-xs px-2 py-1 rounded-full {getStatusColor(execution.status)}">
                    {execution.status}
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {:else if workflows.length === 0}
        <div class="text-center text-gray-500">
          <p class="text-xs">No workflows or executions available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>