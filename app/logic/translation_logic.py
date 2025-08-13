import os
from openai import OpenAI
from dotenv import load_dotenv
import multiprocessing as mp
from functools import partial
import logging
import re
import codecs
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Language difference constants for narration timing
LANGUAGE_DIFFERENCES = {
    "en": { "words": 10.0, "syllables": 10.0 },
    "pt": { "words": 11.0, "syllables": 11.8 },
    "es": { "words": 10.8, "syllables": 11.5 },
    "hi": { "words": 12.5, "syllables": 13.5 },
    "in": { "words": 11.2, "syllables": 12.2 },
    "he": { "words": 10.6, "syllables": 11.0 },
    "ar": { "words": 11.8, "syllables": 12.6 },
    "fr": { "words": 10.5, "syllables": 11.3 }
}

def get_languages_diff(src_lang: str, tgt_lang: str) -> dict:
    """
    Calculate the difference in words and syllables per second between source and target languages.
    """
    # Check if both languages exist in our table
    if src_lang not in LANGUAGE_DIFFERENCES or tgt_lang not in LANGUAGE_DIFFERENCES:
        logger.warning(f"Language not found in table: src={src_lang}, tgt={tgt_lang}")
        return {"words": 0, "syllables": 0}
    
    src_words = LANGUAGE_DIFFERENCES[src_lang]["words"]
    src_syllables = LANGUAGE_DIFFERENCES[src_lang]["syllables"]
    tgt_words = LANGUAGE_DIFFERENCES[tgt_lang]["words"]
    tgt_syllables = LANGUAGE_DIFFERENCES[tgt_lang]["syllables"]
    
    # Calculate percentage differences
    word_pct = round((tgt_words / src_words - 1) * 100)
    syllable_pct = round((tgt_syllables / src_syllables - 1) * 100)
    
    logger.info(f"Language diff {src_lang}->{tgt_lang}: words={word_pct}%, syllables={syllable_pct}%")
    
    return {"words": word_pct, "syllables": syllable_pct}

def _translate_chunk_worker(args):
    """Worker function for translating a single chunk"""
    try:
        chunk, src_lang, tgt_lang, chunk_index, translation_notes = args
        logger.info(f"Translating chunk {chunk_index + 1}")
        
        result = call_gpt_chunk(chunk, src_lang, tgt_lang, translation_notes)
        logger.info(f"Successfully translated chunk {chunk_index + 1}")
        
        return chunk_index, result
        
    except Exception as e:
        logger.error(f"Error translating chunk {chunk_index + 1}: {str(e)}")
        raise

def call_gpt_chunk(chunk: str, src_lang: str, tgt_lang: str, translation_notes: str = None) -> str:
    """Call GPT to translate a chunk of SRT content."""
    from app.utils.text_utils import clean_translated_text
    from app.utils.prompt_utils import get_prompt, get_system_prompt
    
    lang_diff = get_languages_diff(src_lang, tgt_lang)
    word_pct = abs(lang_diff["words"])
    syllable_pct = abs(lang_diff["syllables"])
    word_pct_type = "less" if lang_diff["words"] < 0 else "more"
    syl_pct_type = "less" if lang_diff["syllables"] < 0 else "more"
    
    # Get prompt using template system
    user_prompt = get_prompt("TRANSLATE_SRT", {
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "word_pct": word_pct,
        "syllable_pct": syllable_pct,
        "word_pct_type": word_pct_type,
        "syl_pct_type": syl_pct_type,
        "chunk": chunk,
        "translation_notes": translation_notes or ""
    })

    system_prompt = get_system_prompt("TRANSLATE_SRT")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
    )

    result = response.choices[0].message.content.strip()
    return clean_translated_text(result)

def translate_srt_with_gpt(srt_text: str, src_lang: str, tgt_lang: str, max_workers: int = 5, translation_notes: str = None):
    """
    Translate SRT content using GPT with parallel processing.
    """
    from app.utils.text_utils import split_srt
    
    chunks = split_srt(srt_text)
    logger.info(f"Split SRT into {len(chunks)} chunks for parallel translation")
    
    if len(chunks) == 1:
        logger.info("Single chunk detected, using sequential processing")
        translated = call_gpt_chunk(chunks[0], src_lang, tgt_lang, translation_notes)
        return translated, None
    
    # Prepare arguments for multiprocessing
    args_list = []
    for i, chunk in enumerate(chunks):
        args_list.append((chunk, src_lang, tgt_lang, i, translation_notes))
    
    # Use multiprocessing to translate chunks in parallel
    actual_workers = min(max_workers, len(chunks))
    logger.info(f"Using {actual_workers} parallel processes for translation")
    
    try:
        with mp.Pool(processes=actual_workers) as pool:
            results = pool.map(_translate_chunk_worker, args_list)
        
        # Sort results by chunk index to maintain order
        results.sort(key=lambda x: x[0])
        translated_chunks = [result[1] for result in results]
        
        logger.info(f"Successfully translated {len(translated_chunks)} chunks")
        
        return "\n\n".join(translated_chunks), None
        
    except Exception as e:
        logger.error(f"Error in parallel translation: {str(e)}")
        raise
