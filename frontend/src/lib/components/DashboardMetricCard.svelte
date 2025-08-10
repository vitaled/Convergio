<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let title: string;
  export let value: string | number;
  export let change: number;
  export let changeType: 'increase' | 'decrease' | 'neutral' = 'neutral';
  export let icon: string;
  export let iconColor: string = 'text-blue-600';
  export let bgColor: string = 'bg-blue-50';
  export let valueColor: string = 'text-gray-900';
  export let changeColor: string = 'text-green-600';
  export let formatValue: (value: string | number) => string = (val) => String(val);
  export let showChange: boolean = true;
  export let loading: boolean = false;

  const dispatch = createEventDispatcher();

  $: changeIcon = changeType === 'increase' ? '/convergio_icons/up.svg' : 
                   changeType === 'decrease' ? '/convergio_icons/down.svg' : 
                   '/convergio_icons/minus.svg';
  
  $: changeTextColor = changeType === 'increase' ? 'text-green-600' : 
                       changeType === 'decrease' ? 'text-red-600' : 
                       'text-gray-600';

  function handleClick() {
    dispatch('click');
  }
</script>

<div 
  class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer {loading ? 'opacity-60' : ''}"
  on:click={handleClick}
>
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="rounded-lg {bgColor} p-2">
        <img src={icon} alt="" class="h-5 w-5 {iconColor}" />
      </div>
      <div>
        <p class="text-sm font-medium text-gray-600">{title}</p>
        <p class="text-2xl font-bold {valueColor}">
          {loading ? '...' : formatValue(value)}
        </p>
      </div>
    </div>
    
    {#if showChange && !loading}
      <div class="flex items-center space-x-1">
        <img src={changeIcon} alt="" class="h-3 w-3" />
        <span class="text-sm font-medium {changeTextColor}">
          {change > 0 ? '+' : ''}{change}%
        </span>
      </div>
    {/if}
  </div>
</div>
