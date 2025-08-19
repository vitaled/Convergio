<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  // Cost data store with provider breakdown
  const costData = writable({
    total_cost_usd: 0.0,
    today_cost_usd: 0.0,
    total_interactions: 0,
    total_tokens: 0,
    active_sessions: 0,
    budget_utilization: 0.0,
    status: 'loading',
    provider_breakdown: {},
    model_breakdown: {},
    hourly_breakdown: {},
    last_updated: ''
  });

  let showDetails = false;
  let updateInterval: ReturnType<typeof setInterval> | null = null;

  async function fetchCostData() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:4000';
      const response = await fetch(`${apiUrl}/api/v1/cost-management/realtime/current`, {
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
          active_sessions: 0,
          budget_utilization: 0.0,
          status: 'unavailable',
          provider_breakdown: {},
          model_breakdown: {},
          hourly_breakdown: {},
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
        active_sessions: 0,
        budget_utilization: 0.0,
        status: 'error',
        provider_breakdown: {},
        model_breakdown: {},
        hourly_breakdown: {},
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

  function getProviderColor(provider: string): string {
    switch (provider.toLowerCase()) {
      case 'openai': return 'text-green-600';
      case 'anthropic': return 'text-purple-600';
      case 'perplexity': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  }
</script>

<!-- Cost Display Component -->
<div class="relative">
  <!-- Main Cost Display -->
  <button
    on:click={() => showDetails = !showDetails}
    class="flex items-center space-x-2 text-xs text-white/90 hover:bg-white/10 backdrop-blur-sm px-3 py-2 rounded-lg transition-all duration-300 border border-white/20"
    title="Click to toggle detailed cost breakdown"
  >
    <span class="text-xs">{getStatusIcon($costData.status)}</span>
    <div class="flex flex-col items-start">
      <span class="font-mono text-xs leading-tight">
        {formatCost($costData.total_cost_usd)}
      </span>
      {#if $costData.today_cost_usd > 0 && $costData.today_cost_usd !== $costData.total_cost_usd}
        <span class="font-mono text-xs opacity-75 leading-tight">
          {formatCost($costData.today_cost_usd)} today
        </span>
      {/if}
    </div>
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

  <!-- Enhanced Detailed Cost Panel -->
  {#if showDetails}
    <div class="absolute right-0 top-full mt-2 w-80 bg-slate-900/95 backdrop-blur-lg border border-white/20 rounded-xl shadow-2xl z-[60] p-4">
      <div class="space-y-4">
        <!-- Header -->
        <div class="flex items-center justify-between pb-2 border-b border-white/20">
          <h3 class="text-sm font-medium text-white">💰 Cost Overview</h3>
          <div class="flex items-center space-x-2">
            <span class="text-xs px-2 py-1 rounded-full font-mono {$costData.status === 'healthy' ? 'bg-green-500/20 text-green-400' : $costData.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' : $costData.status === 'exceeded' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/70'}">
              {$costData.status}
            </span>
          </div>
        </div>

        <!-- Cost Metrics -->
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <div class="text-xs text-white/70">Total Cost</div>
            <div class="text-sm font-mono font-medium text-white">
              {formatCost($costData.total_cost_usd)}
            </div>
          </div>
          
          <div class="space-y-1">
            <div class="text-xs text-white/70">Today</div>
            <div class="text-sm font-mono font-medium text-blue-400">
              {formatCost($costData.today_cost_usd)}
            </div>
          </div>
        </div>

        <!-- Budget Utilization -->
        {#if $costData.budget_utilization > 0}
          <div class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-white/70">Budget Used:</span>
              <span class="font-mono text-white">{$costData.budget_utilization.toFixed(1)}%</span>
            </div>
            <div class="w-full bg-white/20 rounded-full h-1.5">
              <div class="h-1.5 rounded-full {$costData.budget_utilization > 80 ? 'bg-red-400' : $costData.budget_utilization > 50 ? 'bg-yellow-400' : 'bg-green-400'}" 
                   style="width: {Math.min($costData.budget_utilization, 100)}%"></div>
            </div>
          </div>
        {/if}

        <!-- Provider Breakdown -->
        {#if Object.keys($costData.provider_breakdown).length > 0}
          <div class="space-y-2">
            <div class="text-xs font-medium text-white/90 flex items-center">
              <span>Provider Costs (Today)</span>
            </div>
            {#each Object.entries($costData.provider_breakdown) as [provider, cost]}
              <div class="flex justify-between items-center text-xs">
                <div class="flex items-center space-x-2">
                  <div class="w-2 h-2 rounded-full {provider === 'openai' ? 'bg-green-400' : provider === 'anthropic' ? 'bg-purple-400' : provider === 'perplexity' ? 'bg-blue-400' : 'bg-white/50'}"></div>
                  <span class="capitalize text-white/70">{provider}</span>
                </div>
                <span class="font-mono text-white">{formatCost(cost)}</span>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Top Models -->
        {#if Object.keys($costData.model_breakdown).length > 0}
          <div class="space-y-2">
            <div class="text-xs font-medium text-white/90">Top Models (Today)</div>
            {#each Object.entries($costData.model_breakdown).slice(0, 3) as [model, cost]}
              <div class="flex justify-between items-center text-xs">
                <span class="text-white/70 truncate">{model}</span>
                <span class="font-mono text-white">{formatCost(cost)}</span>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Usage Metrics -->
        {#if $costData.total_interactions > 0}
          <div class="pt-2 border-t border-white/20 space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-white/70">Interactions:</span>
              <span class="font-mono text-white">{$costData.total_interactions.toLocaleString()}</span>
            </div>
            
            <div class="flex justify-between text-xs">
              <span class="text-white/70">Tokens:</span>
              <span class="font-mono text-white">{$costData.total_tokens.toLocaleString()}</span>
            </div>

            {#if $costData.active_sessions > 0}
              <div class="flex justify-between text-xs">
                <span class="text-white/70">Active Sessions:</span>
                <span class="font-mono text-white">{$costData.active_sessions}</span>
              </div>
            {/if}
          </div>
        {/if}

        <!-- Last Updated -->
        <div class="pt-2 border-t border-white/20 flex justify-between items-center text-xs text-white/60">
          <span>Updated:</span>
          <span class="font-mono">
            {$costData.last_updated ? new Date($costData.last_updated + (($costData.last_updated.includes('Z') || $costData.last_updated.includes('+')) ? '' : 'Z')).toLocaleTimeString() : 'N/A'}
          </span>
        </div>

        <!-- Status Message -->
        {#if $costData.status === 'error' || $costData.status === 'unavailable'}
          <div class="pt-2 text-xs text-white/60 italic">
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
    class="fixed inset-0 z-[55]" 
    role="button"
    tabindex="-1"
    aria-label="Close cost details"
    on:click={() => showDetails = false}
    on:keydown={(e) => e.key === 'Escape' && (showDetails = false)}
  ></div>
{/if}