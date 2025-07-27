# src/pdf_outline_extractor.py
"""
Round 1A: Understand Your Document
Extracts Title and H1/H2/H3 headings from PDFs using advanced heuristics.
Designed for accuracy, performance, and multilingual support within constraints.
"""
import fitz  # PyMuPDF
import json
import os
from collections import Counter
import statistics
import re

# --- Configuration (Matches Docker volume mounts) ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
# --- End Configuration ---

def get_text_characteristics(text):
    """Analyzes basic text characteristics."""
    if not text:
        return {
            'is_all_caps': False, 'is_title_case': False, 'ends_with_period': False,
            'word_count': 0, 'char_count': 0
        }
    # A stricter check for title case that ignores single-word all-caps lines
    is_title_case = text.istitle() and not text.isupper()
    is_all_caps = text.isupper() and len(text.split()) > 0
    ends_with_period = text.rstrip().endswith('.')
    word_count = len(text.split())
    char_count = len(text)
    return {
        'is_all_caps': is_all_caps,
        'is_title_case': is_title_case,
        'ends_with_period': ends_with_period,
        'word_count': word_count,
        'char_count': char_count
    }

def analyze_document_style(doc):
    """Analyzes font sizes and styles to estimate body text stats."""
    font_sizes = []
    pages_to_analyze = min(5, doc.page_count)

    for page_num in range(pages_to_analyze):
        page = doc.load_page(page_num)
        # Focus on the main content area
        content_rect = fitz.Rect(page.rect.width * 0.1, page.rect.height * 0.1, page.rect.width * 0.9, page.rect.height * 0.9)
        blocks = page.get_text("dict", clip=content_rect)["blocks"]
        for block in blocks:
            if block['type'] == 0:  # Text block
                # Only analyze blocks that look like paragraphs
                if len(block['lines']) > 2 and len(block['lines'][0]['spans'][0]['text'].split()) > 3:
                    for line in block['lines']:
                        for span in line['spans']:
                            size = round(span['size'], 1)
                            if 7 <= size <= 24:
                                font_sizes.append(size)

    if not font_sizes:
        return {'median_size': 11.0, 'std_dev': 1.5}

    median_size = statistics.median(font_sizes)
    std_dev = statistics.stdev(font_sizes) if len(set(font_sizes)) > 1 else 1.0

    return {'median_size': median_size, 'std_dev': std_dev}

def is_line_a_heading(line_text, line_size, is_bold, is_standalone, body_stats):
    """Applies heuristics to a line of text to see if it's a heading."""
    if not line_text or line_text.isdigit():
        return False, 0.0

    text_chars = get_text_characteristics(line_text)

    # --- Quick Rejection Filters ---
    if text_chars['word_count'] > 25: return False, 0.0
    if text_chars['ends_with_period'] and text_chars['word_count'] > 5: return False, 0.0

    # --- Scoring ---
    score = 0.0
    max_score = 20.0

    is_large = line_size > body_stats['median_size'] + 0.5

    # A line must have at least one strong characteristic
    if not is_bold and not is_large and not text_chars['is_all_caps']:
        return False, 0.0

    # --- Positive Indicators ---
    if is_bold: score += 6
    if is_large: score += 4
    if line_size > body_stats['median_size'] + 2.5: score += 2 # Extra for very large
    if text_chars['is_all_caps'] and text_chars['word_count'] < 10: score += 3
    if text_chars['is_title_case']: score += 2
    if is_standalone: score += 2 # Bonus for being in its own text block

    # Numbered / Appendix headings (e.g. "1.2 Section", "Appendix A:")
    if re.match(r"^((\d{1,2}(\.\d{1,2})*\.?)|([A-Z]\.)|(Appendix|Chapter|Section)\s+[\w\d])\s+", line_text):
        score += 5

    # --- Penalties ---
    if text_chars['ends_with_period']: score -= 3
    if text_chars['word_count'] == 1 and not is_large and not text_chars['is_all_caps']: score -= 2
    if text_chars['word_count'] > 15: score -= 2

    normalized_score = max(0.0, score / max_score)

    return normalized_score >= 0.35, normalized_score # Threshold for raw score of 7

