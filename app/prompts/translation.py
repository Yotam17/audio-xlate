"""
Translation-related prompts for subtitle translation.
"""

TRANSLATE_SRT_SYSTEM_PROMPT = """You are a subtitle translation assistant. Always return raw SRT content without any markdown formatting, code blocks, or JSON wrapping."""

TRANSLATE_SRT_USER_PROMPT_TEMPLATE = """Translate the following subtitles from {src_lang} to {tgt_lang}. Keep the timing and structure as close as possible.

{translation_notes_section}IMPORTANT: Return ONLY the translated SRT content. Do NOT wrap it in markdown code blocks (```), JSON, or any other formatting. Return the raw SRT text exactly as it should appear in the subtitle file.

To help match the narrator speed in {tgt_lang}, aim for approximately:
- {word_pct}% {word_pct_type} words than the original
- {syllable_pct}% {syl_pct_type} syllables than the original

These are soft goals. Do not compromise the natural flow or clarity of the translation just to meet them. Focus on:
- Preserving the original meaning and order of ideas
- Keeping the emotional tone and rhythm
- Ensuring the subtitle fits naturally within its time slot

{chunk}

Return the translated subtitles without any formatting wrappers:"""
