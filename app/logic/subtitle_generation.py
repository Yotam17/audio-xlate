import spacy
from typing import List, Dict, Tuple
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_CHARS_PER_LINE = 42
GRACE_CHARS = 45
MIN_CHARS_BEFORE_SPLIT = 30
GAP_FOR_BOUNDARY = 1.5  # seconds
SHORT_SUBTITLE_PERIOD = 2.5  # seconds

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("SpaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

class Sentence:
    """Represents a sentence with its timing information and associated words"""
    def __init__(self, text: str, start_time: float, end_time: float, is_boundary: bool = False, words: List[Dict] = None):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.is_boundary = is_boundary
        self.words = words or []

def optimize_cut(text: str, max_length: int) -> (str, str):
    """
    Try to cut at a comma or space close to max_length.
    Returns two parts: the part before the cut and the remaining part.
    """
    if len(text) <= max_length:
        return text, ""

    # Prefer cutting at punctuation, then space
    for punct in [",", " "]:
        idx = text.rfind(punct, 0, max_length)
        if punct!=" " and max_length-idx > 10:
            continue
        if idx != -1:
            return text[:idx+1].strip(), text[idx+1:].strip()

    # Fallback to hard cut
    return text[:max_length], text[max_length:]

def split_text_by_word_alignment(full_text: str, words: List[Dict], first_text: str, second_text: str):
    """
    Split a long sentence using word-aligned timings after a text cut.

    Args:
        full_text: The full sentence text.
        words: List of word dicts with 'word', 'start', 'end' (only the relevant words for this text).
        first_text: The first part of the sentence after the cut.
        second_text: The remaining text.

    Returns:
        Tuple of two dicts: (subtitle1, subtitle2) each with 'text', 'start', 'end'.
    """
    if not words:
        # Fallback if no words available
        logger.warning("No words available for alignment, using rough timing")
        return {
            "start": 0,
            "end": 1,
            "text": first_text
        }, {
            "start": 1,
            "end": 2,
            "text": second_text
        }
    
    # Count words in first_text to determine how many words to use
    first_text_word_count = len(first_text.split())
    
    if first_text_word_count > len(words):
        logger.warning(f"First text has {first_text_word_count} words but only {len(words)} words available")
        first_text_word_count = len(words)
    
    # Use the first N words for the first part
    words_first = words[:first_text_word_count]
    words_second = words[first_text_word_count:] if first_text_word_count < len(words) else []
    
    subtitle1 = {
        "start": words_first[0]["start"],
        "end": words_first[-1]["end"],
        "text": first_text
    }
    
    if words_second:
        subtitle2 = {
            "start": words_second[0]["start"],
            "end": words_second[-1]["end"],
            "text": second_text
        }
    else:
        # If no words left for second part, use timing from first part
        subtitle2 = {
            "start": subtitle1["end"],
            "end": subtitle1["end"] + 1,  # Add 1 second as fallback
            "text": second_text
        }
    
    return subtitle1, subtitle2

def generate_subtitles_from_whisper(verbose_response: dict) -> List[Dict]:
    """
    Convert Whisper verbose JSON response to a list of subtitles (dict with start, end, text).
    """
    if not verbose_response or 'segments' not in verbose_response:
        logger.error("Invalid Whisper response: missing 'segments'")
        return []

    segments = verbose_response['segments']
    words = verbose_response.get('words', [])
    
    # Validate that segments exist
    if not segments:
        logger.error("No segments found in Whisper response")
        return []
    
    # Check if words data exists
    if not words:
        logger.warning("No word-level timing data found in Whisper response. Subtitle generation may not be optimal.")
    
    logger.info(f"Processing {len(segments)} segments with {len(words)} words")
    
    # === STEP 1: Collect all text from segments ===
    full_text = ""
    for segment in segments:
        full_text += segment['text']
    
    logger.info(f"Collected full text: {len(full_text)} characters")
    
    # === STEP 2: Split full text into sentences using SpaCy ===
    all_sentences = split_text_into_sentences(full_text, words)

    # Print first 4 sentences for debugging
    logger.info("First 4 sentences:")
    for i, sent in enumerate(all_sentences):
        if sent.is_boundary:
            logger.info(f"Sentence {i+1}:")
            logger.info(f"  Text: {sent.text}")
            logger.info(f"  Start time: {sent.start_time:.2f}s")
            logger.info(f"  End time: {sent.end_time:.2f}s") 
            logger.info(f"  Is boundary: {sent.is_boundary}")
            logger.info(f"  Word count: {len(sent.words)}")
            logger.info(f"  Words: {[word['word'] for word in sent.words]}")
    logger.info(f"Split full text into {len(all_sentences)} sentences")

    # === STEP 3: Subtitle construction ===
    subtitles = []
    current_text = ""
    current_start = None
    current_end = None
    current_words = []  # Track the words for the current subtitle

    i = 0
    while i < len(all_sentences):
        sentence = all_sentences[i]
        sent_text = sentence.text
        sent_start = sentence.start_time
        sent_end = sentence.end_time
        is_boundary = sentence.is_boundary
        sentence_words = sentence.words  # Words for this sentence

        if not current_text:
            current_text = sent_text
            current_start = sent_start
            current_end = sent_end
            current_words = sentence_words.copy()  # Start with this sentence's words
        else:
            # Add with space
            current_text = (current_text + " " + sent_text).replace("  "," ").strip()
            current_end = sent_end
            current_words.extend(sentence_words)  # Add this sentence's words

        # === Handle long subtitles ===
        while len(current_text) > GRACE_CHARS:
            # Try to cut the text
            first_part, second_part = optimize_cut(current_text, MAX_CHARS_PER_LINE)

            if first_part:
                # Count words in first_part to know how many words to use
                first_part_word_count = len(first_part.split())
                
                # Take the first N words from current_words
                words_for_first_part = current_words[:first_part_word_count]
                
                # Align timings by word list
                subtitle1, subtitle2 = split_text_by_word_alignment(
                    current_text,
                    words_for_first_part,  # Pass only the relevant words
                    first_part,
                    second_part
                )

                # Handle short subtitle duration
                duration = subtitle1["end"] - subtitle1["start"]
                if duration < SHORT_SUBTITLE_PERIOD and i + 1 < len(all_sentences):
                    next_start = all_sentences[i + 1].start_time
                    subtitle1["end"] = min(subtitle1["start"] + SHORT_SUBTITLE_PERIOD, next_start)

                subtitles.append(subtitle1)

                # Prepare to process the remaining tail
                current_text = subtitle2["text"]
                current_start = subtitle2["start"]
                current_end = subtitle2["end"]
                
                # Remove the words we used for the first part
                current_words = current_words[first_part_word_count:]
                
                remaining_text = current_text  # Continue loop
                continue

            else:
                # Could not split cleanly — flush it anyway to avoid loop
                logger.warning(f"Could not split: {current_text}")
                break

        # === Add subtitle if we hit a boundary or have enough text ===
        if len(current_text) >= MIN_CHARS_BEFORE_SPLIT or is_boundary:
            subtitle = {
                "start": current_start,
                "end": current_end,
                "text": current_text.strip()
            }

            # Fix short duration
            duration = current_end - current_start
            if duration < SHORT_SUBTITLE_PERIOD and i + 1 < len(all_sentences):
                next_start = all_sentences[i + 1].start_time
                subtitle["end"] = min(current_start + SHORT_SUBTITLE_PERIOD, next_start)

            subtitles.append(subtitle)
            current_text = ""
            current_start = None
            current_end = None
            current_words = []  # Reset words

        i += 1

    # === Final flush ===
    if current_text:
        subtitle = {
            "start": current_start,
            "end": current_end,
            "text": current_text.strip()
        }
        subtitles.append(subtitle)

    logger.info(f"Generated {len(subtitles)} subtitles")
    return subtitles

def split_text_into_sentences(full_text: str, words: List[Dict]) -> List[Sentence]:
    """
    Split full text into sentences using SpaCy and match words to sentences.
    
    Args:
        full_text: Complete text from all segments
        words: Global words array from the verbose response
    
    Returns:
        List of Sentence objects with timing information and associated words
    """
    if not nlp:
        # Fallback: treat the entire text as one sentence
        return [Sentence(full_text, words[0]['start'] if words else 0, words[-1]['end'] if words else 0, words=words)]
    
    # Use SpaCy to split into sentences
    doc = nlp(full_text)
    sentences = []
    
    # Keep track of which words we've used
    word_index = 0
    
    # Process each sentence
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue
        
        # Count words in this sentence
        sent_word_count = len(sent_text.replace("-", " ").split())
        
        # Take the next N words from the words array
        sent_words = []
        for i in range(sent_word_count):
            if word_index < len(words):
                sent_words.append(words[word_index])
                word_index += 1
        
        if sent_words:
            # Use the timing of the first and last words in the sentence
            start_time = sent_words[0]['start']
            end_time = sent_words[-1]['end']
            
            # Check if this sentence is followed by a significant gap
            is_boundary = False
            if word_index < len(words):
                # Find the next word after this sentence
                next_word_start = words[word_index]['start']
                if (next_word_start - end_time) >= GAP_FOR_BOUNDARY:
                    is_boundary = True
            
            sentences.append(Sentence(sent_text, start_time, end_time, is_boundary, sent_words))
        else:
            # Fallback: use timing from surrounding words or default
            start_time = 0
            end_time = 0
            if words:
                # Find words that come before and after this sentence in the text
                # This is a simplified approach
                start_time = words[0]['start']
                end_time = words[-1]['end']
            
            sentences.append(Sentence(sent_text, start_time, end_time, words=[]))
    
    return sentences
