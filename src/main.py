# src/main.py

from __future__ import annotations

import os
import csv
from datetime import datetime
from typing import Dict, Any, Optional

from .agents import (
    create_controller_agent,
    create_brief_and_strategy_agent,
    create_master_draft_writer_agent,
    create_platform_stylist_agent,
    create_quality_reviewer_agent,
    run_agent,
)
from .tools import quality_and_reach_scorer

# -------------------------------
# Configuration
# -------------------------------

REFINEMENT_THRESHOLD = 0.90  # scores below this trigger self-improvement

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVAL_DIR = os.path.join(REPO_ROOT, "evaluation")
EVAL_CSV_PATH = os.path.join(EVAL_DIR, "test_results.csv")


# -------------------------------
# Helpers: CSV / Evaluation
# -------------------------------

def ensure_eval_csv_exists() -> None:
    """Ensure evaluation/test_results.csv exists with a header."""
    os.makedirs(EVAL_DIR, exist_ok=True)
    if not os.path.exists(EVAL_CSV_PATH):
        with open(EVAL_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["test_case", "linkedin", "instagram", "email", "timestamp"])


def get_next_test_case_id() -> int:
    """Infer the next test_case id by reading the last row from CSV."""
    if not os.path.exists(EVAL_CSV_PATH):
        return 1
    try:
        with open(EVAL_CSV_PATH, "r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            if len(reader) <= 1:
                return 1
            last_row = reader[-1]
            last_id = int(last_row[0])
            return last_id + 1
    except Exception as e:
        print(f"[WARN] Failed to infer next test_case id from CSV: {e}")
        return 1


def append_test_result(test_case: int,
                       linkedin_score: Optional[float],
                       instagram_score: Optional[float],
                       email_score: Optional[float]) -> None:
    """Append a single row of scores to evaluation/test_results.csv."""
    ensure_eval_csv_exists()
    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(EVAL_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            test_case,
            f"{linkedin_score:.2f}" if linkedin_score is not None else "",
            f"{instagram_score:.2f}" if instagram_score is not None else "",
            f"{email_score:.2f}" if email_score is not None else "",
            timestamp,
        ])
    print(
        f"\n[SAVED] Test results appended to {EVAL_CSV_PATH} as test_case={test_case}\n"
    )


# -------------------------------
# Core pipeline
# -------------------------------

def parse_strategy(raw_text: str) -> Dict[str, Any]:
    """
    Very lightweight 'parser' for the strategy agent output.

    For this assignment, we don't need deep parsing – we just store
    the full text and some placeholder fields that the quality scorer
    can optionally use.
    """
    return {
        "raw": raw_text,
        "key_points": [],
        "audience": "early-career or general",
        "tone": "honest, practical, encouraging",
    }


