<script lang="ts">
	import { onMount } from 'svelte';
	import ModernKanbanBoard from '$lib/components/modern/ModernKanbanBoard.svelte';
	import ModernGanttChart from '$lib/components/modern/ModernGanttChart.svelte';
	import ModernAnalyticsDashboard from '$lib/components/modern/ModernAnalyticsDashboard.svelte';
	import AIProjectIntegration from '$lib/components/modern/AIProjectIntegration.svelte';
	
	let selectedProjectId = '';
	let projects: any[] = [];
	let selectedView: 'kanban' | 'gantt' | 'analytics' | 'ai_integration' = 'kanban';
	let projectAnalytics: any = null;
	let loading = false;
	
	onMount(async () => {
		await loadProjects();
	});
	
	async function loadProjects() {
		loading = true;
		try {
			const response = await fetch('/api/v1/pm/projects');
			if (response.ok) {
				projects = await response.json();
				if (projects.length > 0) {
					selectedProjectId = projects[0].id;
					await loadProjectAnalytics();
				}
			}
		} catch (error) {
			console.error('Failed to load projects:', error);
		} finally {
			loading = false;
		}
	}
	
	async function loadProjectAnalytics() {
		if (!selectedProjectId) return;
		
		try {
			const response = await fetch(`/api/v1/pm/projects/${selectedProjectId}/analytics`);
			if (response.ok) {
				projectAnalytics = await response.json();
			}
		} catch (error) {
			console.error('Failed to load project analytics:', error);
		}
	}
	
	async function createNewProject() {
		const projectName = prompt('Enter project name:');
		if (!projectName) return;
		
		try {
			const response = await fetch('/api/v1/pm/projects', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: projectName,
					description: 'Created via PM interface',
					status: 'PLANNING'
				})
			});
			
			if (response.ok) {
				await loadProjects();
			}
		} catch (error) {
			console.error('Failed to create project:', error);
		}
	}
	
	function getStatusColor(status: string): string {
		switch (status) {
			case 'COMPLETED': return 'text-green-600';
			case 'IN_PROGRESS': return 'text-blue-600';
			case 'ON_HOLD': return 'text-yellow-600';
			case 'PLANNING': return 'text-purple-600';
			default: return 'text-gray-600';
		}
	}
	
	$: if (selectedProjectId) {
		loadProjectAnalytics();
	}
</script>

<div class="pm-container">
	<!-- Header -->
	<div class="pm-header">
		<div class="header-left">
			<h1 class="text-2xl font-bold">Project Management</h1>
			<p class="text-gray-600">AI-Powered Project Intelligence</p>
		</div>
		
		<div class="header-right">
			<button
				on:click={createNewProject}
				class="btn-primary"
			>
				+ New Project
			</button>
		</div>
	</div>
	
	<!-- Project Selector and View Toggle -->
	<div class="controls-bar">
		<div class="project-selector">
			<label for="project-select" class="text-sm text-gray-600">Current Project:</label>
			<select
				id="project-select"
				bind:value={selectedProjectId}
				class="project-dropdown"
			>
				{#each projects as project}
					<option value={project.id}>
						{project.name} ({project.status})
					</option>
				{/each}
			</select>
			
			{#if projectAnalytics}
				<div class="project-stats">
					<span class="stat-item">
						📊 {projectAnalytics.performance_metrics.total_tasks} tasks
					</span>
					<span class="stat-item">
						✅ {projectAnalytics.performance_metrics.completed_tasks} completed
					</span>
					<span class="stat-item">
						📈 {Math.round(projectAnalytics.performance_metrics.avg_progress)}% progress
					</span>
				</div>
			{/if}
		</div>
		
		<div class="view-toggle">
			<button
				class:active={selectedView === 'kanban'}
				on:click={() => selectedView = 'kanban'}
				class="view-btn"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
				</svg>
				Kanban
			</button>
			
			<button
				class:active={selectedView === 'gantt'}
				on:click={() => selectedView = 'gantt'}
				class="view-btn"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				Gantt
			</button>
			
			<button
				class:active={selectedView === 'ai_integration'}
				on:click={() => selectedView = 'ai_integration'}
				class="view-btn"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
				</svg>
				AI Team
			</button>
			
			<button
				class:active={selectedView === 'analytics'}
				on:click={() => selectedView = 'analytics'}
				class="view-btn"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
				</svg>
				Analytics
			</button>
		</div>
	</div>
	
	<!-- Main Content Area -->
	<div class="content-area">
		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>Loading project data...</p>
			</div>
		{:else if selectedProjectId}
			{#if selectedView === 'kanban'}
				<ModernKanbanBoard projectId={selectedProjectId} />
			{:else if selectedView === 'gantt'}
				<ModernGanttChart projectId={selectedProjectId} />
			{:else if selectedView === 'ai_integration'}
				<AIProjectIntegration projectId={selectedProjectId} />
			{:else if selectedView === 'analytics'}
				<ModernAnalyticsDashboard projectId={selectedProjectId} />
			{/if}
		{:else}
			<div class="empty-state">
				<svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
				</svg>
				<h3 class="text-lg font-semibold mb-2">No Projects Yet</h3>
				<p class="text-gray-600 mb-4">Create your first project to get started</p>
				<button on:click={createNewProject} class="btn-primary">
					Create Project
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	.pm-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #f9fafb;
	}
	
	.pm-header {
		background: white;
		padding: 1.5rem 2rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.header-left h1 {
		margin: 0;
	}
	
	.header-left p {
		margin: 0.25rem 0 0 0;
		font-size: 0.875rem;
	}
	
	.btn-primary {
		background: #3b82f6;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		border: none;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.2s;
	}
	
	.btn-primary:hover {
		background: #2563eb;
	}
	
	.controls-bar {
		background: white;
		padding: 1rem 2rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.project-selector {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.project-dropdown {
		padding: 0.5rem 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		min-width: 200px;
	}
	
	.project-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.stat-item {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	
	.view-toggle {
		display: flex;
		gap: 0.5rem;
	}
	
	.view-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border: 1px solid #e5e7eb;
		background: white;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.view-btn:hover {
		background: #f3f4f6;
	}
	
	.view-btn.active {
		background: #3b82f6;
		color: white;
		border-color: #3b82f6;
	}
	
	.content-area {
		flex: 1;
		padding: 2rem;
		overflow: auto;
	}
	
	.loading-state, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		text-align: center;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #e5e7eb;
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.analytics-view {
		background: white;
		border-radius: 8px;
		padding: 1.5rem;
	}
	
	.analytics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}
	
	.metric-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 1.5rem;
	}
	
	.metric-card h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #374151;
	}
	
	.metric-value {
		font-size: 2rem;
		font-weight: bold;
		color: #111827;
		margin-bottom: 0.25rem;
	}
	
	.metric-label {
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 1rem;
	}
	
	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
		margin: 1rem 0 0.5rem 0;
	}
	
	.progress-fill {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s ease;
	}
	
	.agent-list {
		padding: 1rem;
		background: white;
		border-radius: 6px;
	}
</style>