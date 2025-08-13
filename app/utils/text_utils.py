"""
Text utility functions for cleaning and processing text.
"""

def split_srt(srt: str, max_chars: int = 1000):
    """
    Split SRT content into chunks for processing.
    """
    blocks = srt.strip().split("\n\n")
    chunks = []
    current_chunk = ""
    for block in blocks:
        if len(current_chunk) + len(block) > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = block + "\n\n"
        else:
            current_chunk += block + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def clean_translated_text(text: str) -> str:
    """
    Remove markdown code block wrapping from translated SRT content.
    Handles cases where GPT wraps the response in ```plaintext or ``` blocks.
    """
    # Remove markdown code block wrapping
    text = text.strip()
    
    # Remove ```plaintext at the beginning
    if text.startswith("```plaintext"):
        text = text[12:]  # Remove "```plaintext"
    
    # Remove ``` at the beginning (any language)
    if text.startswith("```"):
        # Find the first newline after ```
        first_newline = text.find('\n', 3)
        if first_newline != -1:
            text = text[first_newline + 1:]  # Remove the opening ``` and language identifier
        else:
            text = text[3:]  # Just remove ```
    
    # Remove ``` at the end
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()
