<script lang="ts">
  import { onMount } from 'svelte';
  import { costService, type CostOverview, type BudgetStatus } from '$lib/services/costService';

  let costData: CostOverview | null = null;
  let budgetData: BudgetStatus | null = null;
  let loading = true;
  let error: string | null = null;

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  }

  function formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num);
  }

  function getBudgetHealthColor(health?: string): string {
    switch (health) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  }

  async function loadCostData() {
    try {
      loading = true;
      error = null;
      
      const [cost, budget] = await Promise.all([
        costService.getCostOverview(),
        costService.getBudgetStatus()
      ]);
      
      costData = cost;
      budgetData = budget;
    } catch (err) {
      console.error('Failed to load cost data:', err);
      error = 'Failed to load cost data';
    } finally {
      loading = false;
    }
  }

  onMount(loadCostData);
</script>

<div class="bg-white border border-gray-200 rounded">
  <div class="px-4 py-3 border-b border-gray-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-gray-900">Cost Management</h3>
      <button 
        on:click={loadCostData}
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
        <div class="grid grid-cols-2 gap-4 mb-6">
          {#each Array(4) as _}
            <div class="bg-gray-100 p-4 rounded">
              <div class="w-16 h-6 bg-gray-200 rounded mb-1"></div>
              <div class="w-12 h-4 bg-gray-200 rounded"></div>
            </div>
          {/each}
        </div>
        <div class="space-y-3">
          {#each Array(4) as _}
            <div class="flex justify-between items-center p-3 border border-gray-100 rounded">
              <div class="w-24 h-4 bg-gray-200 rounded"></div>
              <div class="w-16 h-4 bg-gray-200 rounded"></div>
            </div>
          {/each}
        </div>
      </div>
    {:else if error}
      <div class="text-center text-red-600">
        <p>{error}</p>
        <button 
          on:click={loadCostData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Cost Overview -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded">
          <p class="text-2xl font-bold text-blue-600">
            {costData?.total_cost_usd ? formatCurrency(costData.total_cost_usd) : '-'}
          </p>
          <p class="text-sm text-blue-600">Total Cost</p>
        </div>
        <div class="bg-green-50 p-4 rounded">
          <p class="text-2xl font-bold text-green-600">
            {costData?.period_cost_usd ? formatCurrency(costData.period_cost_usd) : '-'}
          </p>
          <p class="text-sm text-green-600">Period Cost</p>
        </div>
        <div class="bg-purple-50 p-4 rounded">
          <p class="text-2xl font-bold text-purple-600">
            {costData?.cost_breakdown?.total_requests ? formatNumber(costData.cost_breakdown.total_requests) : '-'}
          </p>
          <p class="text-sm text-purple-600">Total Requests</p>
        </div>
        <div class="bg-orange-50 p-4 rounded">
          <p class="text-2xl font-bold text-orange-600">
            {budgetData?.utilization_percentage ? `${budgetData.utilization_percentage.toFixed(1)}%` : '-'}
          </p>
          <p class="text-sm text-orange-600">Budget Used</p>
        </div>
      </div>

      <!-- Budget Status -->
      {#if budgetData}
        <div class="mb-6 p-4 border border-gray-200 rounded">
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-xs font-medium text-gray-700">Budget Status</h4>
            <span class="text-xs px-2 py-1 rounded-full {getBudgetHealthColor(budgetData.budget_health)}">
              {budgetData.budget_health || 'unknown'}
            </span>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">Total Budget</span>
              <span class="font-medium">{formatCurrency(budgetData.total_budget_usd)}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">Used</span>
              <span class="font-medium">{formatCurrency(budgetData.used_budget_usd)}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">Remaining</span>
              <span class="font-medium text-green-600">{formatCurrency(budgetData.remaining_budget_usd)}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">Projected Monthly</span>
              <span class="font-medium">{formatCurrency(budgetData.projected_monthly_cost)}</span>
            </div>
          </div>
        </div>
      {/if}

      <!-- Top Models -->
      {#if costData?.top_models && costData.top_models.length > 0}
        <div class="mb-6">
          <h4 class="text-xs font-medium text-gray-700 mb-3">Top Models by Cost</h4>
          <div class="space-y-2">
            {#each costData.top_models.slice(0, 5) as model}
              <div class="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                <div>
                  <p class="text-sm font-medium text-gray-900">{model.model}</p>
                  <p class="text-xs text-gray-500">{formatNumber(model.usage_count)} requests</p>
                </div>
                <p class="text-sm font-medium">{formatCurrency(model.cost_usd)}</p>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Top Agents -->
      {#if costData?.top_agents && costData.top_agents.length > 0}
        <div>
          <h4 class="text-xs font-medium text-gray-700 mb-3">Top Agents by Cost</h4>
          <div class="space-y-2">
            {#each costData.top_agents.slice(0, 5) as agent}
              <div class="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                <div>
                  <p class="text-sm font-medium text-gray-900">{agent.agent_id}</p>
                  <p class="text-xs text-gray-500">{agent.percentage.toFixed(1)}% of total</p>
                </div>
                <p class="text-sm font-medium">{formatCurrency(agent.cost_usd)}</p>
              </div>
            {/each}
          </div>
        </div>
      {:else if costData}
        <div class="text-center text-gray-500">
          <p class="text-xs">No cost breakdown available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>