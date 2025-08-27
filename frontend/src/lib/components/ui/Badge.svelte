<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface $$Props extends HTMLAttributes<HTMLSpanElement> {
		variant?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray';
		size?: 'sm' | 'md' | 'lg';
		rounded?: boolean;
		dot?: boolean;
		removable?: boolean;
	}

	export let variant: NonNullable<$$Props['variant']> = 'primary';
	export let size: NonNullable<$$Props['size']> = 'md';
	export let rounded: $$Props['rounded'] = true;
	export let dot: $$Props['dot'] = false;
	export let removable: $$Props['removable'] = false;

	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		remove: void;
	}>();

	// Compute CSS classes
	$: variantClasses = {
		primary: 'badge-primary',
		success: 'badge-success',
		warning: 'badge-warning',
		error: 'badge-error',
		info: 'badge-info',
		gray: 'badge-gray'
	};

	$: sizeClasses = {
		sm: 'badge-sm',
		md: 'badge',
		lg: 'badge-lg'
	};

	$: classes = [
		sizeClasses[size],
		variantClasses[variant],
		!rounded ? 'rounded-md' : '', // Override rounded-full from base badge class
		dot ? 'pl-2' : ''
	].filter(Boolean).join(' ');

	function handleRemove() {
		dispatch('remove');
	}
</script>

<span class={classes} {...$$restProps}>
	{#if dot}
		<span class="badge-dot bg-current opacity-75 mr-1.5" aria-hidden="true"></span>
	{/if}
	
	<slot />
	
	{#if removable}
		<button
			type="button"
			class="badge-remove-btn ml-1 hover:bg-black/10 rounded-full p-0.5 transition-colors duration-200"
			on:click={handleRemove}
			aria-label="Remove badge"
		>
			<span class="icon-x w-3 h-3" aria-hidden="true"></span>
		</button>
	{/if}
</span>

<style>
	.badge-dot {
		@apply w-2 h-2 rounded-full inline-block;
	}

	.badge-remove-btn {
		@apply -mr-1 inline-flex items-center justify-center;
	}

	.dark .badge-remove-btn:hover {
		background-color: rgba(255, 255, 255, 0.1);
	}

	/* Icon styles */
	.icon-x {
		display: inline-block;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M6 18 18 6M6 6l12 12' /%3e%3c/svg%3e");
	}
</style>