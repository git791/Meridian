import asyncio
from core.config import settings

DEMO_TRANSCRIPT = """
Alice: Good morning everyone. Let's start with the Q3 OKR review.
Bob: Sure. We've hit 80% of the engineering velocity target.
Alice: That's solid. What's blocking the remaining 20%?
Bob: Mostly the legacy API migration — it's taking longer than estimated.
Alice: Okay. Charlie, can you own the migration plan and have a draft by Friday?
Charlie: Yes, I'll have it done by Thursday to give a buffer.
Alice: Perfect. Let's also schedule a follow-up next week to review progress.
Bob: I'll send the calendar invite after this call.
Alice: Great. Any other blockers?
Charlie: We need design sign-off on the new onboarding screens.
Alice: Diana, can you prioritise that review by Wednesday?
Diana: Absolutely.
Alice: Perfect. That's everything. Thanks all.
"""


class TranscriptionAgent:
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.model = None

        if not demo_mode and settings.GCP_PROJECT:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                vertexai.init(project=settings.GCP_PROJECT, location=settings.VERTEX_LOCATION)
                # Use Gemini for transcription (multimodal)
                self.model = GenerativeModel("gemini-1.5-pro-001")
            except Exception:
                pass

    async def transcribe(self, audio_file: str) -> str:
        if self.demo_mode or not audio_file or not self.model:
            await asyncio.sleep(1.2)  # simulate processing
            return DEMO_TRANSCRIPT

        try:
            from vertexai.generative_models import GenerativeModel, Part

            with open(audio_file, "rb") as f:
                audio_bytes = f.read()

            audio_part = Part.from_data(data=audio_bytes, mime_type="audio/webm")
            response = self.model.generate_content([audio_part, "Transcribe this audio verbatim. Include speaker labels."])
            return response.text
        except Exception as e:
            # Fall back to demo transcript on error
            return DEMO_TRANSCRIPT + f"\n[Transcription error: {e}]"