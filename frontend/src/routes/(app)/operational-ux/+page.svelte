<!--
Operational UX Test Page - Pagina di test per i componenti M4
Include Timeline, RunPanel e altri componenti per la verifica funzionale
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import Timeline from '$lib/components/Timeline.svelte';
  import RunPanel from '$lib/components/RunPanel.svelte';
  import { telemetryActions, telemetryHealth } from '$lib/stores/telemetry';
  
  // State
  let conversationId = 'conv_001'; // ID di esempio per testing
  let showAdvanced = false;
  let telemetryStatus = 'unknown';
  let lastHealthCheck = null;
  
  // Test conversation IDs
  const testConversations = [
    'conv_001',
    'conv_002',
    'conv_003'
  ];
  
  // Methods
  async function checkTelemetryHealth() {
    try {
      const isHealthy = await telemetryActions.checkHealth();
      telemetryStatus = isHealthy ? 'healthy' : 'unhealthy';
      lastHealthCheck = new Date();
    } catch (error) {
      telemetryStatus = 'error';
      console.error('Health check failed:', error);
    }
  }
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'unhealthy': return 'text-red-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }
  
  function getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '✅';
      case 'unhealthy': return '❌';
      case 'error': return '🚨';
      default: return '❓';
    }
  }
  
  // Lifecycle
  onMount(() => {
    checkTelemetryHealth();
    
    // Check health every 30 seconds
    const healthInterval = setInterval(checkTelemetryHealth, 30000);
    
    return () => clearInterval(healthInterval);
  });
</script>

<svelte:head>
  <title>Operational UX Test - Convergio</title>
  <meta name="description" content="Test page for Operational UX components" />
</svelte:head>

