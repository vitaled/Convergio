<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Button, Badge, Avatar } from './index';

	interface Notification {
		id: string;
		title: string;
		message: string;
		type: 'info' | 'success' | 'warning' | 'error';
		timestamp: Date;
		read: boolean;
		actions?: {
			label: string;
			action: string;
			variant?: 'primary' | 'secondary';
		}[];
		avatar?: string;
		icon?: string;
		href?: string;
	}

	interface $$Props {
		notifications: Notification[];
		unreadCount?: number;
		showAvatar?: boolean;
		maxHeight?: string;
		position?: 'left' | 'right' | 'center';
		loading?: boolean;
		emptyMessage?: string;
	}

	export let notifications: $$Props['notifications'];
	export let unreadCount: $$Props['unreadCount'] = 0;
	export let showAvatar: $$Props['showAvatar'] = true;
	export let maxHeight: $$Props['maxHeight'] = '400px';
	export let position: NonNullable<$$Props['position']> = 'right';
	export let loading: $$Props['loading'] = false;
	export let emptyMessage: $$Props['emptyMessage'] = 'No notifications';

	const dispatch = createEventDispatcher<{
		notificationClick: { notification: Notification };
		actionClick: { notification: Notification; action: string };
		markAsRead: { notification: Notification };
		markAllAsRead: void;
		clearAll: void;
	}>();

	let isOpen = false;
	let dropdownRef: HTMLElement;

	// Group notifications by date
	$: groupedNotifications = groupByDate(notifications);

	// Computed unread count
	$: computedUnreadCount = unreadCount || notifications.filter(n => !n.read).length;

	// Position classes
	$: positionClasses = {
		left: 'left-0',
		right: 'right-0',
		center: 'left-1/2 transform -translate-x-1/2'
	}[position];

	function groupByDate(notifs: Notification[]) {
		const groups: Record<string, Notification[]> = {};
		
		notifs.forEach(notification => {
			const date = new Date(notification.timestamp);
			const today = new Date();
			const yesterday = new Date(today);
			yesterday.setDate(yesterday.getDate() - 1);
			
			let groupKey: string;
			if (isSameDay(date, today)) {
				groupKey = 'Today';
			} else if (isSameDay(date, yesterday)) {
				groupKey = 'Yesterday';
			} else {
				groupKey = date.toLocaleDateString();
			}
			
			if (!groups[groupKey]) {
				groups[groupKey] = [];
			}
			groups[groupKey].push(notification);
		});
		
		return groups;
	}

	function isSameDay(date1: Date, date2: Date): boolean {
		return date1.toDateString() === date2.toDateString();
	}

	function formatTime(date: Date): string {
		const now = new Date();
		const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
		
		if (diffInMinutes < 1) return 'Just now';
		if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
		if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
		return date.toLocaleDateString();
	}

	function toggleDropdown() {
		isOpen = !isOpen;
	}

	function closeDropdown() {
		isOpen = false;
	}

	function handleNotificationClick(notification: Notification) {
		if (!notification.read) {
			dispatch('markAsRead', { notification });
		}
		
		if (notification.href) {
			window.location.href = notification.href;
		}
		
		dispatch('notificationClick', { notification });
	}

	function handleActionClick(notification: Notification, actionType: string) {
		dispatch('actionClick', { notification, action: actionType });
	}

	function handleMarkAllAsRead() {
		dispatch('markAllAsRead');
	}

	function handleClearAll() {
		dispatch('clearAll');
	}

	// Close dropdown when clicking outside
	function handleClickOutside(event: Event) {
		if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
			closeDropdown();
		}
	}

	$: if (isOpen) {
		document.addEventListener('click', handleClickOutside);
	} else {
		document.removeEventListener('click', handleClickOutside);
	}
</script>

