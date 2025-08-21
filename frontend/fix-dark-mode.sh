#!/bin/bash

echo "🌙 Fixing Dark Mode Color Issues"
echo "================================"

# The problem: dark mode text is invisible because we're using wrong surface colors
# Fix: Update dark mode classes to use correct contrast

files=(
    "src/routes/(app)/+layout.svelte"
    "src/lib/components/ThemeToggle.svelte"
    "src/routes/(app)/agents/+page.svelte"
    "src/routes/(app)/pm/+page.svelte"
    "src/routes/(app)/dashboard/+page.svelte"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "🔧 Fixing: $file"
        
        # Fix main background and text combinations for readability
        # Dark mode should have light text on dark backgrounds
        sed -i '' 's/bg-surface-950 dark:bg-surface-50/bg-surface-50 dark:bg-surface-950/g' "$file"
        sed -i '' 's/text-surface-100 dark:text-surface-900/text-surface-900 dark:text-surface-100/g' "$file"
        sed -i '' 's/text-surface-200 dark:text-surface-800/text-surface-800 dark:text-surface-200/g' "$file"
        sed -i '' 's/text-surface-300 dark:text-surface-700/text-surface-700 dark:text-surface-300/g' "$file"
        sed -i '' 's/text-surface-400 dark:text-surface-600/text-surface-600 dark:text-surface-400/g' "$file"
        
        # Fix borders for proper contrast
        sed -i '' 's/border-surface-700 dark:border-surface-300/border-surface-300 dark:border-surface-700/g' "$file"
        sed -i '' 's/border-surface-600 dark:border-surface-400/border-surface-400 dark:border-surface-600/g' "$file"
        
        # Fix card/panel backgrounds
        sed -i '' 's/bg-surface-900 dark:bg-surface-100/bg-surface-100 dark:bg-surface-900/g' "$file"
        sed -i '' 's/bg-surface-800 dark:bg-surface-200/bg-surface-200 dark:bg-surface-800/g' "$file"
        
        echo "   ✅ Fixed"
    else
        echo "   ❌ File not found: $file"
    fi
done

echo ""
echo "✨ Dark mode contrast fixes completed!"
echo "Now text should be readable in both light and dark modes"