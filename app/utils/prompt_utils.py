"""
Utility functions for managing and formatting prompts.
"""

from typing import Dict, Any
import importlib

def get_prompt(template_name: str, params: Dict[str, Any]) -> str:
    """
    Get a prompt template by name with parameters.
    
    Args:
        template_name: Name of the template to retrieve (e.g., "TRANSLATE_SRT")
        params: Dictionary of parameters to substitute in the template
    
    Returns:
        Formatted prompt string
    """
    if template_name == "TRANSLATE_SRT":
        from app.prompts.translation import TRANSLATE_SRT_USER_PROMPT_TEMPLATE
        
        src_lang = params.get("src_lang", "")
        tgt_lang = params.get("tgt_lang", "")
        word_pct = params.get("word_pct", 0)
        syllable_pct = params.get("syllable_pct", 0)
        word_pct_type = params.get("word_pct_type", "more")
        syl_pct_type = params.get("syl_pct_type", "more")
        chunk = params.get("chunk", "")
        translation_notes = params.get("translation_notes", "")
        
        # Format translation notes section
        translation_notes_section = ""
        if translation_notes:
            translation_notes_section = f"Translation notes: {translation_notes}\n\n"
        
        return TRANSLATE_SRT_USER_PROMPT_TEMPLATE.format(
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            word_pct=word_pct,
            syllable_pct=syllable_pct,
            word_pct_type=word_pct_type,
            syl_pct_type=syl_pct_type,
            chunk=chunk,
            translation_notes_section=translation_notes_section
        )
    
    else:
        raise ValueError(f"Unknown template name: {template_name}")

def get_system_prompt(prompt_name: str) -> str:
    """
    Get a system prompt by name.
    
    Args:
        prompt_name: Name of the system prompt to retrieve
    
    Returns:
        System prompt string
    """
    if prompt_name == "TRANSLATE_SRT":
        from app.prompts.translation import TRANSLATE_SRT_SYSTEM_PROMPT
        return TRANSLATE_SRT_SYSTEM_PROMPT
    
    else:
        raise ValueError(f"Unknown system prompt name: {prompt_name}")
