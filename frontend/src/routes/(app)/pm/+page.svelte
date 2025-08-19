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
	let error = '';
	
	onMount(async () => {
		await loadProjects();
	});
	
	async function loadProjects() {
		loading = true;
		error = '';
		try {
			const response = await fetch('http://localhost:4000/api/v1/projects/engagements');
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
			const response = await fetch(`http://localhost:4000/api/v1/projects/engagements/${projectId}/details`);
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
			const response = await fetch('http://localhost:4000/api/v1/projects/engagements', {
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
	<title>Project Management - Convergio</title>
	<meta name="description" content="Manage your AI agent projects and workflows" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-indigo-900">
	<!-- Header Section -->
	<div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div class="flex items-center space-x-4">
					<div class="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg">
						<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
						</svg>
					</div>
					<div>
						<h1 class="text-3xl font-bold text-slate-900 dark:text-white">Project Management</h1>
						<p class="text-slate-600 dark:text-slate-400 mt-1">Manage AI agent projects and coordinate workflows</p>
					</div>
				</div>
				
				<!-- Quick Actions -->
				<div class="flex items-center space-x-3">
					<button 
						on:click={() => createProject('New Project', 'Project description')}
						class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-lg shadow-lg hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						New Project
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			</div>
		{:else if error}
			<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
				<div class="text-red-600 dark:text-red-400 text-lg font-medium mb-2">Error Loading Projects</div>
				<div class="text-red-500 dark:text-red-300">{error}</div>
				<button 
					on:click={loadProjects}
					class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
				>
					Retry
				</button>
			</div>
		{:else}
			<!-- Project Selection -->
			{#if projects.length > 0}
				<div class="mb-8">
					<div class="flex items-center space-x-4 mb-4">
						<h2 class="text-xl font-semibold text-slate-900 dark:text-white">Select Project</h2>
						<div class="flex-1"></div>
					</div>
					
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{#each projects as project}
							<button
								on:click={() => handleProjectSelect(project.id)}
								class="text-left p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-md {selectedProjectId === project.id 
									? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
									: 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600'}"
							>
								<div class="font-medium text-slate-900 dark:text-white mb-1">{project.title}</div>
								<div class="text-sm text-slate-600 dark:text-slate-400">{project.description || 'No description'}</div>
								<div class="mt-2">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
										{project.status || 'Active'}
									</span>
								</div>
							</button>
						{/each}
					</div>
				</div>
			{:else}
				<div class="text-center py-20">
					<div class="w-24 h-24 mx-auto mb-6 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
						<svg class="w-12 h-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
						</svg>
					</div>
					<h3 class="text-xl font-medium text-slate-900 dark:text-white mb-2">No Projects Yet</h3>
					<p class="text-slate-600 dark:text-slate-400 mb-6">Create your first project to get started with project management</p>
					<button 
						on:click={() => createProject('My First Project', 'Start managing your AI agent workflows')}
						class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium rounded-lg shadow-lg hover:from-blue-600 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						Create First Project
					</button>
				</div>
			{/if}

			<!-- View Selection -->
			{#if selectedProjectId && projects.length > 0}
				<div class="mb-8">
					<div class="flex items-center justify-between mb-6">
						<h2 class="text-2xl font-bold text-slate-900 dark:text-white">Project Views</h2>
						
						<!-- View Tabs -->
						<div class="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
							<button
								on:click={() => selectedView = 'kanban'}
								class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'kanban' 
									? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' 
									: 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}"
							>
								Kanban Board
							</button>
							<button
								on:click={() => selectedView = 'gantt'}
								class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'gantt' 
									? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' 
									: 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}"
							>
								Gantt Chart
							</button>
							<button
								on:click={() => selectedView = 'analytics'}
								class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'analytics' 
									? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' 
									: 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}"
							>
								Analytics
							</button>
							<button
								on:click={() => selectedView = 'ai_integration'}
								class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'ai_integration' 
									? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' 
									: 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'}"
							>
								AI Integration
							</button>
						</div>
					</div>

					<!-- View Content -->
					<div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
						{#if selectedView === 'kanban'}
							<ModernKanbanBoard />
						{:else if selectedView === 'gantt'}
							<ModernGanttChart />
						{:else if selectedView === 'analytics'}
							<ModernAnalyticsDashboard />
						{:else if selectedView === 'ai_integration'}
							<AIProjectIntegration />
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