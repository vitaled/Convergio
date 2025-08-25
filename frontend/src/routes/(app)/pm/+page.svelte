<script lang="ts">
	import { onMount } from 'svelte';
	import ModernKanbanBoard from '$lib/components/modern/ModernKanbanBoard.svelte';
	import ModernGanttChart from '$lib/components/modern/ModernGanttChart.svelte';
	import ModernAnalyticsDashboard from '$lib/components/modern/ModernAnalyticsDashboard.svelte';
	import AIProjectIntegration from '$lib/components/modern/AIProjectIntegration.svelte';
	import PMOrchestrationDashboard from '$lib/components/orchestration/PMOrchestrationDashboard.svelte';
	
	let selectedProjectId = '';
	let projects: any[] = [];
	let selectedView: 'orchestration' | 'kanban' | 'gantt' | 'analytics' | 'ai_integration' = 'orchestration';
	let projectAnalytics: any = null;
	let loading = false;
	let error = '';
	let orchestrationEnabled = true; // Toggle for orchestration features
	
	onMount(async () => {
		await loadProjects();
	});
	
	async function loadProjects() {
		loading = true;
		error = '';
		try {
			const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
			const response = await fetch(`${apiUrl}/api/v1/projects/engagements`);
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			const data = await response.json();
			projects = data.engagements || [];
			
			if (projects.length > 0 && !selectedProjectId) {
				selectedProjectId = projects[0].id;
				await loadProjectAnalytics(selectedProjectId);
			}
		} catch (err) {
			console.error('Error loading projects:', err);
			error = err instanceof Error ? err.message : 'Failed to load projects';
		} finally {
			loading = false;
		}
	}
	
	async function loadProjectAnalytics(projectId: string) {
		try {
			const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
			const response = await fetch(`${apiUrl}/api/v1/projects/engagements/${projectId}/details`);
			if (response.ok) {
				const data = await response.json();
				projectAnalytics = data;
			}
		} catch (err) {
			console.error('Error loading project analytics:', err);
		}
	}
	
	async function createProject(title: string, description: string) {
		try {
			const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
			const response = await fetch(`${apiUrl}/api/v1/projects/engagements`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ title, description })
			});
			
			if (response.ok) {
				await loadProjects();
			}
		} catch (err) {
			console.error('Error creating project:', err);
		}
	}
	
	async function handleProjectSelect(projectId: string) {
		selectedProjectId = projectId;
		await loadProjectAnalytics(projectId);
	}
</script>

<svelte:head>
	<title>AI-Orchestrated Project Management - Convergio</title>
	<meta name="description" content="CRM-style AI orchestration for project management with real-time collaboration" />
</svelte:head>

