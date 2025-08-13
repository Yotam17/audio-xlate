# Prompts Directory

This directory contains all AI model prompts used throughout the application. Prompts are organized by functionality and separated into system prompts and user prompt templates.

## Structure

- **`__init__.py`** - Package initialization
- **`translation.py`** - Translation-related prompts
- **`README.md`** - This file

## Adding New Prompts

### 1. Create a new prompt file

Create a new file in the `app/prompts/` directory, for example `app/prompts/summarization.py`:

```python
"""
Summarization-related prompts.
"""

SUMMARIZE_TEXT_SYSTEM_PROMPT = """You are a text summarization assistant. Create concise, accurate summaries."""

SUMMARIZE_TEXT_USER_PROMPT_TEMPLATE = """Please summarize the following text in {max_words} words or less:

{text}

Focus on the main points and key information."""
```

### 2. Update prompt_utils.py

Add the new prompt to `app/utils/prompt_utils.py`:

```python
def get_prompt(template_name: str, params: Dict[str, Any]) -> str:
    # ... existing code ...
    
    if template_name == "SUMMARIZE_TEXT":
        from app.prompts.summarization import SUMMARIZE_TEXT_USER_PROMPT_TEMPLATE
        
        max_words = params.get("max_words", 100)
        text = params.get("text", "")
        
        return SUMMARIZE_TEXT_USER_PROMPT_TEMPLATE.format(
            max_words=max_words,
            text=text
        )
    
    # ... rest of function ...

def get_system_prompt(prompt_name: str) -> str:
    # ... existing code ...
    
    if prompt_name == "SUMMARIZE_TEXT":
        from app.prompts.summarization import SUMMARIZE_TEXT_SYSTEM_PROMPT
        return SUMMARIZE_TEXT_SYSTEM_PROMPT
    
    # ... rest of function ...
```

### 3. Use the prompt in your code

```python
from app.utils.prompt_utils import get_prompt, get_system_prompt

# Get the user prompt
user_prompt = get_prompt("SUMMARIZE_TEXT", {
    "max_words": 50,
    "text": "Your text here..."
})

# Get the system prompt
system_prompt = get_system_prompt("SUMMARIZE_TEXT")

# Use with OpenAI API
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.4,
)
```

## Best Practices

1. **Descriptive Names**: Use clear, descriptive names for prompt constants
2. **Templates**: Use Python string formatting with named parameters
3. **Separation**: Keep system prompts and user prompts separate
4. **Documentation**: Add docstrings to explain what each prompt does
5. **Parameters**: Use type hints and provide default values where appropriate
6. **Testing**: Test prompts with various inputs to ensure they work correctly

## Current Prompts

### Translation Prompts (`translation.py`)
- `TRANSLATE_SRT_SYSTEM_PROMPT` - System prompt for subtitle translation
- `TRANSLATE_SRT_USER_PROMPT_TEMPLATE` - User prompt template for subtitle translation

## Future Prompts

Consider adding prompts for:
- Text summarization
- Content generation
- Error analysis
- Quality assessment
- Language detection
