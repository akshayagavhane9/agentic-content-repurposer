from typing import Dict, Any, List, Optional
import re


# ---------------- Platform Configuration ---------------- #

PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = {
    "linkedin": {
        "min_words": 80,
        "max_words": 220,
    },
    "instagram": {
        "max_chars": 2200,   # IG caption hard limit
        "max_lines": 10,
    },
    "email": {
        "min_words": 40,
        "max_words": 160,
    },
}


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/newlines into single spaces; trim ends."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------------- Built-In Tools ---------------- #

def topic_research_tool(topic: str) -> Dict[str, Any]:
    """
    Simple topic helper used by the strategy / planning agent.

    This is intentionally lightweight but structured so it can be
    extended later (e.g., plugging in a real web search API).
    """
    cleaned = _normalize_whitespace(topic)
    if not cleaned:
        return {
            "topic": "",
            "keywords": [],
            "angles": [],
            "notes": "No topic provided."
        }

    words = [w.strip(".,!?").lower() for w in cleaned.split() if len(w) > 3]
    unique_words = sorted(set(words))

    return {
        "topic": cleaned,
        "keywords": unique_words[:8],
        "angles": [
            f"Practical tips about {w}" for w in unique_words[:3]
        ],
        "notes": "Heuristic topic breakdown based on user brief."
    }


def keyword_and_hook_mapper_tool(strategy_text: str) -> Dict[str, Any]:
    """
    Heuristic tool that extracts candidate keywords and hook phrases
    from the strategy text. Used by planning/styling agents.
    """
    cleaned = _normalize_whitespace(strategy_text)
    if not cleaned:
        return {
            "keywords": [],
            "hooks": [],
            "notes": "Empty strategy text; nothing to extract."
        }

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    first_sentence = sentences[0] if sentences else cleaned

    # Naive keyword extraction
    tokens = [t.strip(".,!?").lower() for t in cleaned.split()]
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "you", "your"}
    keywords = sorted({t for t in tokens if len(t) > 3 and t not in stopwords})

    # Hook ideas
    hooks: List[str] = []
    if "?" in first_sentence:
        hooks.append("Start with a question to draw the reader in.")
    if "story" in cleaned.lower():
        hooks.append("Open with a short story-based hook.")
    hooks.append("Use a concrete scenario your audience relates to.")
    hooks.append("Highlight a pain point in the first line.")

    return {
        "keywords": keywords[:10],
        "hooks": hooks[:4],
        "notes": "Heuristic mapper; can be swapped with a smarter tool later."
    }