<div class="notification-dropdown" bind:this={dropdownRef}>
	<!-- Trigger Button -->
	<Button
		variant="ghost"
		size="icon"
		on:click={toggleDropdown}
		aria-label="Notifications"
		aria-expanded={isOpen}
		class="relative"
	>
		<span class="icon-bell" aria-hidden="true"></span>
		{#if computedUnreadCount > 0}
			<Badge
				variant="error"
				size="sm"
				class="notification-badge"
			>
				{computedUnreadCount > 99 ? '99+' : computedUnreadCount}
			</Badge>
		{/if}
	</Button>

	<!-- Dropdown Menu -->
	{#if isOpen}
		<div class="dropdown-menu {positionClasses}" style="max-height: {maxHeight}">
			<!-- Header -->
			<div class="dropdown-header">
				<h3 class="header-title">Notifications</h3>
				<div class="header-actions">
					{#if computedUnreadCount > 0}
						<button
							type="button"
							class="header-action-btn"
							on:click={handleMarkAllAsRead}
						>
							Mark all read
						</button>
					{/if}
					{#if notifications.length > 0}
						<button
							type="button"
							class="header-action-btn"
							on:click={handleClearAll}
						>
							Clear all
						</button>
					{/if}
				</div>
			</div>

			<!-- Content -->
			<div class="dropdown-content">
				{#if loading}
					<!-- Loading State -->
					<div class="loading-state">
						<div class="loading-spinner"></div>
						<p class="loading-text">Loading notifications...</p>
					</div>
				{:else if notifications.length === 0}
					<!-- Empty State -->
					<div class="empty-state">
						<span class="icon-bell-slash empty-icon" aria-hidden="true"></span>
						<p class="empty-message">{emptyMessage}</p>
					</div>
				{:else}
					<!-- Notifications List -->
					{#each Object.entries(groupedNotifications) as [date, notifs] (date)}
						<div class="notification-group">
							<h4 class="group-date">{date}</h4>
							
							{#each notifs as notification (notification.id)}
								<div
									class="notification-item {!notification.read ? 'unread' : ''} type-{notification.type}"
									on:click={() => handleNotificationClick(notification)}
									on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleNotificationClick(notification)}
									role="button"
									tabindex="0"
								>
									<!-- Unread indicator -->
									{#if !notification.read}
										<div class="unread-indicator" aria-hidden="true"></div>
									{/if}

									<!-- Avatar or Icon -->
									<div class="notification-avatar">
										{#if showAvatar && notification.avatar}
											<Avatar src={notification.avatar} size="sm" />
										{:else if notification.icon}
											<div class="notification-icon type-{notification.type}">
												<span class="icon-{notification.icon}" aria-hidden="true"></span>
											</div>
										{:else}
											<div class="notification-icon type-{notification.type}">
												<span class="icon-{notification.type}" aria-hidden="true"></span>
											</div>
										{/if}
									</div>

									<!-- Content -->
									<div class="notification-content">
										<div class="notification-header">
											<h5 class="notification-title">{notification.title}</h5>
											<span class="notification-time">{formatTime(notification.timestamp)}</span>
										</div>
										
										<p class="notification-message">{notification.message}</p>

										<!-- Actions -->
										{#if notification.actions && notification.actions.length > 0}
											<div class="notification-actions">
												{#each notification.actions as action}
													<button
														type="button"
														class="action-btn"
														class:primary={action.variant === 'primary'}
														on:click|stopPropagation={() => handleActionClick(notification, action.action)}
													>
														{action.label}
													</button>
												{/each}
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{/each}
				{/if}
			</div>

			<!-- Footer -->
			{#if notifications.length > 0}
				<div class="dropdown-footer">
					<a href="/notifications" class="view-all-link">
						View all notifications
					</a>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.notification-dropdown {
		@apply relative;
	}

	.notification-badge {
		@apply absolute -top-1 -right-1 min-w-[1.25rem] h-5 flex items-center justify-center;
	}

	.dropdown-menu {
		@apply absolute top-full mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-50 overflow-hidden;
		box-shadow: var(--shadow-xl);
		animation: fadeInDown 0.2s ease-out;
	}

	.dropdown-header {
		@apply flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900;
	}

	.header-title {
		@apply text-sm font-semibold text-gray-900 dark:text-white;
		font-family: var(--font-primary);
	}

	.header-actions {
		@apply flex items-center gap-2;
	}

	.header-action-btn {
		@apply text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors duration-200;
		font-family: var(--font-primary);
	}

	.dropdown-content {
		@apply overflow-y-auto;
	}

	.loading-state,
	.empty-state {
		@apply flex flex-col items-center justify-center py-8 text-gray-500 dark:text-gray-400;
	}

	.loading-text,
	.empty-message {
		@apply text-sm mt-2;
		font-family: var(--font-primary);
	}

	.empty-icon {
		@apply w-8 h-8 mb-2;
	}

	.notification-group {
		@apply border-b border-gray-100 dark:border-gray-700 last:border-b-0;
	}

	.group-date {
		@apply px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 sticky top-0 z-10;
		font-family: var(--font-primary);
	}

	.notification-item {
		@apply relative flex items-start gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors duration-200 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700;
	}

	.notification-item.unread {
		@apply bg-primary-50 dark:bg-primary-900/20;
	}

	.unread-indicator {
		@apply absolute left-2 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-primary-600 rounded-full;
	}

	.notification-avatar {
		@apply flex-shrink-0;
	}

	.notification-icon {
		@apply w-8 h-8 rounded-full flex items-center justify-center;
	}

	.notification-icon.type-info {
		@apply bg-info-100 text-info-600 dark:bg-info-900/30 dark:text-info-400;
	}

	.notification-icon.type-success {
		@apply bg-success-100 text-success-600 dark:bg-success-900/30 dark:text-success-400;
	}

	.notification-icon.type-warning {
		@apply bg-warning-100 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400;
	}

	.notification-icon.type-error {
		@apply bg-error-100 text-error-600 dark:bg-error-900/30 dark:text-error-400;
	}

	.notification-content {
		@apply flex-1 min-w-0;
	}

	.notification-header {
		@apply flex items-start justify-between gap-2 mb-1;
	}

	.notification-title {
		@apply text-sm font-medium text-gray-900 dark:text-white truncate;
		font-family: var(--font-primary);
	}

	.notification-time {
		@apply text-xs text-gray-500 dark:text-gray-400 flex-shrink-0;
		font-family: var(--font-primary);
	}

	.notification-message {
		@apply text-sm text-gray-600 dark:text-gray-300 line-clamp-2;
		font-family: var(--font-primary);
	}

	.notification-actions {
		@apply flex items-center gap-2 mt-2;
	}

	.action-btn {
		@apply px-3 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors duration-200;
		font-family: var(--font-primary);
	}

	.action-btn.primary {
		@apply bg-primary-600 text-white hover:bg-primary-700;
	}

	.dropdown-footer {
		@apply px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900;
	}

	.view-all-link {
		@apply block text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-center transition-colors duration-200;
		font-family: var(--font-primary);
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.empty-icon {
		@apply w-8 h-8;
	}

	.icon-bell {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0' /%3e%3c/svg%3e");
	}

	.icon-bell-slash {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9.143 17.082a24.248 24.248 0 0 0 3.844.148m-3.844-.148a23.856 23.856 0 0 1-5.455-1.31 8.964 8.964 0 0 0 2.3-5.542m3.155 6.852a3 3 0 0 0 5.667 1.97m1.965-2.277L21 4.5m-4.5 0H9a9.009 9.009 0 0 0-8.96 8.047L21 4.5ZM3 12v.75a8.964 8.964 0 0 0 3.07 6.795L3 12Z' /%3e%3c/svg%3e");
	}

	.icon-info {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z' /%3e%3c/svg%3e");
	}

	.icon-success {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' /%3e%3c/svg%3e");
	}

	.icon-warning {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z' /%3e%3c/svg%3e");
	}

	.icon-error {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z' /%3e%3c/svg%3e");
	}

	@keyframes fadeInDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.dropdown-menu {
			@apply w-screen max-w-sm right-0;
		}
	}
</style>