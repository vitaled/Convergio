<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  interface ApiStatus {
    openai: { connected: boolean; model?: string; error?: string };
    anthropic: { connected: boolean; model?: string; error?: string };
    perplexity: { connected: boolean; model?: string; error?: string };
    backend: { connected: boolean; version?: string };
  }
  
  let isOpen = false;
  let apiStatus: ApiStatus = {
    openai: { connected: false },
    anthropic: { connected: false },
    perplexity: { connected: false },
    backend: { connected: false }
  };
  
  let overallStatus: 'online' | 'partial' | 'offline' = 'offline';
  let intervalId: NodeJS.Timeout;
  
  onMount(() => {
    checkApiStatus();
    // Check status every 30 seconds
    intervalId = setInterval(checkApiStatus, 30000);
  });
  
  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
  
  async function checkApiStatus() {
    try {
      // Check system API status (from .env configuration)
      const systemResponse = await fetch('http://localhost:9000/api/v1/system/api-status', {
        signal: AbortSignal.timeout(3000)
      });
      
      if (systemResponse.ok) {
        const systemStatus = await systemResponse.json();
        
        // Update backend status
        apiStatus.backend = { 
          connected: systemStatus.backend?.connected || false, 
          version: systemStatus.backend?.version || 'Unknown'
        };
        
        // Update OpenAI status from system config
        apiStatus.openai = {
          connected: systemStatus.openai?.connected || false,
          model: systemStatus.openai?.model || undefined,
          error: systemStatus.openai?.connected ? undefined : 'Not configured in .env'
        };
        
        // Update Anthropic status from system config
        apiStatus.anthropic = {
          connected: systemStatus.anthropic?.connected || false,
          model: systemStatus.anthropic?.model || undefined,
          error: systemStatus.anthropic?.connected ? undefined : 'Not configured in .env'
        };
        
        // Update Perplexity status from system config
        apiStatus.perplexity = {
          connected: systemStatus.perplexity?.connected || false,
          model: systemStatus.perplexity?.model || undefined,
          error: systemStatus.perplexity?.connected ? undefined : 'Not configured in .env'
        };
      } else {
        apiStatus.backend = { connected: false };
      }
      
      // Also check user-provided keys (optional override)
      try {
        const keysResponse = await fetch('http://localhost:9000/api/v1/user-keys/status', {
          signal: AbortSignal.timeout(3000)
        });
        
        if (keysResponse.ok) {
          const keysStatus = await keysResponse.json();
          
          // Override with user keys if provided
          if (keysStatus.openai?.is_configured) {
            apiStatus.openai.connected = true;
            apiStatus.openai.model = 'GPT-4 (User)';
            apiStatus.openai.error = keysStatus.openai?.is_valid === false ? 'Invalid user API key' : undefined;
          }
          
          if (keysStatus.anthropic?.is_configured) {
            apiStatus.anthropic.connected = true;
            apiStatus.anthropic.model = 'Claude 3 (User)';
            apiStatus.anthropic.error = keysStatus.anthropic?.is_valid === false ? 'Invalid user API key' : undefined;
          }
          
          if (keysStatus.perplexity?.is_configured) {
            apiStatus.perplexity.connected = true;
            apiStatus.perplexity.model = 'Sonar (User)';
            apiStatus.perplexity.error = keysStatus.perplexity?.is_valid === false ? 'Invalid user API key' : undefined;
          }
        }
      } catch (userKeysError) {
        // User keys are optional, don't fail if not available
        console.log('User keys not checked:', userKeysError);
      }
      
    } catch (error) {
      console.error('Failed to check API status:', error);
      apiStatus.backend = { connected: false };
    }
    
    // Calculate overall status
    updateOverallStatus();
  }
  
  function updateOverallStatus() {
    const connectedCount = [
      apiStatus.backend.connected,
      apiStatus.openai.connected,
      apiStatus.anthropic.connected,
      apiStatus.perplexity.connected
    ].filter(Boolean).length;
    
    if (!apiStatus.backend.connected) {
      overallStatus = 'offline';
    } else if (connectedCount === 4) {
      overallStatus = 'online';
    } else if (connectedCount > 1) {
      overallStatus = 'partial';
    } else {
      overallStatus = 'offline';
    }
  }
  
  function getStatusColor(status: 'online' | 'partial' | 'offline') {
    switch (status) {
      case 'online': return 'text-green-600';
      case 'partial': return 'text-yellow-600';
      case 'offline': return 'text-red-600';
    }
  }
  
  function getStatusBgColor(status: 'online' | 'partial' | 'offline') {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'partial': return 'bg-yellow-500';
      case 'offline': return 'bg-red-500';
    }
  }
  
  function getServiceIcon(service: string) {
    switch (service) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'perplexity': return '🔍';
      case 'backend': return '⚙️';
      default: return '📡';
    }
  }
  
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.api-status-dropdown')) {
      isOpen = false;
    }
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="api-status-dropdown relative">
  <!-- Status Button -->
  <button
    on:click|stopPropagation={() => isOpen = !isOpen}
    class="flex items-center space-x-2 text-xs {getStatusColor(overallStatus)} hover:opacity-80 transition-opacity cursor-pointer"
    aria-label="API connection status"
    aria-expanded={isOpen}
  >
    <div class="h-1.5 w-1.5 {getStatusBgColor(overallStatus)} rounded-full animate-pulse"></div>
    <span class="hidden sm:inline capitalize">{overallStatus}</span>
    <svg
      class="w-3 h-3 transition-transform {isOpen ? 'rotate-180' : ''}"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
    </svg>
  </button>
  
  <!-- Dropdown Panel -->
  {#if isOpen}
    <div
      class="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
      on:click|stopPropagation
    >
      <div class="p-3 border-b border-gray-100">
        <h3 class="text-xs font-semibold text-gray-900">API Connection Status</h3>
        <p class="text-xs text-gray-500 mt-0.5">Real-time service availability</p>
      </div>
      
      <div class="p-2 space-y-2">
        <!-- Backend Status -->
        <div class="flex items-center justify-between p-2 rounded hover:bg-gray-50">
          <div class="flex items-center space-x-2">
            <span class="text-base">{getServiceIcon('backend')}</span>
            <div>
              <p class="text-xs font-medium text-gray-900">Backend Server</p>
              <p class="text-xs text-gray-500">
                {#if apiStatus.backend.connected}
                  v{apiStatus.backend.version || 'Unknown'}
                {:else}
                  Not connected
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <div class="h-2 w-2 rounded-full {apiStatus.backend.connected ? 'bg-green-500' : 'bg-red-500'}"></div>
            <span class="text-xs {apiStatus.backend.connected ? 'text-green-600' : 'text-red-600'}">
              {apiStatus.backend.connected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        
        <!-- OpenAI Status -->
        <div class="flex items-center justify-between p-2 rounded hover:bg-gray-50">
          <div class="flex items-center space-x-2">
            <span class="text-base">{getServiceIcon('openai')}</span>
            <div>
              <p class="text-xs font-medium text-gray-900">OpenAI</p>
              <p class="text-xs text-gray-500">
                {#if apiStatus.openai.connected}
                  {apiStatus.openai.model || 'Connected'}
                {:else if apiStatus.openai.error}
                  {apiStatus.openai.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <div class="h-2 w-2 rounded-full {apiStatus.openai.connected ? 'bg-green-500' : 'bg-gray-300'}"></div>
            <span class="text-xs {apiStatus.openai.connected ? 'text-green-600' : 'text-gray-500'}">
              {apiStatus.openai.connected ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <!-- Anthropic Status -->
        <div class="flex items-center justify-between p-2 rounded hover:bg-gray-50">
          <div class="flex items-center space-x-2">
            <span class="text-base">{getServiceIcon('anthropic')}</span>
            <div>
              <p class="text-xs font-medium text-gray-900">Anthropic</p>
              <p class="text-xs text-gray-500">
                {#if apiStatus.anthropic.connected}
                  {apiStatus.anthropic.model || 'Connected'}
                {:else if apiStatus.anthropic.error}
                  {apiStatus.anthropic.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <div class="h-2 w-2 rounded-full {apiStatus.anthropic.connected ? 'bg-green-500' : 'bg-gray-300'}"></div>
            <span class="text-xs {apiStatus.anthropic.connected ? 'text-green-600' : 'text-gray-500'}">
              {apiStatus.anthropic.connected ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <!-- Perplexity Status -->
        <div class="flex items-center justify-between p-2 rounded hover:bg-gray-50">
          <div class="flex items-center space-x-2">
            <span class="text-base">{getServiceIcon('perplexity')}</span>
            <div>
              <p class="text-xs font-medium text-gray-900">Perplexity</p>
              <p class="text-xs text-gray-500">
                {#if apiStatus.perplexity.connected}
                  {apiStatus.perplexity.model || 'Web Search Ready'}
                {:else if apiStatus.perplexity.error}
                  {apiStatus.perplexity.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <div class="h-2 w-2 rounded-full {apiStatus.perplexity.connected ? 'bg-green-500' : 'bg-yellow-500'}"></div>
            <span class="text-xs {apiStatus.perplexity.connected ? 'text-green-600' : 'text-yellow-600'}">
              {apiStatus.perplexity.connected ? 'Active' : 'Optional'}
            </span>
          </div>
        </div>
      </div>
      
      <div class="p-3 border-t border-gray-100 bg-gray-50">
        <div class="flex items-center justify-between">
          <p class="text-xs text-gray-500">
            Last checked: {new Date().toLocaleTimeString()}
          </p>
          <button
            on:click={checkApiStatus}
            class="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>