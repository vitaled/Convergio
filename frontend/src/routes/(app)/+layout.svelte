<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import AliAssistant from '$lib/components/AliAssistant.svelte';
  import CostDisplay from '$lib/components/CostDisplay.svelte';
  import ApiStatusDropdown from '$lib/components/ApiStatusDropdown.svelte';
  import '$lib/styles/modern-ui.css';
  
  // MVP navigation items (simplified for initial release)
  const navItems = [
    { href: '/agents', label: 'AI Team', iconPath: '/convergio_icons/users.svg' },
    { href: '/pm', label: 'Projects', iconPath: '/convergio_icons/projects.svg' },
    { href: '/dashboard', label: 'Analytics', iconPath: '/convergio_icons/analytics.svg' },
    { href: '/settings', label: 'Settings', iconPath: '/convergio_icons/settings.svg' }
  ];
  
  // 🚧 ROADMAP: Advanced features removed for MVP simplification
  // Future Phase 2 navigation items (Q2-Q3 2025):
  // - CEO Dashboard (Executive business intelligence)
  // - Agent Management (Advanced CRUD operations)  
  // - Swarm Coordination (Multi-agent orchestration)
  
  let healthStatus: any = null;
  const APP_VERSION: string = (typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : (typeof __VERSION__ !== 'undefined' ? __VERSION__ : '0.0.0')) as unknown as string;
  
  onMount(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:4000';
      const response = await fetch(`${apiUrl}/health`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        healthStatus = await response.json();
      }
    } catch (error) {
      // No fallback - show real error state
      healthStatus = null;
      console.error('Failed to get health status:', error);
    }
  });
  
  // SEMPLICE: controlla se il path corrente inizia con l'href del menu
  function isActive(href: string): boolean {
    const currentPath = $page.url.pathname;
    
    // Per la home page
    if (href === '/') {
      return currentPath === '/';
    }
    
    // Per le altre pagine: controllo esatto del path
    return currentPath === href;
  }
</script>

<!-- Modern Light Glassmorphism Layout -->
<div class="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 font-mono text-sm">
  <!-- Light Glassmorphism Top Navigation -->
  <div class="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-14">
        <!-- Logo & Title -->
        <div class="flex items-center space-x-4">
          <button on:click={() => goto('/')} class="flex items-center space-x-3 hover:opacity-75 transition-all">
            <img src="/convergio_logo.png" alt="Platform Convergio" class="h-8 w-auto" />
            <span class="text-gray-800 font-medium tracking-tight">platform.Convergio.io</span>
          </button>
        </div>
        
        <!-- Glassmorphism Navigation -->
        <nav class="hidden md:flex items-center space-x-4">
          {#each navItems as item}
            <a
              href={item.href}
              sveltekit:prefetch
              aria-current={isActive(item.href) ? 'page' : undefined}
              class="flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-300 {isActive(item.href)
                ? 'bg-gray-200/60 text-gray-900 border border-gray-300/50 shadow-md'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/50 border border-transparent'}"
            >
              <img src={item.iconPath} alt="" class="h-3 w-3" />
              <span>{item.label}</span>
            </a>
          {/each}
        </nav>
        
        <!-- Status & Cost Indicators -->
        <div class="flex items-center space-x-4">
          <!-- Cost Display -->
          <CostDisplay />
          
          <!-- Version -->
          <div class="hidden md:block text-xs text-white/60 tracking-wide">
            v{APP_VERSION}
          </div>
          
          <!-- API Status Dropdown -->
          <ApiStatusDropdown />
        </div>
      </div>
    </div>
  </div>
  
  <!-- Content Area -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <slot />
  </main>
  
  <!-- Ali Assistant (always present) -->
  <AliAssistant />
</div>