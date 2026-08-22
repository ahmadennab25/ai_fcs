"""Small helper utilities shared across the core app."""
import json


def parse_json_output(raw: str) -> dict:
    """
    Safely parse JSON returned by an LLM.

    Language models sometimes wrap JSON in Markdown code fences
    (```json ... ```). This helper strips those fences before parsing so
    callers always receive a clean Python dict.
    """
    if isinstance(raw, dict):
        return raw

    text = (raw or "").strip()
    if text.startswith("```"):
        # Remove the opening fence (``` or ```json) and the trailing fence.
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip().strip("`").strip()

    return json.loads(text)
