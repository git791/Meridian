def clean_json_response(text: str) -> str:
    """Removes markdown backticks from Gemini JSON responses."""
    return text.replace("```json", "").replace("```", "").strip()