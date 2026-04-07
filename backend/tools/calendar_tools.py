def format_slot_for_display(slot: dict) -> str:
    """Formats an ISO slot for human-readable output."""
    start = slot.get("start", "").split("T")[-1][:5]
    end = slot.get("end", "").split("T")[-1][:5]
    return f"{start} to {end}"