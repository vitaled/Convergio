<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let projectId: string = '';
  export let timeRange: string = '30d';
  
  let loading = true;
  let selectedMetric = 'overview';
  let realTimeData = writable({});
  let chartData: any = {};
  let kpiMetrics: any = {};
  let aiInsights: any[] = [];
  
  // Modern glassmorphism colors with data visualization palette
  const colors = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    background: 'rgba(15, 23, 42, 1)',
    glass: 'rgba(255, 255, 255, 0.1)',
    glassBorder: 'rgba(255, 255, 255, 0.2)',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    chartGradients: [
      'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
      'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
      'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
      'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)'
    ]
  };
  
  // Mock KPI data with AI insights
  const mockKPIMetrics = {
    overview: {
      totalProjects: { value: 24, change: +12, target: 30 },
      activeAgents: { value: 48, change: +3, target: 50 },
      completionRate: { value: 87.5, change: +5.2, target: 90 },
      averageVelocity: { value: 42, change: -2.1, target: 45 },
      costEfficiency: { value: 94.2, change: +3.8, target: 95 },
      clientSatisfaction: { value: 4.8, change: +0.3, target: 5.0 }
    },
    performance: {
      taskThroughput: { value: 156, change: +23, target: 180 },
      averageResponseTime: { value: 2.4, change: -0.6, target: 2.0 },
      errorRate: { value: 0.8, change: -0.3, target: 0.5 },
      systemUptime: { value: 99.94, change: +0.02, target: 99.95 },
      aiOptimizationScore: { value: 92.1, change: +4.5, target: 95 },
      resourceUtilization: { value: 78.3, change: +2.1, target: 80 }
    },
    business: {
      revenue: { value: 245000, change: +18500, target: 300000 },
      profitMargin: { value: 34.2, change: +2.8, target: 35 },
      customerAcquisition: { value: 89, change: +12, target: 100 },
      retentionRate: { value: 96.8, change: +1.2, target: 97 },
      marketingROI: { value: 4.2, change: +0.8, target: 5.0 },
      timeToMarket: { value: 21, change: -3, target: 18 }
    }
  };
  
  // Mock AI insights with proactive recommendations
  const mockAIInsights = [
    {
      type: 'optimization',
      priority: 'high',
      title: 'Project Velocity Optimization',
      message: 'Ali detected 15% velocity improvement opportunity by reallocating Marcus PM and Sara UX Designer to parallel tracks',
      confidence: 0.94,
      estimatedImpact: '+6.3 story points/sprint',
      recommendation: 'Implement parallel workflow for design and development phases',
      agent: 'Ali Chief of Staff'
    },
    {
      type: 'resource',
      priority: 'medium',
      title: 'Resource Bottleneck Alert',
      message: 'Thor QA Guardian is operating at 95% capacity - consider load balancing or additional QA resources',
      confidence: 0.87,
      estimatedImpact: '-12% delivery risk',
      recommendation: 'Schedule Luca Security Expert for cross-functional QA support',
      agent: 'Marcus PM'
    },
    {
      type: 'cost',
      priority: 'high',
      title: 'Cost Efficiency Opportunity',
      message: 'AI model optimization could reduce operational costs by 23% while maintaining quality standards',
      confidence: 0.91,
      estimatedImpact: '$18,500/month savings',
      recommendation: 'Implement dynamic model selection based on task complexity',
      agent: 'Amy CFO'
    },
    {
      type: 'quality',
      priority: 'medium',
      title: 'Quality Assurance Enhancement',
      message: 'Pattern analysis suggests implementing automated testing will increase delivery quality by 28%',
      confidence: 0.83,
      estimatedImpact: '+28% quality score',
      recommendation: 'Deploy Thor QA Guardian automated testing pipeline',
      agent: 'Baccio Tech Architect'
    }
  ];
  
  // Mock chart data for visualizations
  const mockChartData = {
    projectVelocity: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [
        { label: 'Completed', data: [12, 19, 15, 22], color: colors.success },
        { label: 'In Progress', data: [8, 12, 10, 15], color: colors.primary },
        { label: 'Planned', data: [15, 18, 20, 25], color: colors.warning }
      ]
    },
    agentUtilization: {
      labels: ['Marcus PM', 'Sara UX', 'Baccio Arch', 'Dan Eng', 'Thor QA', 'Ali Chief'],
      datasets: [
        { label: 'Utilization %', data: [85, 92, 78, 88, 95, 72], color: colors.secondary }
      ]
    },
    costTrends: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        { label: 'AI Costs', data: [12500, 13200, 11800, 14100, 13600, 12900], color: colors.danger },
        { label: 'Infrastructure', data: [8500, 8800, 8200, 8900, 8600, 8400], color: colors.info },
        { label: 'Revenue', data: [45000, 48500, 42000, 52000, 49500, 51200], color: colors.success }
      ]
    }
  };
  
  onMount(async () => {
    await loadAnalyticsData();
    await loadAIInsights();
    setupRealTimeUpdates();
    loading = false;
  });
  
  async function loadAnalyticsData() {
    try {
      if (projectId) {
        const response = await fetch(`/api/v1/analytics/project/${projectId}?range=${timeRange}`);
        if (response.ok) {
          const data = await response.json();
          kpiMetrics = data.kpis || mockKPIMetrics;
          chartData = data.charts || mockChartData;
        }
      } else {
        // Global analytics
        const response = await fetch(`/api/v1/analytics/global?range=${timeRange}`);
        if (response.ok) {
          const data = await response.json();
          kpiMetrics = data.kpis || mockKPIMetrics;
          chartData = data.charts || mockChartData;
        }
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
      kpiMetrics = mockKPIMetrics;
      chartData = mockChartData;
    }
  }
  
  async function loadAIInsights() {
    try {
      const response = await fetch('/api/v1/agents/ali/analytics-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          metrics: kpiMetrics,
          time_range: timeRange
        })
      });
      
      if (response.ok) {
        aiInsights = await response.json();
      }
    } catch (error) {
      console.error('Failed to load AI insights:', error);
      aiInsights = mockAIInsights;
    }
  }
  
  function setupRealTimeUpdates() {
    // Simulate real-time metric updates
    setInterval(() => {
      realTimeData.update(data => ({
        ...data,
        timestamp: new Date(),
        activeUsers: Math.floor(Math.random() * 50) + 150,
        systemLoad: Math.random() * 100,
        throughput: Math.floor(Math.random() * 20) + 40
      }));
    }, 5000);
  }
  
  function formatMetricValue(value: number, type: string): string {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', { 
          style: 'currency', 
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'decimal':
        return value.toFixed(2);
      case 'rating':
        return `${value.toFixed(1)}/5.0`;
      case 'days':
        return `${value} days`;
      default:
        return value.toLocaleString();
    }
  }
  
  function getChangeIcon(change: number): string {
    if (change > 0) return '📈';
    if (change < 0) return '📉';
    return '➖';
  }
  
  function getChangeColor(change: number): string {
    if (change > 0) return colors.success;
    if (change < 0) return colors.danger;
    return colors.textSecondary;
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return colors.danger;
      case 'medium': return colors.warning;
      case 'low': return colors.success;
      default: return colors.primary;
    }
  }
  
  function getInsightIcon(type: string): string {
    switch (type) {
      case 'optimization': return '⚡';
      case 'resource': return '👥';
      case 'cost': return '💰';
      case 'quality': return '🎯';
      case 'risk': return '⚠️';
      default: return '🧠';
    }
  }
  
  async function implementRecommendation(insight: any) {
    try {
      const response = await fetch('/api/v1/agents/implement-recommendation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendation: insight.recommendation,
          agent: insight.agent,
          project_id: projectId
        })
      });
      
      if (response.ok) {
        alert(`✅ ${insight.agent} is implementing: ${insight.recommendation}`);
        // Reload insights
        await loadAIInsights();
      }
    } catch (error) {
      console.error('Failed to implement recommendation:', error);
      alert(`🤖 ${insight.agent} has been notified to implement the recommendation`);
    }
  }
  
  $: currentMetrics = kpiMetrics[selectedMetric] || {};
