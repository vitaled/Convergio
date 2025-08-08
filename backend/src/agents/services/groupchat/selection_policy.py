"""
Speaker Selection Policy
Chooses the next speaker based on message intent, registry hints, and mission phase.
"""

from typing import List, Dict

from autogen_agentchat.agents import AssistantAgent


def select_key_agents(all_agents: List[AssistantAgent]) -> List[AssistantAgent]:
    priority = {
        "ali_chief_of_staff",
        "diana_performance_dashboard",
        "domik_mckinsey_strategic_decision_maker",
        "socrates_first_principles_reasoning",
        "wanda_workflow_orchestrator",
        "xavier_coordination_patterns",
    }
    keys = [a for a in all_agents if a.name in priority]
    others = [a for a in all_agents if a.name not in priority][:5]
    return keys + others


def pick_next_speaker(message_text: str, participants: List[AssistantAgent]) -> AssistantAgent:
    text = (message_text or "").lower()
    by_name = {a.name: a for a in participants}
    if "budget" in text or "cost" in text or "finance" in text:
        return by_name.get("amy_cfo", participants[0])
    if "risk" in text or "security" in text or "compliance" in text:
        return by_name.get("luca_security_expert", participants[0])
    if "strategy" in text or "decision" in text or "plan" in text:
        return by_name.get("ali_chief_of_staff", participants[0])
    return participants[0]


def selection_rationale(message_text: str, participants: List[AssistantAgent]) -> Dict[str, str]:
    """Return simple rationale for audit/metrics."""
    text = (message_text or "").lower()
    if any(k in text for k in ["budget", "cost", "finance"]):
        return {"reason": "finance_keywords", "picked": "amy_cfo"}
    if any(k in text for k in ["risk", "security", "compliance"]):
        return {"reason": "security_keywords", "picked": "luca_security_expert"}
    if any(k in text for k in ["strategy", "decision", "plan"]):
        return {"reason": "strategy_keywords", "picked": "ali_chief_of_staff"}
    return {"reason": "default_first", "picked": participants[0].name if participants else "unknown"}


