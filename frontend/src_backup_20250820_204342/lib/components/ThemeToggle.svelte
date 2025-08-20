<script lang="ts">
  import { theme, resolvedTheme, themeUtils } from '$lib/stores/themeStore';
  import type { Theme } from '$lib/stores/themeStore';
  
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'button' | 'dropdown' | 'minimal' = 'button';
  export let showLabel = true;
  
  $: currentTheme = $theme;
  $: isResolvedDark = $resolvedTheme === 'dark';
  
  // Configurazione dimensioni
  const sizes = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base', 
    lg: 'w-12 h-12 text-lg'
  };
  
  // Icone per i temi
  const themeIcons = {
    light: '☀️',
    dark: '🌙',
    system: '🖥️'
  };
  
  const themeLabels = {
    light: 'Light',
    dark: 'Dark', 
    system: 'System'
  };
  
  function handleThemeChange(newTheme: Theme) {
    themeUtils.setTheme(newTheme);
  }
  
  function handleToggle() {
    themeUtils.toggleTheme();
  }
  
  function handleCycle() {
    themeUtils.cycleTheme();
  }
</script>

{#if variant === 'button'}
  <!-- Pulsante semplice toggle light/dark -->
  <button
    on:click={handleToggle}
    class="inline-flex items-center justify-center {sizes[size]} 
           bg-surface-100 hover:bg-surface-200 dark:bg-surface-800 dark:hover:bg-surface-700
           border border-surface-300 dark:border-surface-600 rounded-lg 
           text-surface-700 dark:text-surface-300 
           transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
    title={isResolvedDark ? 'Switch to light mode' : 'Switch to dark mode'}
    aria-label="Toggle theme"
  >
    <span class="transition-transform duration-300 {isResolvedDark ? 'rotate-180' : ''}">
      {isResolvedDark ? themeIcons.light : themeIcons.dark}
    </span>
  </button>

{:else if variant === 'dropdown'}
  <!-- Dropdown con tutte le opzioni -->
  <div class="relative group">
    <button
      class="inline-flex items-center gap-2 px-3 py-2 
             bg-surface-100 hover:bg-surface-200 dark:bg-surface-800 dark:hover:bg-surface-700
             border border-surface-300 dark:border-surface-600 rounded-lg 
             text-surface-700 dark:text-surface-300 text-sm
             transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
      aria-label="Theme selector"
    >
      <span>{themeIcons[currentTheme]}</span>
      {#if showLabel}
        <span>{themeLabels[currentTheme]}</span>
      {/if}
      <svg class="w-4 h-4 transition-transform group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </button>
    
    <!-- Dropdown menu -->
    <div class="absolute right-0 mt-2 w-32 opacity-0 invisible group-hover:opacity-100 group-hover:visible
                bg-surface-50 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg shadow-lg 
                transition-all duration-200 z-50">
      {#each Object.entries(themeLabels) as [themeKey, label]}
        <button
          on:click={() => handleThemeChange(themeKey as Theme)}
          class="w-full flex items-center gap-2 px-3 py-2 text-left text-sm
                 text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700
                 first:rounded-t-lg last:rounded-b-lg transition-colors duration-150
                 {currentTheme === themeKey ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300' : ''}"
        >
          <span>{themeIcons[themeKey as Theme]}</span>
          <span>{label}</span>
          {#if currentTheme === themeKey}
            <span class="ml-auto text-primary-600 dark:text-primary-400">✓</span>
          {/if}
        </button>
      {/each}
    </div>
  </div>

{:else if variant === 'minimal'}
  <!-- Versione minimale - solo icona -->
  <button
    on:click={handleCycle}
    class="inline-flex items-center justify-center {sizes[size]}
           text-surface-600 hover:text-surface-900 dark:text-surface-400 dark:hover:text-surface-100
           hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg
           transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
    title={`Current: ${themeLabels[currentTheme]} (click to cycle)`}
    aria-label="Cycle theme"
  >
    <span class="transition-all duration-300 {isResolvedDark ? 'scale-110' : ''}">
      {themeIcons[currentTheme]}
    </span>
  </button>
{/if}

<style>
  /* Animazioni personalizzate per le transizioni tema */
  .group:hover .opacity-0 {
    transition-delay: 150ms;
  }
  
  /* Focus visibile per accessibilità */
  button:focus-visible {
    outline: 2px solid rgb(var(--color-primary));
    outline-offset: 2px;
  }
</style>