</script>

<div class="modern-analytics-container">
  <!-- Header with Controls -->
  <div class="analytics-header">
    <div class="header-left">
      <h2 class="analytics-title">
        <span class="title-icon">📊</span>
        Analytics Intelligence
      </h2>
      <p class="analytics-subtitle">AI-powered insights and performance metrics</p>
    </div>
    
    <div class="header-controls">
      <!-- Time Range Selector -->
      <div class="time-range-selector">
        <select bind:value={timeRange} on:change={loadAnalyticsData}>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 3 Months</option>
          <option value="1y">Last Year</option>
        </select>
      </div>
      
      <!-- Metric Category Tabs -->
      <div class="metric-tabs">
        <button 
          class="tab-btn"
          class:active={selectedMetric === 'overview'}
          on:click={() => selectedMetric = 'overview'}
        >
          Overview
        </button>
        <button 
          class="tab-btn"
          class:active={selectedMetric === 'performance'}
          on:click={() => selectedMetric = 'performance'}
        >
          Performance
        </button>
        <button 
          class="tab-btn"
          class:active={selectedMetric === 'business'}
          on:click={() => selectedMetric === 'business'}
        >
          Business
        </button>
      </div>
      
      <!-- Real-time indicator -->
      <div class="real-time-status">
        <div class="pulse-dot"></div>
        <span>Live</span>
      </div>
    </div>
  </div>
  
  <!-- AI Insights Panel -->
  {#if aiInsights.length > 0}
    <div class="ai-insights-panel">
      <div class="insights-header">
        <h3>
          <span class="ai-icon">🧠</span>
          AI Strategic Insights
        </h3>
        <p>Proactive recommendations from your AI team</p>
      </div>
      
      <div class="insights-grid">
        {#each aiInsights as insight}
          <div class="insight-card" style="border-left: 4px solid {getPriorityColor(insight.priority)}">
            <div class="insight-header">
              <div class="insight-meta">
                <span class="insight-icon">{getInsightIcon(insight.type)}</span>
                <span class="insight-type">{insight.type.toUpperCase()}</span>
                <span class="priority-badge" style="background: {getPriorityColor(insight.priority)}">
                  {insight.priority.toUpperCase()}
                </span>
              </div>
              <div class="confidence-score">
                {Math.round(insight.confidence * 100)}% confidence
              </div>
            </div>
            
            <h4 class="insight-title">{insight.title}</h4>
            <p class="insight-message">{insight.message}</p>
            
            <div class="insight-impact">
              <span class="impact-label">Estimated Impact:</span>
              <span class="impact-value">{insight.estimatedImpact}</span>
            </div>
            
            <div class="insight-recommendation">
              <span class="rec-label">Recommendation:</span>
              <p class="rec-text">{insight.recommendation}</p>
            </div>
            
            <div class="insight-actions">
              <span class="agent-attribution">by {insight.agent}</span>
              <button 
                class="implement-btn"
                on:click={() => implementRecommendation(insight)}
              >
                Implement
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- KPI Metrics Grid -->
  <div class="kpi-grid">
    {#each Object.entries(currentMetrics) as [key, metric]}
      <div class="kpi-card">
        <div class="kpi-header">
          <h4 class="kpi-title">{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h4>
          <span class="change-indicator" style="color: {getChangeColor(metric.change)}">
            {getChangeIcon(metric.change)}
          </span>
        </div>
        
        <div class="kpi-value">
          {#if key === 'revenue'}
            {formatMetricValue(metric.value, 'currency')}
          {:else if key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') || key.includes('Uptime')}
            {formatMetricValue(metric.value, 'percentage')}
          {:else if key.includes('Satisfaction')}
            {formatMetricValue(metric.value, 'rating')}
          {:else if key.includes('Time') && key.includes('Response')}
            {formatMetricValue(metric.value, 'decimal')}s
          {:else if key.includes('Time')}
            {formatMetricValue(metric.value, 'days')}
          {:else}
            {formatMetricValue(metric.value, 'number')}
          {/if}
        </div>
        
        <div class="kpi-meta">
          <div class="change-info">
            <span class="change-value" style="color: {getChangeColor(metric.change)}">
              {metric.change > 0 ? '+' : ''}{formatMetricValue(Math.abs(metric.change), 
                key === 'revenue' ? 'currency' : 
                key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') ? 'percentage' : 'number')}
            </span>
            <span class="change-period">vs last period</span>
          </div>
          
          <div class="target-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                style="width: {Math.min((metric.value / metric.target) * 100, 100)}%; background: {colors.primary}"
              ></div>
            </div>
            <span class="target-label">Target: {formatMetricValue(metric.target, 
              key === 'revenue' ? 'currency' : 
              key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') ? 'percentage' : 'number')}</span>
          </div>
        </div>
      </div>
    {/each}
  </div>
  
  <!-- Charts Section -->
  <div class="charts-section">
    <div class="chart-card">
      <h3 class="chart-title">Project Velocity Trends</h3>
      <div class="chart-container">
        <!-- Simplified chart visualization -->
        <div class="simple-chart">
          {#each chartData.projectVelocity?.datasets || [] as dataset, i}
            <div class="chart-legend-item">
              <div class="legend-color" style="background: {dataset.color}"></div>
              <span>{dataset.label}</span>
            </div>
          {/each}
          <div class="chart-bars">
            {#each chartData.projectVelocity?.labels || [] as label, i}
              <div class="bar-group">
                <div class="bar-label">{label}</div>
                {#each chartData.projectVelocity?.datasets || [] as dataset, j}
                  <div 
                    class="chart-bar" 
                    style="height: {(dataset.data[i] / 30) * 100}%; background: {dataset.color}"
                  ></div>
                {/each}
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
    
    <div class="chart-card">
      <h3 class="chart-title">Agent Utilization</h3>
      <div class="chart-container">
        <div class="utilization-chart">
          {#each chartData.agentUtilization?.labels || [] as agent, i}
            {@const utilization = chartData.agentUtilization?.datasets[0]?.data[i] || 0}
            <div class="utilization-row">
              <div class="agent-name">{agent}</div>
              <div class="utilization-bar">
                <div 
                  class="utilization-fill" 
                  style="width: {utilization}%; background: {utilization > 90 ? colors.danger : utilization > 80 ? colors.warning : colors.success}"
                ></div>
              </div>
              <div class="utilization-value">{utilization}%</div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
  
  <!-- Real-time Metrics -->
  {#if $realTimeData.timestamp}
    <div class="realtime-panel">
      <h3 class="realtime-title">
        <span class="pulse-icon">📡</span>
        Real-time Metrics
      </h3>
      
      <div class="realtime-grid">
        <div class="realtime-metric">
          <span class="metric-label">Active Users</span>
          <span class="metric-value">{$realTimeData.activeUsers}</span>
        </div>
        
        <div class="realtime-metric">
          <span class="metric-label">System Load</span>
          <span class="metric-value">{$realTimeData.systemLoad?.toFixed(1)}%</span>
        </div>
        
        <div class="realtime-metric">
          <span class="metric-label">Throughput</span>
          <span class="metric-value">{$realTimeData.throughput}/min</span>
        </div>
        
        <div class="realtime-metric">
          <span class="metric-label">Last Update</span>
          <span class="metric-value">{$realTimeData.timestamp?.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .modern-analytics-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    min-height: 100vh;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }
  
  .modern-analytics-container::before {
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
  
  .analytics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .analytics-title {
    font-size: 32px;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .title-icon {
    font-size: 36px;
  }
  
  .analytics-subtitle {
    color: #cbd5e1;
    margin: 6px 0 0 52px;
    font-size: 16px;
  }
  
  .header-controls {
    display: flex;
    align-items: center;
    gap: 20px;
  }
  
  .time-range-selector select {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f8fafc;
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 14px;
  }
  
  .metric-tabs {
    display: flex;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 4px;
    backdrop-filter: blur(12px);
  }
  
  .tab-btn {
    padding: 10px 20px;
    border: none;
    background: transparent;
    color: #cbd5e1;
    border-radius: 8px;
    transition: all 0.3s ease;
    font-weight: 500;
  }
  
  .tab-btn.active {
    background: rgba(99, 102, 241, 0.3);
    color: #6366f1;
  }
  
  .real-time-status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #10b981;
    font-size: 14px;
    font-weight: 500;
  }
  
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
  
  .ai-insights-panel {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .insights-header h3 {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .insights-header p {
    color: #cbd5e1;
    font-size: 14px;
    margin-bottom: 20px;
  }
  
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
  }
  
  .insight-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
  }
  
  .insight-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  }
  
  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .insight-meta {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .insight-icon {
    font-size: 18px;
  }
  
  .insight-type {
    font-size: 10px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .priority-badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    color: white;
  }
  
  .confidence-score {
    color: #10b981;
    font-size: 12px;
    font-weight: 600;
  }
  
  .insight-title {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  .insight-message {
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 12px;
  }
  
  .insight-impact {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  
  .impact-label {
    color: #94a3b8;
    font-size: 12px;
  }
  
  .impact-value {
    color: #10b981;
    font-size: 12px;
    font-weight: 600;
  }
  
  .insight-recommendation {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
  }
  
  .rec-label {
    color: #a78bfa;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .rec-text {
    color: #ddd6fe;
    font-size: 13px;
    margin: 6px 0 0 0;
    line-height: 1.4;
  }
  
  .insight-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .agent-attribution {
    color: #94a3b8;
    font-size: 11px;
    font-style: italic;
  }
  
  .implement-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #6366f1;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .implement-btn:hover {
    background: rgba(99, 102, 241, 0.3);
    transform: translateY(-1px);
  }
  
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .kpi-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s ease;
  }
  
  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  }
  
  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .kpi-title {
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
  }
  
  .change-indicator {
    font-size: 16px;
  }
  
  .kpi-value {
    color: #f8fafc;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 16px;
    line-height: 1;
  }
  
  .kpi-meta {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .change-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .change-value {
    font-size: 14px;
    font-weight: 600;
  }
  
  .change-period {
    color: #94a3b8;
    font-size: 12px;
  }
  
  .target-progress {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .progress-bar {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.5s ease;
  }
  
  .target-label {
    color: #94a3b8;
    font-size: 11px;
  }
  
  .charts-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 24px;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .chart-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
  }
  
  .chart-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
  }
  
  .simple-chart {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .chart-legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #cbd5e1;
    font-size: 12px;
  }
  
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }
  
  .chart-bars {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 150px;
    gap: 12px;
  }
  
  .bar-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 1;
  }
  
  .bar-label {
    color: #94a3b8;
    font-size: 11px;
    text-align: center;
  }
  
  .chart-bar {
    width: 100%;
    min-height: 4px;
    border-radius: 2px;
    transition: height 0.5s ease;
  }
  
  .utilization-chart {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .utilization-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .agent-name {
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 500;
    min-width: 80px;
  }
  
  .utilization-bar {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .utilization-fill {
    height: 100%;
    transition: width 0.5s ease;
  }
  
  .utilization-value {
    color: #f8fafc;
    font-size: 12px;
    font-weight: 600;
    min-width: 35px;
    text-align: right;
  }
  
  .realtime-panel {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    z-index: 1;
  }
  
  .realtime-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .pulse-icon {
    animation: pulse 2s infinite;
  }
  
  .realtime-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
  }
  
  .realtime-metric {
    display: flex;
    flex-direction: column;
    gap: 4px;
    text-align: center;
  }
  
  .metric-label {
    color: #94a3b8;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .metric-value {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 700;
  }
</style>