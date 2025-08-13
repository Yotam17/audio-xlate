import re
from datetime import timedelta

MIN_MERGE_GAP_SECS = 1.2

def parse_time(srt_time: str):
    h, m, s = srt_time.split(":")
    s, ms = s.split(",")
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))

def ends_with_sentence(text):
    return bool(re.search(r'[.!?…״"。]+$', text.strip()))

def optimize_sentence_flow(srt_text: str):
    entries = []
    blocks = re.split(r'\n{2,}', srt_text.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            number = int(lines[0])
            start, end = lines[1].split(" --> ")
            text = " ".join(lines[2:]).strip()
            entries.append({
                "number": number,
                "start": parse_time(start.strip()),
                "end": parse_time(end.strip()),
                "text": text
            })

    optimized = []
    current = {
        "text": entries[0]["text"],
        "srt_entries": [entries[0]["number"]],
        "last_end": entries[0]["end"]
    }

    for i in range(1, len(entries)):
        prev = entries[i - 1]
        curr = entries[i]
        gap = (curr["start"] - prev["end"]).total_seconds()

        prev_end_sentence = ends_with_sentence(prev["text"])
        if (not prev_end_sentence) and gap <= MIN_MERGE_GAP_SECS:
            current["text"] += " " + curr["text"]
            current["srt_entries"].append(curr["number"])
            current["last_end"] = curr["end"]
        else:
            optimized.append({
                "text": current["text"],
                "srt_entries": current["srt_entries"]
            })
            current = {
                "text": curr["text"],
                "srt_entries": [curr["number"]],
                "last_end": curr["end"]
            }

    # Append the last
    optimized.append({
        "text": current["text"],
        "srt_entries": current["srt_entries"]
    })

    return optimized
