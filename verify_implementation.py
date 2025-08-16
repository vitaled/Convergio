#!/usr/bin/env python3
"""
Verification Script for Convergio Implementation
Checks all components from Report13Ago.md and ToDoWorkflowPlanAug14.md
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    return Path(filepath).exists()

def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists"""
    return Path(dirpath).is_dir()

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{title.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def print_status(item: str, status: bool, details: str = ""):
    """Print status of a check"""
    symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    status_text = f"{GREEN}OK{RESET}" if status else f"{RED}MISSING{RESET}"
    print(f"  {symbol} {item}: {status_text}")
    if details:
        print(f"    {YELLOW}{details}{RESET}")

def check_wave1_decision_engine() -> Tuple[int, int]:
    """Check Wave 1: Decision Engine + Orchestrator v2"""
    print_header("Wave 1: Decision Engine + Orchestrator v2")
    
    checks = [
        ("Decision Engine", "backend/src/agents/services/decision_engine.py"),
        ("Orchestrator v2", "backend/src/agents/services/autogen_groupchat_orchestrator.py"),
        ("Tool Executor", "backend/src/agents/services/groupchat/tool_executor.py"),
        ("Config with flags", "backend/src/agents/utils/config.py"),
        ("Cost Tracker", "backend/src/agents/services/cost_tracker.py"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave2_per_turn_rag() -> Tuple[int, int]:
    """Check Wave 2: Per-Turn RAG + Shared Context"""
    print_header("Wave 2: Per-Turn RAG + Shared Context")
    
    checks = [
        ("Per-Turn RAG", "backend/src/agents/services/groupchat/per_turn_rag.py"),
        ("Conflict Detector", "backend/src/agents/services/groupchat/conflict_detector.py"),
        ("GroupChat Setup", "backend/src/agents/services/groupchat/setup.py"),
        ("RAG Test", "tests/integration/test_per_turn_rag.py"),
        ("Conflict Test", "tests/integration/test_conflict_resolution.py"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave3_frontend_ops() -> Tuple[int, int]:
    """Check Wave 3: Frontend Operational UX"""
    print_header("Wave 3: Frontend Operational UX")
    
    checks = [
        ("Telemetry API", "backend/src/api/telemetry.py"),
        ("Telemetry Service", "backend/src/agents/services/observability/telemetry_api.py"),
        ("Timeline Component", "frontend/src/lib/components/Timeline.svelte"),
        ("RunPanel Component", "frontend/src/lib/components/RunPanel.svelte"),
        ("Telemetry Store", "frontend/src/lib/stores/telemetry.ts"),
        ("Operational UX Page", "frontend/src/routes/(app)/operational-ux/+page.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave4_governance() -> Tuple[int, int]:
    """Check Wave 4: Governance, Safety, Ops"""
    print_header("Wave 4: Governance, Safety, Ops")
    
    checks = [
        ("Rate Limiting", "backend/src/core/rate_limiting.py"),
        ("SLO Dashboard", "backend/src/agents/services/observability/slo_dashboard.py"),
        ("Runbook System", "backend/src/agents/services/observability/runbook.py"),
        ("Governance API", "backend/src/api/governance.py"),
        ("Security Guardian", "backend/src/agents/security/ai_security_guardian.py"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave5_graphflow() -> Tuple[int, int]:
    """Check Wave 5: AutoGen Workflow Generator (GraphFlow)"""
    print_header("Wave 5: AutoGen Workflow Generator (GraphFlow)")
    
    checks = [
        ("GraphFlow Generator", "backend/src/agents/services/graphflow/generator.py"),
        ("GraphFlow Orchestrator", "backend/src/agents/services/graphflow_orchestrator.py"),
        ("Workflows API", "backend/src/api/workflows.py"),
        ("Workflow Editor UI", "frontend/src/lib/components/dashboard/WorkflowEditor.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave6_agent_lifecycle() -> Tuple[int, int]:
    """Check Wave 6: Agent Lifecycle & Scale"""
    print_header("Wave 6: Agent Lifecycle & Scale")
    
    checks = [
        ("Agent Loader", "backend/src/agents/services/agent_loader.py"),
        ("Agent Definitions", "backend/src/agents/definitions"),
        ("Agent Management API", "backend/src/api/agent_management.py"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        if filepath.endswith("definitions"):
            exists = check_directory_exists(filepath)
        else:
            exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave7_pm_intelligence() -> Tuple[int, int]:
    """Check Wave 7: Frontend PM & Intelligence"""
    print_header("Wave 7: Frontend PM & Intelligence")
    
    checks = [
        ("Project Model", "backend/src/models/project.py"),
        ("Kanban Board", "frontend/src/lib/components/KanbanBoard.svelte"),
        ("Gantt Chart", "frontend/src/lib/components/GanttChart.svelte"),
        ("Calendar View", "frontend/src/lib/components/CalendarView.svelte"),
        ("Resource Board", "frontend/src/lib/components/ResourceBoard.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave8_insight_engine() -> Tuple[int, int]:
    """Check Wave 8: Ali Proattivo & Insight Engine"""
    print_header("Wave 8: Ali Proattivo & Insight Engine")
    
    checks = [
        ("Event Bus", "backend/src/agents/services/event_bus.py"),
        ("Insight Engine", "backend/src/agents/services/insight_engine.py"),
        ("Proactive Actions", "backend/src/agents/services/proactive_actions.py"),
        ("Ali Coach Panel", "frontend/src/lib/components/AliCoachPanel.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave9_custom_fields() -> Tuple[int, int]:
    """Check Wave 9: Modello Dati Personalizzabile"""
    print_header("Wave 9: Custom Fields & Templates")
    
    checks = [
        ("Custom Fields", "backend/src/models/custom_field.py"),
        ("Template Library", "backend/src/services/template_library.py"),
        ("Templates API", "backend/src/api/templates.py"),
        ("Form Renderer", "frontend/src/lib/components/CustomFormRenderer.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_wave10_multi_tenancy() -> Tuple[int, int]:
    """Check Wave 10: SaaS Multi-tenancy & Billing"""
    print_header("Wave 10: SaaS Multi-tenancy & Billing")
    
    checks = [
        ("Tenant Model", "backend/src/models/tenant.py"),
        ("Billing Service", "backend/src/services/billing.py"),
        ("Tenant Dashboard", "frontend/src/routes/(app)/admin/tenant-dashboard/+page.svelte"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def check_additional_components() -> Tuple[int, int]:
    """Check Additional Components"""
    print_header("Additional Components")
    
    checks = [
        ("M3 Scenario Tests", "tests/integration/test_scenarios/golden_scenarios.py"),
        ("Scenario Fixtures", "tests/integration/fixtures/scenarios.yaml"),
        ("Export Service", "backend/src/services/export_service.py"),
        ("Unified Orchestrator", "backend/src/agents/orchestrators/unified.py"),
        ("Web Tools", "backend/src/agents/tools/web_search_tool.py"),
        ("Database Tools", "backend/src/agents/tools/database_tools.py"),
        ("Vector Tools", "backend/src/agents/tools/vector_search_tool.py"),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, filepath in checks:
        exists = check_file_exists(filepath)
        print_status(name, exists, filepath)
        if exists:
            passed += 1
    
    return passed, total

def main():
    """Main verification function"""
    print(f"\n{BOLD}{BLUE}Convergio Implementation Verification{RESET}")
    print(f"{YELLOW}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{YELLOW}Checking Report13Ago.md and ToDoWorkflowPlanAug14.md requirements...{RESET}")
    
    total_passed = 0
    total_checks = 0
    
    # Run all checks
    checks = [
        check_wave1_decision_engine(),
        check_wave2_per_turn_rag(),
        check_wave3_frontend_ops(),
        check_wave4_governance(),
        check_wave5_graphflow(),
        check_wave6_agent_lifecycle(),
        check_wave7_pm_intelligence(),
        check_wave8_insight_engine(),
        check_wave9_custom_fields(),
        check_wave10_multi_tenancy(),
        check_additional_components(),
    ]
    
    for passed, total in checks:
        total_passed += passed
        total_checks += total
    
    # Print summary
    print_header("SUMMARY")
    
    percentage = (total_passed / total_checks * 100) if total_checks > 0 else 0
    
    if percentage == 100:
        color = GREEN
        status = "ALL CHECKS PASSED!"
    elif percentage >= 80:
        color = YELLOW
        status = "MOSTLY COMPLETE"
    else:
        color = RED
        status = "INCOMPLETE"
    
    print(f"{BOLD}Total Checks:{RESET} {total_checks}")
    print(f"{BOLD}Passed:{RESET} {GREEN}{total_passed}{RESET}")
    print(f"{BOLD}Failed:{RESET} {RED}{total_checks - total_passed}{RESET}")
    print(f"{BOLD}Completion:{RESET} {color}{percentage:.1f}%{RESET}")
    print(f"\n{BOLD}Status:{RESET} {color}{status}{RESET}")
    
    # List missing components
    if total_passed < total_checks:
        print(f"\n{YELLOW}Note: Some components may be in different locations or renamed.{RESET}")
        print(f"{YELLOW}Please verify manually if needed.{RESET}")
    
    return percentage == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)