"""
GroupChat Setup
Create SelectorGroupChat with settings-driven parameters.
"""

from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import List

from autogen_agentchat.agents import AssistantAgent


def create_groupchat(
    participants: List[AssistantAgent],
    model_client: OpenAIChatCompletionClient,
    max_turns: int,
) -> SelectorGroupChat:
    return SelectorGroupChat(
        participants=participants,
        model_client=model_client,
        allow_repeated_speaker=False,
        max_turns=max_turns,
    )


