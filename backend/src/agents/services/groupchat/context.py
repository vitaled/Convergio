"""
Message Context Utilities
Build enhanced messages with system, business, and user context.
"""

from typing import Optional, Dict
from datetime import datetime


def _get_system_context(settings) -> str:
    return (
        "Convergio.io Business Context:\n"
        f"- Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- Environment: {settings.environment}\n"
        f"- Available agents: {getattr(settings, 'expected_agents_count', 'N/A')} specialized business agents\n"
        "- Focus: Strategic business operations, talent management, and process optimization"
    )


def enhance_message_with_context(
    *,
    settings,
    message: str,
    context: Optional[Dict[str, any]],
) -> str:
    enhanced_message = message

    if context:
        if "agent_name" in context and context["agent_name"]:
            selected_agent = context["agent_name"]
            selected_role = context.get("agent_role", "Specialist")
            enhanced_message = (
                f"DIRECT REQUEST to {selected_agent} ({selected_role}):\n\n"
                f"{message}\n\n"
                f"Note: User has specifically selected {selected_agent} to handle this request. "
                f"Please ensure {selected_agent} takes the lead in responding."
            )

        if "business_context" in context:
            enhanced_message = f"Business Context: {context['business_context']}\n\n{enhanced_message}"

        if "user_preferences" in context:
            enhanced_message = f"{enhanced_message}\n\nUser Preferences: {context['user_preferences']}"

    system_context = _get_system_context(settings)
    enhanced_message = f"System Context: {system_context}\n\n{enhanced_message}"

    return enhanced_message