<!-- Projects Page -->
<div class="min-h-screen bg-surface-100 dark:bg-surface-900 space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-lg font-medium text-surface-900 dark:text-surface-100">🚀 AI-Orchestrated Project Management</h1>
			<p class="mt-1 text-sm text-surface-700 dark:text-surface-300">CRM-style journey tracking with intelligent agent orchestration and real-time collaboration</p>
		</div>
		
		<!-- Quick Actions -->
		<div class="flex items-center space-x-3">
			<button 
				on:click={() => createProject('New Project', 'Project description')}
				class="btn-primary flex items-center space-x-2"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				<span>New Project</span>
			</button>
		</div>
	</div>

	<!-- Main Content -->
	<div>
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
				<div class="text-red-600 text-lg font-medium mb-2">Error Loading Projects</div>
				<div class="text-red-500">{error}</div>
				<button 
					on:click={loadProjects}
					class="mt-4 btn-secondary"
				>
					Retry
				</button>
			</div>
		{:else}
			<!-- Project Selection -->
			{#if projects.length > 0}
				<div class="bg-surface-50 dark:bg-surface-950 border border-surface-300 dark:border-surface-700 rounded-lg overflow-hidden">
					<div class="p-4 border-b border-surface-300 dark:border-surface-700 bg-surface-100 dark:bg-surface-900">
						<h2 class="text-md font-medium text-surface-900 dark:text-surface-100">Select Project</h2>
					</div>
					
					<div class="p-4">
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
							{#each projects as project}
								<button
									on:click={() => handleProjectSelect(project.id)}
									class="text-left p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-md {selectedProjectId === project.id 
										? 'border-blue-500 bg-blue-50' 
										: 'border-surface-300 dark:border-surface-700 bg-surface-50 dark:bg-surface-950 hover:border-surface-400 dark:border-surface-600'}"
								>
									<div class="font-medium text-surface-900 dark:text-surface-100 mb-1">{project.title}</div>
									<div class="text-sm text-surface-600 dark:text-surface-400">{project.description || 'No description'}</div>
									<div class="mt-2">
										<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
											{project.status || 'Active'}
										</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
			{:else}
				<div class="bg-surface-50 dark:bg-surface-950 border border-surface-300 dark:border-surface-700 rounded-lg">
					<div class="text-center py-20">
						<div class="w-24 h-24 mx-auto mb-6 bg-surface-200 dark:bg-surface-800 rounded-full flex items-center justify-center">
							<svg class="w-12 h-12 text-surface-400 dark:text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
							</svg>
						</div>
						<h3 class="text-xl font-medium text-surface-900 dark:text-surface-100 mb-2">No Projects Yet</h3>
						<p class="text-surface-600 dark:text-surface-400 mb-6">Create your first project to get started with project management</p>
						<button 
							on:click={() => createProject('My First Project', 'Start managing your AI agent workflows')}
							class="btn-primary flex items-center space-x-2"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							<span>Create First Project</span>
						</button>
					</div>
				</div>
			{/if}

			<!-- View Selection -->
			{#if selectedProjectId && projects.length > 0}
				<div class="bg-surface-50 dark:bg-surface-950 border border-surface-300 dark:border-surface-700 rounded-lg overflow-hidden">
					<div class="p-4 border-b border-surface-300 dark:border-surface-700 bg-surface-100 dark:bg-surface-900">
						<div class="flex items-center justify-between">
							<h2 class="text-md font-medium text-surface-900 dark:text-surface-100">Project Views</h2>
							
							<!-- View Tabs -->
							<div class="flex bg-surface-200 dark:bg-surface-800 rounded-lg p-1">
								<button
									on:click={() => selectedView = 'orchestration'}
									class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'orchestration' 
										? 'bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 shadow-sm' 
										: 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:text-surface-100'}"
								>
									🚀 AI Orchestration
								</button>
								<button
									on:click={() => selectedView = 'kanban'}
									class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'kanban' 
										? 'bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 shadow-sm' 
										: 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:text-surface-100'}"
								>
									Kanban Board
								</button>
								<button
									on:click={() => selectedView = 'gantt'}
									class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'gantt' 
										? 'bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 shadow-sm' 
										: 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:text-surface-100'}"
								>
									Gantt Chart
								</button>
								<button
									on:click={() => selectedView = 'analytics'}
									class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'analytics' 
										? 'bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 shadow-sm' 
										: 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:text-surface-100'}"
								>
									Analytics
								</button>
								<button
									on:click={() => selectedView = 'ai_integration'}
									class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'ai_integration' 
										? 'bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 shadow-sm' 
										: 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:text-surface-100'}"
								>
									AI Integration
								</button>
							</div>
						</div>
					</div>

					<!-- View Content -->
					<div class="p-4">
						{#if selectedView === 'orchestration'}
							<PMOrchestrationDashboard projectId={selectedProjectId} />
						{:else if selectedView === 'kanban'}
							<ModernKanbanBoard projectId={selectedProjectId} />
						{:else if selectedView === 'gantt'}
							<ModernGanttChart projectId={selectedProjectId} />
						{:else if selectedView === 'analytics'}
							<ModernAnalyticsDashboard projectId={selectedProjectId} />
						{:else if selectedView === 'ai_integration'}
							<AIProjectIntegration projectId={selectedProjectId} />
						{/if}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	/* Custom scrollbar for better UX */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: transparent;
	}
	
	::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: #94a3b8;
	}
	
	/* Dark mode scrollbar */
	:global(.dark) ::-webkit-scrollbar-thumb {
		background: #475569;
	}
	
	:global(.dark) ::-webkit-scrollbar-thumb:hover {
		background: #64748b;
	}
</style>