def run_content_repurposer(user_brief: str) -> Dict[str, Any]:
    """
    Run the full agentic pipeline and return a run_state dictionary
    that tracks all intermediate and final outputs.
    """
    run_state: Dict[str, Any] = {
        "brief": user_brief,
        "controller_plan": None,
        "strategy": None,
        "base_draft": None,
        "linkedin": None,
        "instagram": None,
        "email": None,
        "scores": {},
        "refinements": {
            "linkedin": {"old": None, "new": None, "delta": 0.0},
            "instagram": {"old": None, "new": None, "delta": 0.0},
            "email": {"old": None, "new": None, "delta": 0.0},
        },
    }

    # ---------------------------
    # 1. Instantiate agents
    # ---------------------------
    controller = create_controller_agent()
    strategist = create_brief_and_strategy_agent()
    master_writer = create_master_draft_writer_agent()
    stylist = create_platform_stylist_agent()
    reviewer = create_quality_reviewer_agent()

    # ---------------------------
    # 2. Controller: high-level plan
    # ---------------------------
    controller_prompt = f"""
You are the Content Director orchestrating a multi-agent system.

User brief:
\"\"\"{user_brief}\"\"\"

Outline how our agents (Strategy, Draft Writer, Platform Stylist, Quality Reviewer)
should collaborate to turn this brief into LinkedIn, Instagram, and Email content.
Use numbered steps and keep it concise.
"""
    controller_plan = run_agent(controller, controller_prompt)
    run_state["controller_plan"] = controller_plan

    print("\n\n=== CONTROLLER PLAN (for logs/demo) ===")
    print(controller_plan.strip())
    print("\n")

    # ---------------------------
    # 3. Strategy Agent
    # ---------------------------
    strategist_prompt = f"""
You are a Content Strategist.

User brief:
\"\"\"{user_brief}\"\"\"

Summarize:
1) target audience,
2) desired tone,
3) 3–5 key message points to cover across all platforms.
"""
    strategy_raw = run_agent(strategist, strategist_prompt)
    try:
        strategy = parse_strategy(strategy_raw)
    except Exception as e:
        print(f"[WARN] Failed to parse strategy output, using default. Error: {e}")
        strategy = {
            "raw": strategy_raw,
            "key_points": [user_brief],
            "audience": "general",
            "tone": "neutral",
        }

    run_state["strategy"] = strategy

    # ---------------------------
    # 4. Master Draft Writer – base neutral draft
    # ---------------------------
    draft_prompt = f"""
You are the Master Draft Writer.

Based on the user brief and the strategist notes, write a neutral,
well-structured base draft (2–3 short paragraphs) on the topic.

User brief:
\"\"\"{user_brief}\"\"\"

Strategist notes:
\"\"\"{strategy_raw}\"\"\"
"""
    base_draft = run_agent(master_writer, draft_prompt)

    if not base_draft or base_draft.startswith("[FALLBACK"):
        print("[WARN] Base draft appears empty or fallback. Using user brief as base draft.")
        base_draft = f"This draft is based on the user brief:\n\n{user_brief}"

    run_state["base_draft"] = base_draft

    print("\n=== BASE DRAFT (neutral) ===")
    print(base_draft.strip())
    print("\n")

    # ---------------------------
    # 5. Platform Styling Agent – LinkedIn, Instagram, Email
    # ---------------------------

    # LinkedIn
    linkedin_prompt = f"""
You are a LinkedIn content specialist.

Using the base draft below, create a LinkedIn post:
- Professional but human tone
- 5–8 short lines
- Clear hook in the first 1–2 lines
- End with a question or call-to-action inviting comments

Base draft:
\"\"\"{base_draft}\"\"\"
"""
    linkedin_text = run_agent(stylist, linkedin_prompt)

    # Instagram
    instagram_prompt = f"""
You are an Instagram caption specialist.

Using the base draft below, write:
- A short, emotionally engaging caption
- Use emojis sparingly but effectively
- End with a question to encourage replies
- Then propose 10–15 relevant hashtags on new lines under [Hashtags]

Base draft:
\"\"\"{base_draft}\"\"\"
"""
    instagram_text = run_agent(stylist, instagram_prompt)

    # Email
    email_prompt = f"""
You are writing a short email-style blurb or newsletter snippet.

Using the base draft below:
- Write 3–6 sentences
- Supportive, clear, encouraging
- One clear, gentle call-to-action at the end

Base draft:
\"\"\"{base_draft}\"\"\"
"""
    email_text = run_agent(stylist, email_prompt)

    run_state["linkedin"] = linkedin_text
    run_state["instagram"] = instagram_text
    run_state["email"] = email_text

    print("=== LINKEDIN POST ===")
    print(linkedin_text.strip())
    print("\n")

    print("=== INSTAGRAM CAPTION ===")
    print(instagram_text.strip())
    print("\n")

    print("=== EMAIL BLURB ===")
    print(email_text.strip())
    print("\n")

    # ---------------------------
    # 6. Quality Reviewer & Custom Scoring Tool (with fallbacks)
    # ---------------------------

    scores: Dict[str, Any] = {}

    try:
        scores["linkedin"] = quality_and_reach_scorer("linkedin", linkedin_text, strategy=strategy)
    except Exception as e:
        print(f"[WARN] Quality scoring failed for LinkedIn: {e}")
        scores["linkedin"] = {
            "platform": "linkedin",
            "score": None,
            "summary_feedback": "Scoring failed.",
            "dimensions": {},
        }

    try:
        scores["instagram"] = quality_and_reach_scorer("instagram", instagram_text, strategy=strategy)
    except Exception as e:
        print(f"[WARN] Quality scoring failed for Instagram: {e}")
        scores["instagram"] = {
            "platform": "instagram",
            "score": None,
            "summary_feedback": "Scoring failed.",
            "dimensions": {},
        }

    try:
        scores["email"] = quality_and_reach_scorer("email", email_text, strategy=strategy)
    except Exception as e:
        print(f"[WARN] Quality scoring failed for Email: {e}")
        scores["email"] = {
            "platform": "email",
            "score": None,
            "summary_feedback": "Scoring failed.",
            "dimensions": {},
        }

    run_state["scores"] = scores

    print("=== QUALITY REPORT ===\n")
    for platform in ["linkedin", "instagram", "email"]:
        s = scores.get(platform) or {}
        print(f"[{platform.upper()}]")
        print(f"Score: {s.get('score')}")
        print(f"Summary: {s.get('summary_feedback')}")
        print()

    # ---------------------------
    # 7. Self-Improvement Engine (refinement loop)
    #    – focus on LinkedIn and Email where long-form matters most
    # ---------------------------

    refinements_made = []

    def maybe_refine(platform: str, original_text: str) -> str:
        record = run_state["refinements"][platform]
        base_score = scores[platform].get("score")

        if base_score is None or base_score >= REFINEMENT_THRESHOLD:
            # No refinement needed
            return original_text

        improvement_prompt = f"""
You are revising a {platform} post to improve its quality.

Original {platform} content:
\"\"\"{original_text}\"\"\"

Scoring feedback:
\"\"\"{scores[platform].get('summary_feedback')}\"\"\"

Goal:
- Keep the same main message
- Stronger hook in the first line
- Clearer call-to-action
- Keep length reasonable for {platform}

Rewrite the content accordingly.
"""
        improved = run_agent(stylist, improvement_prompt)
        if not improved or improved.startswith("[FALLBACK"):
            print(f"[WARN] Refinement for {platform} resulted in fallback/empty text. Keeping original.")
            return original_text

        try:
            new_score = quality_and_reach_scorer(platform, improved, strategy=strategy)
            old = base_score
            new = new_score.get("score", old)
            delta = (new - old) if (old is not None and new is not None) else 0.0

            scores[platform] = new_score
            record["old"] = old
            record["new"] = new
            record["delta"] = delta

            refinements_made.append(platform)
            return improved
        except Exception as e:
            print(f"[WARN] Failed to re-score improved {platform} content: {e}")
            return original_text

    # Apply refinement to LinkedIn and Email (Instagram is usually already strong)
    run_state["linkedin"] = maybe_refine("linkedin", run_state["linkedin"])
    run_state["email"] = maybe_refine("email", run_state["email"])

    if refinements_made:
        print("=== SELF-IMPROVEMENT REFINEMENTS ===")
        for platform in refinements_made:
            r = run_state["refinements"][platform]
            if r["old"] is not None and r["new"] is not None:
                print(
                    f"[REFINEMENT] {platform.capitalize()} improved from "
                    f"{r['old']:.2f} \u2192 {r['new']:.2f} (\u0394={r['delta']:.2f})."
                )
        print("====================================\n")

    return run_state


# -------------------------------
# CLI entrypoint
# -------------------------------

def main() -> None:
    print("=== Agentic Content Repurposer ===")
    print("This will take a single brief and create LinkedIn, Instagram, and Email content.\n")

    user_brief = input("Enter your content brief (1–3 sentences about your idea, audience, and tone):\n> ").strip()
    if not user_brief:
        print("No brief provided. Exiting.")
        return

    # Run pipeline
    run_state = run_content_repurposer(user_brief)

    # Persist evaluation row
    linkedin_score = (run_state["scores"].get("linkedin") or {}).get("score")
    instagram_score = (run_state["scores"].get("instagram") or {}).get("score")
    email_score = (run_state["scores"].get("email") or {}).get("score")

    test_case_id = get_next_test_case_id()
    append_test_result(test_case_id, linkedin_score, instagram_score, email_score)


if __name__ == "__main__":
    main()