def platform_formatting_tool(
    platform: str,
    text: str,
    hashtags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Platform-aware formatter that:
      - validates input
      - applies basic length constraints
      - prepares captions/hashtags where needed

    Returns a dict with at least 'formatted_text', and for Instagram:
      - 'caption'
      - 'hashtag_block'
    """
    platform = (platform or "").lower()
    raw_text = text or ""

    if platform not in PLATFORM_CONFIG:
        # Unknown platform: return safe fallback
        safe = _normalize_whitespace(raw_text)
        return {
            "platform": platform,
            "formatted_text": safe,
            "warning": "Unknown platform; no specific formatting applied."
        }

    # Empty text guard
    if not raw_text.strip():
        return {
            "platform": platform,
            "formatted_text": "[EMPTY CONTENT] No text was provided to format.",
            "warning": "Input text was empty."
        }

    formatted = raw_text.strip()

    # ---------------- LinkedIn formatting ---------------- #
    if platform == "linkedin":
        formatted = _normalize_whitespace(formatted)
        words = formatted.split()
        cfg = PLATFORM_CONFIG["linkedin"]
        min_w, max_w = cfg["min_words"], cfg["max_words"]

        length_warning = None
        if len(words) > max_w:
            formatted = " ".join(words[:max_w])
            length_warning = f"Trimmed LinkedIn post to {max_w} words."
        elif len(words) < min_w:
            length_warning = f"LinkedIn post is quite short ({len(words)} words)."

        return {
            "platform": "linkedin",
            "formatted_text": formatted,
            "length_warning": length_warning,
        }

    # ---------------- Instagram formatting ---------------- #
    if platform == "instagram":
        # Keep line breaks but ensure we don't exceed Instagram limits
        caption = raw_text.strip()
        cfg = PLATFORM_CONFIG["instagram"]

        # Rough line constraint
        lines = caption.splitlines()
        if len(lines) > cfg["max_lines"]:
            caption = "\n".join(lines[:cfg["max_lines"]])

        if len(caption) > cfg["max_chars"]:
            caption = caption[:cfg["max_chars"]]

        # Hashtags handling
        hashtags = hashtags or []
        cleaned_tags: List[str] = []
        for tag in hashtags:
            t = tag.strip()
            if not t:
                continue
            if not t.startswith("#"):
                t = "#" + t
            cleaned_tags.append(t)

        # Deduplicate while preserving order
        seen = set()
        deduped_tags = []
        for t in cleaned_tags:
            if t.lower() not in seen:
                seen.add(t.lower())
                deduped_tags.append(t)

        hashtag_block = " ".join(deduped_tags)

        full_text = caption
        if hashtag_block:
            full_text = f"{caption}\n\n{hashtag_block}"

        return {
            "platform": "instagram",
            "formatted_text": full_text,
            "caption": caption,
            "hashtag_block": hashtag_block,
        }

    # ---------------- Email formatting ---------------- #
    if platform == "email":
        formatted = _normalize_whitespace(formatted)
        words = formatted.split()
        cfg = PLATFORM_CONFIG["email"]
        min_w, max_w = cfg["min_words"], cfg["max_words"]

        length_warning = None
        if len(words) > max_w:
            formatted = " ".join(words[:max_w])
            length_warning = f"Trimmed email blurb to {max_w} words."
        elif len(words) < min_w:
            length_warning = f"Email blurb is quite short ({len(words)} words)."

        return {
            "platform": "email",
            "formatted_text": formatted,
            "length_warning": length_warning,
        }

    # Fallback (should not reach here because of platform check above)
    safe = _normalize_whitespace(raw_text)
    return {
        "platform": platform,
        "formatted_text": safe,
        "warning": "Reached fallback branch of formatter."
    }


# ---------------- Custom Tool: Quality & Reach Scorer ---------------- #

def quality_and_reach_scorer(
    platform: str,
    text: str,
    strategy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Heuristic quality scoring tool.

    Dimensions:
      - clarity
      - tone_match (currently heuristic, can be extended)
      - length_appropriateness (platform-aware)
      - hook_strength
      - cta_quality
      - hashtag_richness (instagram only)

    Returns:
      {
        'platform': 'linkedin',
        'score': 0.78,
        'dimensions': {...},
        'summary_feedback': 'Short explanation...'
      }
    """
    platform = (platform or "").lower()
    text = (text or "").strip()

    if not text:
        return {
            "platform": platform,
            "score": 0.0,
            "dimensions": {},
            "summary_feedback": "No text to evaluate."
        }

    # Remove excess whitespace for analysis
    normalized = _normalize_whitespace(text)
    words = normalized.split()
    word_count = len(words)

    # -------- Clarity (very simple heuristic) -------- #
    # If text is not fallback and sentence-like, assume decent clarity.
    clarity = 0.8
    if "[FALLBACK]" in text:
        clarity = 0.3
    elif len(words) < 15:
        clarity = 0.6  # very short → slightly less clear for deeper topics

    # -------- Tone match (placeholder heuristic) -------- #
    # Could be adapted in the future based on "strategy".
    tone_match = 0.8

    # -------- Length appropriateness (platform-aware) -------- #
    length_appropriateness = 0.8
    if platform in ("linkedin", "email"):
        cfg = PLATFORM_CONFIG.get(platform, {})
        min_w = cfg.get("min_words", 0)
        max_w = cfg.get("max_words", 10**9)
        if word_count < min_w:
            length_appropriateness = 0.5
        elif word_count > max_w:
            length_appropriateness = 0.6
        else:
            length_appropriateness = 0.9
    elif platform == "instagram":
        # IG captions: short but not too short
        if word_count < 10:
            length_appropriateness = 0.5
        elif word_count > 120:
            length_appropriateness = 0.6
        else:
            length_appropriateness = 0.9

    # -------- Hook strength -------- #
    # Check first line / sentence for question, strong phrase, or emoji.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    opening = sentences[0] if sentences else text
    hook_strength = 0.7
    if "?" in opening:
        hook_strength = 0.85
    if any(e in opening for e in ["🔥", "✨", "💪", "🚀"]):
        hook_strength = max(hook_strength, 0.8)
    if opening.lower().startswith(("imagine", "what if", "ever felt")):
        hook_strength = max(hook_strength, 0.85)

    # -------- CTA quality -------- #
    cta_phrases = [
        "share", "comment", "tell me", "let me know",
        "join", "reply", "dm me", "reach out", "connect"
    ]
    cta_quality = 0.6
    lower_text = text.lower()
    if any(p in lower_text for p in cta_phrases):
        cta_quality = 0.9

    # -------- Hashtag richness (instagram only) -------- #
    hashtag_richness = None
    if platform == "instagram":
        tags = re.findall(r"#\w+", text)
        if len(tags) == 0:
            hashtag_richness = 0.4
        elif 3 <= len(tags) <= 15:
            hashtag_richness = 0.9
        else:
            hashtag_richness = 0.7

    dimensions: Dict[str, Optional[float]] = {
        "clarity": clarity,
        "tone_match": tone_match,
        "length_appropriateness": length_appropriateness,
        "hook_strength": hook_strength,
        "cta_quality": cta_quality,
        "hashtag_richness": hashtag_richness,
    }

    # Compute final score as average of non-None dimensions
    numeric_values = [v for v in dimensions.values() if v is not None]
    final_score = sum(numeric_values) / len(numeric_values) if numeric_values else 0.0

    # -------- Summary feedback -------- #
    feedback_parts: List[str] = []
    if length_appropriateness < 0.7:
        feedback_parts.append("Adjust the length to better fit this platform.")
    if hook_strength < 0.75:
        feedback_parts.append("Consider a stronger opening line or hook.")
    if cta_quality < 0.75:
        feedback_parts.append("Add a clearer call-to-action.")
    if platform == "instagram" and hashtag_richness is not None and hashtag_richness < 0.7:
        feedback_parts.append("Add more relevant hashtags to increase reach.")

    if not feedback_parts:
        summary_feedback = "Overall, this content is well-structured for the platform."
    else:
        summary_feedback = " ".join(feedback_parts)

    return {
        "platform": platform,
        "score": round(final_score, 2),
        "dimensions": dimensions,
        "summary_feedback": summary_feedback,
    }
