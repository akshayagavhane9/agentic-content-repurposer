# src/agents.py

from __future__ import annotations

import os
import time
from typing import Optional, Any, List

from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------
# Environment & Client Setup
# -------------------------------

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment or .env file.")

client = OpenAI(api_key=API_KEY)

# You can change this to any valid OpenAI chat model
MODEL_NAME = "gpt-4o-mini"

# -------------------------------
# Safe Agent Execution Wrapper
# -------------------------------

def run_agent(agent: dict, prompt: str, temperature: float = 0.7) -> str:
    """
    Unified safe execution layer for ALL agents.

    Features:
    - Automatic retries (3 attempts)
    - Delay between retries
    - Fallback response if the model fails
    - Works for all specialized agents

    `agent` is a lightweight dict created by create_agent().
    Expected keys: "role", "system_prompt"
    """
    MAX_RETRIES = 3
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": agent["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )

            # IMPORTANT: with the new OpenAI client, message is an object, not a dict
            return response.choices[0].message.content.strip()

        except Exception as e:
            last_error = e
            print(f"[ERROR] Attempt {attempt}/{MAX_RETRIES} failed for {agent['role']}: {e}")
            time.sleep(1.0 * attempt)

    print(f"[FALLBACK] Agent '{agent['role']}' returning fallback text.")
    return f"[FALLBACK OUTPUT] Unable to generate content due to: {last_error}"


# -------------------------------
# Helper: Create Agent Objects
# -------------------------------

def create_agent(role: str, system_prompt: str, tools: Optional[List[Any]] = None) -> dict:
    """
    Lightweight structured agent object.

    We are not using CrewAI's Agent class directly here to avoid Pydantic validation
    issues and keep the implementation simple and assignment-focused.
    """
    return {
        "role": role,
        "system_prompt": system_prompt,
        "tools": tools or [],
        "memory": True,
    }


# -------------------------------
# AGENT DEFINITIONS
# -------------------------------

def create_controller_agent() -> dict:
    """
    Controller / Director Agent:
    Orchestrates the overall flow and decides the high-level plan.
    """
    return create_agent(
        role="Content Director",
        system_prompt=(
            "You are the Controller Agent who oversees a multi-agent content system. "
            "You do not generate final content yourself. Instead, you outline how the "
            "strategy, draft writer, platform stylists, and quality reviewer should "
            "work together, step-by-step."
        ),
    )


def create_brief_and_strategy_agent() -> dict:
    """
    Strategy Agent:
    Extracts target audience, tone, and key message points from the user brief.
    """
    return create_agent(
        role="Content Strategist",
        system_prompt=(
            "You are a Content Strategist. From a short brief, you identify the "
            "target audience, desired tone, and 3–5 key points that must be covered "
            "across all platforms."
        ),
    )


def create_master_draft_writer_agent() -> dict:
    """
    Master Draft Writer:
    Turns the brief + strategy into a neutral long-form base draft.
    """
    return create_agent(
        role="Master Draft Writer",
        system_prompt=(
            "You are the Master Draft Writer. Using the user brief and strategist notes, "
            "you write a clear, neutral, well-structured base draft (2–3 short paragraphs). "
            "Do not optimize for any specific platform; just focus on clarity and completeness."
        ),
    )


def create_platform_stylist_agent() -> dict:
    """
    Platform Stylist:
    Converts the base draft into platform-specific variants for
    LinkedIn, Instagram, and Email.
    """
    return create_agent(
        role="Platform Stylist",
        system_prompt=(
            "You are a Platform Stylist. You take a base draft and adapt it into "
            "platform-specific content:\n"
            "- LinkedIn: professional, multi-line post with a hook and CTA.\n"
            "- Instagram: short, emotive caption with emojis and hashtags.\n"
            "- Email: friendly, supportive blurb with a gentle CTA.\n"
            "Always respect the original message and tone from the brief."
        ),
    )


def create_quality_reviewer_agent() -> dict:
    """
    Quality Reviewer:
    Evaluates content and provides high-level feedback (though in this project,
    the heavy scoring is done by the custom quality_and_reach_scorer tool).
    """
    return create_agent(
        role="Quality Reviewer",
        system_prompt=(
            "You are a Quality Reviewer for multi-platform content. You focus on clarity, "
            "tone consistency, structure, CTA strength, and alignment with platform norms. "
            "You often collaborate with a separate scoring tool that computes numeric scores."
        ),
    )


# -------------------------------
# Public API
# -------------------------------

__all__ = [
    "run_agent",
    "create_controller_agent",
    "create_brief_and_strategy_agent",
    "create_master_draft_writer_agent",
    "create_platform_stylist_agent",
    "create_quality_reviewer_agent",
]
