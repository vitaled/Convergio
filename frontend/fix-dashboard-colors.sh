#!/bin/bash

echo "🎨 Fixing Dashboard Components Hardcoded Colors"
echo "=============================================="

# Dashboard components to fix
files=(
    "src/lib/components/dashboard/WorkflowsOverview.svelte"
    "src/lib/components/dashboard/ProjectsOverview.svelte"
    "src/lib/components/dashboard/WorkflowEditor.svelte" 
    "src/lib/components/dashboard/TalentsOverview.svelte"
    "src/lib/components/dashboard/AgentsOverview.svelte"
    "src/lib/components/dashboard/FeedbackOverview.svelte"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "🔧 Fixing: $file"
        
        # Gray borders
        sed -i '' 's/border-gray-100/border-surface-700 dark:border-surface-300/g' "$file"
        sed -i '' 's/border-gray-200/border-surface-600 dark:border-surface-400/g' "$file"
        
        # Gray backgrounds 
        sed -i '' 's/bg-gray-600/bg-surface-600 dark:bg-surface-400/g' "$file"
        sed -i '' 's/bg-gray-700/bg-surface-700 dark:bg-surface-300/g' "$file"
        sed -i '' 's/bg-gray-800/bg-surface-800 dark:bg-surface-200/g' "$file"
        sed -i '' 's/bg-gray-900/bg-surface-900 dark:bg-surface-100/g' "$file"
        
        # Gray text
        sed -i '' 's/text-gray-400/text-surface-400 dark:text-surface-600/g' "$file"
        sed -i '' 's/text-gray-500/text-surface-500 dark:text-surface-500/g' "$file"
        
        # Hover states
        sed -i '' 's/hover:bg-gray-700/hover:bg-surface-700 dark:hover:bg-surface-300/g' "$file"
        sed -i '' 's/hover:text-surface-400 dark:text-surface-600/hover:text-surface-300 dark:hover:text-surface-700/g' "$file"
        
        echo "   ✅ Fixed"
    else
        echo "   ❌ File not found: $file"
    fi
done

echo ""
echo "✨ Dashboard color fixes completed!"