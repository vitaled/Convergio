<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface $$Props extends HTMLAttributes<HTMLDivElement> {
		variant?: 'default' | 'elevated' | 'flat' | 'stats';
		padding?: 'none' | 'sm' | 'md' | 'lg';
		hoverable?: boolean;
		clickable?: boolean;
	}

	export let variant: NonNullable<$$Props['variant']> = 'default';
	export let padding: NonNullable<$$Props['padding']> = 'md';
	export let hoverable: $$Props['hoverable'] = true;
	export let clickable: $$Props['clickable'] = false;

	// Compute CSS classes
	$: variantClasses = {
		default: 'card',
		elevated: 'card-elevated',
		flat: 'card-flat',
		stats: 'card-stats'
	};

	$: paddingClasses = {
		none: '',
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	};

	$: classes = [
		variantClasses[variant],
		variant !== 'stats' ? paddingClasses[padding] : '', // stats card has its own padding
		hoverable && !clickable ? 'hover:shadow-md hover:-translate-y-1' : '',
		clickable ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1 active:scale-[0.98]' : '',
		'transition-all duration-200'
	].filter(Boolean).join(' ');
</script>

<div class={classes} {...$$restProps} on:click>
	<slot />
</div>

<!-- Card with separate sections -->
<div class="card-wrapper" style="display: none;">
	<!-- This is a template for structured cards -->
	<div class="card">
		<div class="card-header">
			<slot name="header" />
		</div>
		<div class="card-content">
			<slot name="content" />
		</div>
		<div class="card-footer">
			<slot name="footer" />
		</div>
	</div>
</div>