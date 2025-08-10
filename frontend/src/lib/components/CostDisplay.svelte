<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  // Cost data store
  const costData = writable({
    total_cost_usd: 0.0,
    today_cost_usd: 0.0,
    total_interactions: 0,
    total_tokens: 0,
    status: 'loading',
    last_updated: ''
  });

  let showDetails = false;
  let updateInterval: ReturnType<typeof setInterval> | null = null;

  async function fetchCostData() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/cost-management/realtime/current', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        costData.set(data);
      } else {
        console.warn('Cost API unavailable, using fallback');
        costData.set({
          total_cost_usd: 0.0,
          today_cost_usd: 0.0,
          total_interactions: 0,
          total_tokens: 0,
          status: 'unavailable',
          last_updated: new Date().toISOString()
        });
      }
    } catch (error) {
      console.warn('Cost tracking unavailable:', error);
      costData.set({
        total_cost_usd: 0.0,
        today_cost_usd: 0.0,
        total_interactions: 0,
        total_tokens: 0,
        status: 'error',
        last_updated: new Date().toISOString()
      });
    }
  }

  onMount(() => {
    // Initial fetch
    fetchCostData();
    
    // Update every 30 seconds
    updateInterval = setInterval(fetchCostData, 30000);
  });

  onDestroy(() => {
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  });

  function formatCost(amount: number): string {
    if (amount === 0) return '$0.00';
    if (amount < 0.01) return '<$0.01';
    return `$${amount.toFixed(2)}`;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'moderate': return 'text-yellow-600';
      case 'warning': return 'text-orange-600';
      case 'exceeded': return 'text-red-600';
      case 'error': case 'unavailable': return 'text-gray-400';
      default: return 'text-blue-600';
    }
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '💚';
      case 'moderate': return '💛';
      case 'warning': return '🟠';
      case 'exceeded': return '🔴';
      case 'error': case 'unavailable': return '⚪';
      default: return '🔵';
    }
  }
</script>

<!-- Cost Display Component -->
<div class="relative">
  <!-- Main Cost Display -->
  <button
    on:click={() => showDetails = !showDetails}
    class="flex items-center space-x-2 text-xs {getStatusColor($costData.status)} hover:bg-gray-50 px-2 py-1 rounded-md transition-colors"
    title="Click to toggle cost details"
  >
    <span class="text-xs">{getStatusIcon($costData.status)}</span>
    <span class="font-mono">
      {formatCost($costData.total_cost_usd)}
    </span>
    {#if showDetails}
      <svg class="h-3 w-3 transform rotate-180" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    {:else}
      <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    {/if}
  </button>

  <!-- Detailed Cost Panel -->
  {#if showDetails}
    <div class="absolute right-0 top-full mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4">
      <div class="space-y-3">
        <!-- Header -->
        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
          <h3 class="text-sm font-medium text-gray-900">💰 Cost Overview</h3>
          <span class="text-xs text-gray-500 font-mono">
            {$costData.status}
          </span>
        </div>

        <!-- Cost Metrics -->
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <div class="text-xs text-gray-500">Total Cost</div>
            <div class="text-sm font-mono font-medium text-gray-900">
              {formatCost($costData.total_cost_usd)}
            </div>
          </div>
          
          <div class="space-y-1">
            <div class="text-xs text-gray-500">Today</div>
            <div class="text-sm font-mono font-medium text-blue-600">
              {formatCost($costData.today_cost_usd)}
            </div>
          </div>
        </div>

        <!-- Usage Metrics -->
        {#if $costData.total_interactions > 0}
          <div class="pt-2 border-t border-gray-100 space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">Interactions:</span>
              <span class="font-mono text-gray-900">{$costData.total_interactions.toLocaleString()}</span>
            </div>
            
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">Tokens:</span>
              <span class="font-mono text-gray-900">{$costData.total_tokens.toLocaleString()}</span>
            </div>
          </div>
        {/if}

        <!-- Last Updated -->
        <div class="pt-2 border-t border-gray-100 flex justify-between items-center text-xs text-gray-400">
          <span>Updated:</span>
          <span class="font-mono">
            {new Date($costData.last_updated).toLocaleTimeString()}
          </span>
        </div>

        <!-- Status Message -->
        {#if $costData.status === 'error' || $costData.status === 'unavailable'}
          <div class="pt-2 text-xs text-gray-500 italic">
            Cost tracking temporarily unavailable
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<!-- Click outside to close -->
{#if showDetails}
  <div 
    class="fixed inset-0 z-40" 
    role="button"
    tabindex="-1"
    aria-label="Close cost details"
    on:click={() => showDetails = false}
    on:keydown={(e) => e.key === 'Escape' && (showDetails = false)}
  ></div>
{/if}