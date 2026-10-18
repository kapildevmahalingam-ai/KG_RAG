"""Rule-based input and output guardrails ensuring agriculture relevance."""
from __future__ import annotations

# A much more polite and meaningful refusal message
SAFE_REFUSAL = (
    "I am the Tamil Nadu Agriculture Schemes Assistant, designed specifically to "
    "help you with agricultural schemes, subsidies, and welfare benefits in Tamil Nadu "
    "(such as seed distribution, crop insurance, and mechanisation grants). "
    "I'm unable to answer general programming or non-agricultural questions. "
    "How can I assist you with Tamil Nadu agriculture schemes today? 🌾"
)


def check_input(question: str) -> tuple[bool, str]:
  if not question or not question.strip():
    return False, "Please enter a valid question regarding TN Agriculture Schemes."
  if len(question) > 1000:
    return (
        False,
        "Your question is too long. Please keep it under 1000 characters.",
    )

  # Check domain relevance (Agriculture/Scheme keywords)
  keywords = [
      "scheme",
      "subsidy",
      "agri",
      "farmer",
      "crop",
      "loan",
      "tamil",
      "nadu",
      "grant",
      "budget",
      "market",
      "pension",
      "insurance",
      "horticulture",
      "engineering",
      "seeds",
  ]
  if not any(kw in question.lower() for kw in keywords):
    return False, SAFE_REFUSAL

  return True, ""


def check_output(text: str) -> tuple[bool, str]:
  if not text or not text.strip():
    return False, SAFE_REFUSAL
  return True, text