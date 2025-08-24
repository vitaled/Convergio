<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface $$Props extends HTMLAttributes<HTMLDivElement> {
		variant?: 'default' | 'elevated' | 'flat';
		hoverable?: boolean;
		clickable?: boolean;
	}

	export let variant: NonNullable<$$Props['variant']> = 'default';
	export let hoverable: $$Props['hoverable'] = true;
	export let clickable: $$Props['clickable'] = false;

	// Compute CSS classes  
	$: variantClasses = {
		default: 'card',
		elevated: 'card-elevated', 
		flat: 'card-flat'
	};

	$: classes = [
		variantClasses[variant],
		hoverable && !clickable ? 'hover:shadow-md hover:-translate-y-1' : '',
		clickable ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1 active:scale-[0.98]' : '',
		'transition-all duration-200'
	].filter(Boolean).join(' ');
</script>

<div class={classes} {...$$restProps} on:click>
	{#if $$slots.header}
		<div class="card-header">
			<slot name="header" />
		</div>
	{/if}

	{#if $$slots.default || $$slots.content}
		<div class="card-content">
			<slot name="content">
				<slot />
			</slot>
		</div>
	{/if}

	{#if $$slots.footer}
		<div class="card-footer">
			<slot name="footer" />
		</div>
	{/if}
</div>