<div class="operational-ux-page">
  <!-- Header -->
  <div class="page-header">
    <h1 class="page-title">Operational UX Test Page</h1>
    <p class="page-description">
      Test page per i componenti M4: Timeline, RunPanel e Telemetry Store
    </p>
    
    <!-- Telemetry Status -->
    <div class="telemetry-status">
      <span class="status-label">Telemetry Status:</span>
      <span class="status-value {getStatusColor(telemetryStatus)}">
        {getStatusIcon(telemetryStatus)} {telemetryStatus}
      </span>
      {#if lastHealthCheck}
        <span class="last-check">
          Last check: {lastHealthCheck.toLocaleTimeString()}
        </span>
      {/if}
      <button 
        on:click={checkTelemetryHealth}
        class="btn-check-health"
        aria-label="Check telemetry health"
      >
        🔄 Check Health
      </button>
    </div>
  </div>
  
  <!-- Controls -->
  <div class="controls-section">
    <div class="control-group">
      <label for="conversation-select" class="control-label">
        Test Conversation:
      </label>
      <select 
        id="conversation-select"
        bind:value={conversationId}
        class="conversation-select"
      >
        {#each testConversations as convId}
          <option value={convId}>{convId}</option>
        {/each}
      </select>
    </div>
    
    <div class="control-group">
      <label class="control-label">
        <input 
          type="checkbox" 
          bind:checked={showAdvanced}
          class="checkbox-input"
        />
        Show Advanced Metrics
      </label>
    </div>
  </div>
  
  <!-- Components Grid -->
  <div class="components-grid">
    <!-- Timeline Component -->
    <div class="component-section">
      <div class="section-header">
        <h2 class="section-title">📊 Timeline Component</h2>
        <p class="section-description">
          Visualizza timeline per-turn delle conversazioni con speaker, tools, fonti, costi e razionali
        </p>
      </div>
      
      <div class="component-container">
        <Timeline 
          {conversationId}
          autoRefresh={true}
          showDetails={true}
        />
      </div>
    </div>
    
    <!-- RunPanel Component -->
    <div class="component-section">
      <div class="section-header">
        <h2 class="section-title">🎯 RunPanel Component</h2>
        <p class="section-description">
          Mostra metriche in tempo reale: budget, tokens, errori, partecipanti
        </p>
      </div>
      
      <div class="component-container">
        <RunPanel 
          {conversationId}
          autoRefresh={true}
          {showAdvanced}
        />
      </div>
    </div>
  </div>
  
  <!-- Feature Flags Info -->
  <div class="feature-flags-section">
    <div class="section-header">
      <h2 class="section-title">🚩 Feature Flags</h2>
      <p class="section-description">
        Configurazione dei feature flag per M4: Frontend Operational UX
      </p>
    </div>
    
    <div class="flags-grid">
      <div class="flag-item">
        <span class="flag-name">OPS_UI_ENABLED</span>
        <span class="flag-status enabled">✅ Enabled</span>
        <span class="flag-description">Abilita l'interfaccia operational UX</span>
      </div>
      
      <div class="flag-item">
        <span class="flag-name">RAG_IN_LOOP_ENABLED</span>
        <span class="flag-status enabled">✅ Enabled</span>
        <span class="flag-description">Abilita RAG per-turn (Wave 2)</span>
      </div>
      
      <div class="flag-item">
        <span class="flag-name">DECISION_ENGINE_ENABLED</span>
        <span class="flag-status enabled">✅ Enabled</span>
        <span class="flag-description">Abilita Decision Engine (Wave 1)</span>
      </div>
    </div>
  </div>
  
  <!-- Acceptance Criteria -->
  <div class="acceptance-section">
    <div class="section-header">
      <h2 class="section-title">✅ Acceptance Criteria</h2>
      <p class="section-description">
        Criteri di accettazione per M4: Frontend Operational UX
      </p>
    </div>
    
    <div class="criteria-grid">
      <div class="criterion-item">
        <span class="criterion-icon">📊</span>
        <div class="criterion-content">
          <h4 class="criterion-title">95% eventi telemetria visibili</h4>
          <p class="criterion-description">
            Tutti gli eventi di telemetria devono essere visibili nell'interfaccia
          </p>
          <span class="criterion-status">In Progress</span>
        </div>
      </div>
      
      <div class="criterion-item">
        <span class="criterion-icon">⚖️</span>
        <div class="criterion-content">
          <h4 class="criterion-title">Valori UI ~ backend ±5%</h4>
          <p class="criterion-description">
            I valori mostrati nell'UI devono corrispondere al backend con tolleranza ±5%
          </p>
          <span class="criterion-status">In Progress</span>
        </div>
      </div>
      
      <div class="criterion-item">
        <span class="criterion-icon">♿</span>
        <div class="criterion-content">
          <h4 class="criterion-title">A11y ≥95</h4>
          <p class="criterion-description">
            Accessibilità deve essere ≥95% secondo gli standard WCAG
          </p>
          <span class="criterion-status">In Progress</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Testing Instructions -->
  <div class="testing-section">
    <div class="section-header">
      <h2 class="section-title">🧪 Testing Instructions</h2>
      <p class="section-description">
        Come testare i componenti M4
      </p>
    </div>
    
    <div class="testing-steps">
      <ol class="steps-list">
        <li>
          <strong>Verifica Timeline:</strong> Cambia conversation ID e verifica che la timeline si aggiorni
        </li>
        <li>
          <strong>Verifica RunPanel:</strong> Controlla che le metriche si aggiornino in tempo reale
        </li>
        <li>
          <strong>Verifica Responsive:</strong> Ridimensiona la finestra per testare la responsività
        </li>
        <li>
          <strong>Verifica A11y:</strong> Usa screen reader e navigazione da tastiera
        </li>
        <li>
          <strong>Verifica Performance:</strong> Controlla che i componenti si carichino rapidamente
        </li>
      </ol>
    </div>
  </div>
</div>

<style>
  .operational-ux-page {
    @apply min-h-screen bg-gray-50 p-6;
  }
  
  .page-header {
    @apply mb-8 text-center;
  }
  
  .page-title {
    @apply text-3xl font-bold text-gray-900 mb-2;
  }
  
  .page-description {
    @apply text-lg text-gray-600 mb-6;
  }
  
  .telemetry-status {
    @apply flex items-center justify-center gap-4 p-4 bg-white rounded-lg shadow-sm border border-gray-200;
  }
  
  .status-label {
    @apply text-gray-600 font-medium;
  }
  
  .status-value {
    @apply font-semibold;
  }
  
  .last-check {
    @apply text-sm text-gray-500;
  }
  
  .btn-check-health {
    @apply px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors;
  }
  
  .controls-section {
    @apply mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-200;
  }
  
  .control-group {
    @apply flex items-center gap-4 mb-4 last:mb-0;
  }
  
  .control-label {
    @apply text-gray-700 font-medium flex items-center gap-2;
  }
  
  .conversation-select {
    @apply px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500;
  }
  
  .checkbox-input {
    @apply w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500;
  }
  
  .components-grid {
    @apply grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8;
  }
  
  .component-section {
    @apply bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden;
  }
  
  .section-header {
    @apply p-6 border-b border-gray-200;
  }
  
  .section-title {
    @apply text-xl font-semibold text-gray-900 mb-2;
  }
  
  .section-description {
    @apply text-gray-600;
  }
  
  .component-container {
    @apply p-6;
  }
  
  .feature-flags-section,
  .acceptance-section,
  .testing-section {
    @apply mb-8 p-6 bg-white rounded-lg shadow-sm border border-gray-200;
  }
  
  .flags-grid {
    @apply grid grid-cols-1 md:grid-cols-3 gap-4;
  }
  
  .flag-item {
    @apply p-4 border border-gray-200 rounded-lg;
  }
  
  .flag-name {
    @apply block font-mono text-sm font-semibold text-gray-900 mb-2;
  }
  
  .flag-status {
    @apply inline-block px-2 py-1 text-xs font-medium rounded mb-2;
  }
  
  .flag-status.enabled {
    @apply bg-green-100 text-green-800;
  }
  
  .flag-description {
    @apply text-sm text-gray-600;
  }
  
  .criteria-grid {
    @apply grid grid-cols-1 md:grid-cols-3 gap-6;
  }
  
  .criterion-item {
    @apply flex items-start gap-4 p-4 border border-gray-200 rounded-lg;
  }
  
  .criterion-icon {
    @apply text-2xl;
  }
  
  .criterion-content {
    @apply flex-1;
  }
  
  .criterion-title {
    @apply font-semibold text-gray-900 mb-2;
  }
  
  .criterion-description {
    @apply text-sm text-gray-600 mb-2;
  }
  
  .criterion-status {
    @apply inline-block px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded;
  }
  
  .testing-steps {
    @apply mt-4;
  }
  
  .steps-list {
    @apply list-decimal list-inside space-y-2 text-gray-700;
  }
  
  .steps-list li {
    @apply pl-2;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .operational-ux-page {
      @apply p-4;
    }
    
    .telemetry-status {
      @apply flex-col gap-2;
    }
    
    .control-group {
      @apply flex-col items-start gap-2;
    }
    
    .components-grid {
      @apply grid-cols-1 gap-6;
    }
    
    .flags-grid,
    .criteria-grid {
      @apply grid-cols-1 gap-4;
    }
  }
  
  /* Accessibility */
  .operational-ux-page:focus-within {
    @apply outline-none;
  }
  
  .component-section:focus-within {
    @apply ring-2 ring-blue-500 ring-offset-2;
  }
  
  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .operational-ux-page {
      @apply bg-gray-900;
    }
    
    .page-title {
      @apply text-white;
    }
    
    .page-description {
      @apply text-gray-300;
    }
    
    .telemetry-status,
    .controls-section,
    .component-section,
    .feature-flags-section,
    .acceptance-section,
    .testing-section {
      @apply bg-gray-800 border-gray-700;
    }
    
    .section-title {
      @apply text-white;
    }
    
    .section-description {
      @apply text-gray-300;
    }
    
    .flag-name {
      @apply text-white;
    }
    
    .criterion-title {
      @apply text-white;
    }
    
    .criterion-description {
      @apply text-gray-300;
    }
  }
</style>
