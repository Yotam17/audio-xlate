# app/utils/gpt_utils.py
"""
This file has been refactored. Logic functions have been moved to app/logic/translation_logic.py
Utility functions have been moved to app/utils/text_utils.py, app/utils/srt_utils.py, and app/utils/prompt_utils.py

For translation logic, import from app.logic.translation_logic
For text utilities, import from app.utils.text_utils
For time utilities, import from app.utils.srt_utils
For prompt utilities, import from app.utils.prompt_utils
"""

# This file is kept for backward compatibility but is deprecated
# Please update imports to use the new structure

# Re-export get_prompt for backward compatibility
from app.utils.prompt_utils import get_prompt, get_system_prompt

__all__ = ['get_prompt', 'get_system_prompt']
