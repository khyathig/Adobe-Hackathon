import fitz  # PyMuPDF
import json
import os
import re

# Define the input and output directories
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def extract_outline(pdf_path):
    """
    Extracts the title and a structured outline (H1, H2, H3) from a PDF.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"Failed to open PDF: {e}"}

    # 1. Get Title: Prioritize metadata, fallback to largest text on first page
    title = doc.metadata.get('title', 'Untitled')
    if not title.strip():
        title = "Untitled"

    outline = []

    # 2. Golden Path: Try to get the built-in Table of Contents first
    toc = doc.get_toc()
    if toc:
        for level, text, page in toc:
            if level <= 3:  # We only need H1, H2, H3
                outline.append({
                    "level": f"H{level}",
                    "text": text,
                    "page": page
                })
        if outline:
            return {"title": title, "outline": outline}

    # 3. Fallback: Heuristic analysis if ToC is not available
    fonts_summary = {}
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] == 0:  # Text block
                for line in block['lines']:
                    for span in line['spans']:
                        size = round(span['size'])
                        if size not in fonts_summary:
                            fonts_summary[size] = 0
                        fonts_summary[size] += len(span['text'].strip())

    # Identify body text font size (most common)
    if not fonts_summary:
        return {"title": title, "outline": []}  # Empty document

    body_size = max(fonts_summary, key=fonts_summary.get)

    # Identify heading font sizes (larger than body text)
    heading_sizes = sorted([size for size in fonts_summary if size > body_size], reverse=True)

    # Map sizes to H1, H2, H3
    level_map = {}
    if len(heading_sizes) > 0: level_map[heading_sizes[0]] = "H1"
    if len(heading_sizes) > 1: level_map[heading_sizes[1]] = "H2"
    if len(heading_sizes) > 2: level_map[heading_sizes[2]] = "H3"

    # Extract headings based on font size and simple rules
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] == 0:
                for line in block['lines']:
                    # Simple rule: A short line is likely a heading
                    if len(line['spans']) == 1:
                        span = line['spans'][0]
                        size = round(span['size'])
                        text = span['text'].strip()

                        # Rule: Must have text and be a heading size
                        if text and size in level_map:
                            # Rule: Avoid adding duplicate headings from page footers/headers
                            if not any(o['text'] == text and o['level'] == level_map[size] for o in outline):
                                outline.append({
                                    "level": level_map[size],
                                    "text": text,
                                    "page": page_num + 1
                                })

    # If heuristic failed to find a title, use the first H1
    if title == "Untitled" and outline and outline[0]['level'] == "H1":
        title = outline[0]['text']

    return {"title": title, "outline": outline}


if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process all PDF files in the input directory
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            output_data = extract_outline(pdf_path)

            # Write the JSON output
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"Processed {filename} -> {output_filename}")
            
   