def extract_outline(pdf_path):
    """Extracts the title and a structured outline (H1, H2, H3) from a PDF."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"Failed to open PDF: {e}"}

    if doc.page_count == 0:
        return {"title": "Untitled", "outline": []}

    # 1. Get Title from metadata or first prominent text
    title = doc.metadata.get('title', '').strip()
    if not title or len(title) < 5:
        page = doc[0]
        blocks = page.get_text("dict", sort=True)["blocks"]
        # Look for the largest, boldest text in the top half of the first page
        candidates = []
        for block in blocks:
            if block['type'] == 0 and block['bbox'][1] < page.rect.height / 2:
                for line in block['lines']:
                    if line['spans']:
                        span = line['spans'][0]
                        text = span['text'].strip()
                        if len(text) > 3 and len(text.split()) < 15:
                            score = span['size'] + (2 if (span['flags'] & 2**4) else 0)
                            candidates.append((score, text))
        if candidates:
            title = max(candidates, key=lambda item: item[0])[1]
        else:
            title = os.path.basename(pdf_path)

    outline = []

    # 2. Golden Path: Built-in Table of Contents
    toc = doc.get_toc()
    if toc:
        for level, text, page in toc:
            if 1 <= level <= 3:
                outline.append({"level": f"H{level}", "text": text.strip(), "page": page})
        if outline:
            return {"title": title, "outline": outline}

    # 3. Fallback: Heuristic Analysis
    body_stats = analyze_document_style(doc)
    potential_headings = []

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict", sort=True)["blocks"]
        for i, block in enumerate(blocks):
            if block['type'] == 0:  # Text Block
                # A block is "standalone" if it has few lines and there's space around it
                is_standalone = len(block['lines']) <= 2
                
                for line in block['lines']:
                    line_text = " ".join([s['text'] for s in line['spans']]).strip()
                    if not line['spans']: continue
                    
                    # Consolidate line properties
                    avg_size = round(statistics.mean([s['size'] for s in line['spans']]), 1)
                    # A line is bold if the majority of its text (by length) is bold
                    bold_char_count = sum(len(s['text']) for s in line['spans'] if (s['flags'] & 2**4))
                    is_line_bold = (bold_char_count / len(line_text)) > 0.5 if line_text else False

                    is_heading, confidence = is_line_a_heading(line_text, avg_size, is_line_bold, is_standalone, body_stats)

                    if is_heading:
                        potential_headings.append({
                            "text": line_text,
                            "size": avg_size,
                            "page": page_num + 1,
                            "y_pos": line['bbox'][1],
                            "is_bold": is_line_bold
                        })

    if not potential_headings:
        return {"title": title, "outline": []}

    # --- Rank and Assign Levels based on visual signature ---
    def get_visual_signature(h):
        # Group size into buckets to treat similar sizes as the same level
        size_bucket = round(h['size'] * 2) / 2
        return (h['is_bold'], size_bucket)

    signatures = [get_visual_signature(h) for h in potential_headings]
    # Get unique signatures, sorted from most prominent (bold, largest) to least
    unique_signatures = sorted(list(set(signatures)), key=lambda s: (-s[0], -s[1]))

    # Map the top 3 distinct styles to H1, H2, H3
    level_map = {sig: f"H{i+1}" for i, sig in enumerate(unique_signatures[:3])}

    for heading in potential_headings:
        sig = get_visual_signature(heading)
        level = level_map.get(sig)
        if level:
            outline.append({
                "level": level,
                "text": heading['text'],
                "page": heading['page'],
                "y_pos": heading['y_pos']
            })

    # --- Final sort, cleanup, and duplicate removal ---
    outline.sort(key=lambda x: (x['page'], x['y_pos']))

    cleaned_outline = []
    if outline:
        last_text = ""
        last_page = -1
        for item in outline:
            # Simple duplicate check
            if not (item['text'] == last_text and item['page'] == last_page):
                cleaned_outline.append({"level": item["level"], "text": item["text"], "page": item["page"]})
            last_text = item['text']
            last_page = item['page']
            
    # Remove first heading if it's the same as the document title
    if cleaned_outline and cleaned_outline[0]['text'].lower() in title.lower():
        cleaned_outline.pop(0)

    return {"title": title, "outline": cleaned_outline}

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    processed_count = 0
    print(f"Starting processing from '{INPUT_DIR}'...")
    for filename in sorted(os.listdir(INPUT_DIR)):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing: {filename}")
            try:
                output_data = extract_outline(pdf_path)
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                processed_count += 1
            except Exception as e:
                print(f"  -> ERROR processing {filename}: {e}")

    print(f"\nFinished processing {processed_count} PDF file(s).")