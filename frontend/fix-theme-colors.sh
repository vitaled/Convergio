#!/usr/bin/env bash
# 🎨 Script per correzione automatica colori hardcoded nel sistema temi

set -euo pipefail

echo "🎨 Convergio Theme Colors Fix Script"
echo "======================================"

# Directory di lavoro
FRONTEND_DIR="/Users/roberdan/GitHub/convergio/frontend/src"

# Backup
echo "📁 Creating backup..."
cp -r "$FRONTEND_DIR" "${FRONTEND_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

# Contatori
declare -i total_replacements=0

# Funzione per sostituzioni con conteggio
replace_and_count() {
    local pattern="$1"
    local replacement="$2"
    local description="$3"
    
    echo "🔧 Fixing: $description"
    local count=$(find "$FRONTEND_DIR" -name "*.svelte" -exec sed -i '' "s/$pattern/$replacement/g" {} \; -exec grep -l "$replacement" {} \; | wc -l)
    echo "   ✅ Replaced $count instances"
    total_replacements=$((total_replacements + count))
}

echo "🚀 Starting automated color replacements..."

# 1. Sfondi principali
replace_and_count "bg-white" "bg-surface-950 dark:bg-surface-50" "White backgrounds"
replace_and_count "bg-gray-50" "bg-surface-900 dark:bg-surface-100" "Light gray backgrounds"
replace_and_count "bg-gray-100" "bg-surface-800 dark:bg-surface-200" "Gray 100 backgrounds"
replace_and_count "bg-gray-200" "bg-surface-700 dark:bg-surface-300" "Gray 200 backgrounds"
replace_and_count "bg-gray-300" "bg-surface-600 dark:bg-surface-400" "Gray 300 backgrounds"

# 2. Testi principali
replace_and_count "text-white" "text-surface-950 dark:text-surface-50" "White text"
replace_and_count "text-gray-900" "text-surface-100 dark:text-surface-900" "Dark text"
replace_and_count "text-gray-800" "text-surface-200 dark:text-surface-800" "Gray 800 text"
replace_and_count "text-gray-700" "text-surface-300 dark:text-surface-700" "Gray 700 text"
replace_and_count "text-gray-600" "text-surface-400 dark:text-surface-600" "Gray 600 text"
replace_and_count "text-gray-500" "text-surface-500 dark:text-surface-500" "Gray 500 text"

# 3. Bordi
replace_and_count "border-white" "border-surface-950 dark:border-surface-50" "White borders"
replace_and_count "border-gray-200" "border-surface-700 dark:border-surface-300" "Gray 200 borders"
replace_and_count "border-gray-300" "border-surface-600 dark:border-surface-400" "Gray 300 borders"

# 4. Hover states
replace_and_count "hover:bg-gray-50" "hover:bg-surface-800 dark:hover:bg-surface-200" "Hover gray 50"
replace_and_count "hover:bg-gray-100" "hover:bg-surface-700 dark:hover:bg-surface-300" "Hover gray 100"
replace_and_count "hover:text-gray-900" "hover:text-surface-100 dark:hover:text-surface-900" "Hover dark text"

# 5. Focus states  
replace_and_count "focus:bg-gray-50" "focus:bg-surface-800 dark:focus:bg-surface-200" "Focus gray 50"
replace_and_count "focus:ring-gray-500" "focus:ring-primary-500" "Focus ring gray"

echo ""
echo "✨ Theme color fixes completed!"
echo "📊 Total replacements made: $total_replacements"
echo ""
echo "🔍 Files with remaining hardcoded colors:"
find "$FRONTEND_DIR" -name "*.svelte" -exec grep -l "bg-gray-\|text-gray-\|border-gray-" {} \; | head -10

echo ""
echo "🎯 Next steps:"
echo "1. Review the changes manually"
echo "2. Test the theme toggle functionality"
echo "3. Fix any remaining edge cases"
echo "4. Update Gantt and Kanban components manually"

echo ""
echo "💾 Backup created at: ${FRONTEND_DIR}_backup_$(date +%Y%m%d_%H%M%S)"