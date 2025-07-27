# PDF Outline Extractor

This tool extracts a structured outline (H1, H2, H3 headings) and the title from PDF documents. It prioritizes the PDF's built-in table of contents and uses advanced heuristics as a fallback to analyze text properties like size, boldness, and position to identify headings, especially when a standard TOC is unavailable or incomplete.

It is designed to run in a Docker container for ease of use and dependency management.

## Features

*   **Smart Title Extraction**: Attempts to get the title from PDF metadata. If unavailable, it intelligently infers the title from the most prominent text on the first page.
*   **Prioritizes Native TOC**: Uses the PDF's internal table of contents if it exists for maximum accuracy.
*   **Advanced Heuristic Fallback**: If no internal TOC is found, it employs a sophisticated analysis of the document's text to identify potential headings based on formatting and positional cues.
*   **Structured Output**: Produces a clean JSON file for each input PDF, containing the document title and a list of identified headings with their levels (H1/H2/H3) and page numbers.
*   **Dockerized**: Packaged in a Docker container for consistent execution across different environments.

## Approach & Ideology

This tool was developed with a focus on accuracy, performance, and adaptability within the constraints of processing diverse PDF documents.

1.  **Leverage Native Structure First:** It always checks for and uses the PDF's built-in TOC as the primary source.
2.  **Intelligent Heuristic Fallback:** When the native TOC is absent, it switches to a heuristic engine that mimics human identification of headings by looking for:
    *   Visual Prominence (Larger font size, bold text).
    *   Content Patterns (Numbering like "1.2", lack of sentence-ending punctuation).
    *   Contextual Clues (Lines appearing alone in a block).
3.  **Data-Driven Style Analysis:** It analyzes the beginning of the document to estimate the style of body text (median font size, standard deviation). This allows the heuristics to be adaptive to different document designs.
4.  **Style-Based Level Assignment:** Instead of guessing absolute levels, it identifies the top 3 distinct visual styles (e.g., Bold+Large, Large, Bold+Medium) among potential headings and maps them to H1, H2, and H3. This pragmatic approach handles varied document structures effectively.
5.  **Robustness:** The heuristics use scoring with thresholds, multiple filters, and penalties to minimize false positives. Post-processing cleans and sorts the final output.

## Tools & Technologies Used

*   **Python:** Core programming language.
*   **PyMuPDF (`fitz`):** High-performance PDF processing library for extracting text, font sizes, styles, and positional data.
*   **Docker:** Containerization for easy setup and consistent execution.
*   **Standard Python Libraries:** `json` (output), `os` (file I/O), `statistics` (document style analysis), `re` (pattern matching for headings), `collections` (utility functions).

## Prerequisites

*   **Docker:** Ensure Docker is installed and running on your system.

## Usage

1.  **Obtain Files:** Ensure you have the following files: `Dockerfile`, `requirements.txt`, and the `src/` directory containing `pdf_outline_extractor.py`.
2.  **Prepare Directories:**
    *   Create an `input` directory in the project root.
    *   Place the PDF files you want to process into the `input` directory.
    *   Create an `output` directory in the project root to store the results.
3.  **Build the Docker Image:**
    ```bash
    docker build -t pdf-outline-extractor .
    ```
4.  **Run the Docker Container:**
    ```bash
    docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-outline-extractor
    ```
    *   This command runs the container named `pdf-outline-extractor`.
    *   `-v $(pwd)/input:/app/input`: Mounts your local `input` directory to `/app/input` inside the container (where the script looks for PDFs).
    *   `-v $(pwd)/output:/app/output`: Mounts your local `output` directory to `/app/output` inside the container (where the script will save the JSON results).
    *   `--rm`: Automatically removes the container after it finishes running.
5.  **Check Output:** After the container finishes, check the `output` directory. You will find a `.json` file for each processed PDF, named after the original PDF (e.g., `document.json` for `document.pdf`).

## Notes

*   **Accuracy:** While the heuristics aim for high accuracy, results can vary depending on the PDF's original structure and formatting complexity. Documents with highly inconsistent heading styles or those lacking clear visual distinctions might produce less accurate outlines.
*   **Performance:** Processing time depends on the number and size of the input PDFs.
*   **Limitations:** Designed primarily for text-based PDFs. Scanned images or complex layouts might not be processed correctly.
