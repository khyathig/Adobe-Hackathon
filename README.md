# Adobe Hackathon Challenge 1A: Understand Your Document

This project addresses Challenge 1A, "Understand Your Document." The goal is to extract a structured outline (Title, H1, H2, H3 headings with their page numbers) from a given PDF file.

## Approach

This solution uses the `PyMuPDF` (also known as `fitz`) library to parse PDF files and extract structural information.

1.  **Title Extraction:**
    *   First, it attempts to retrieve the document title from the PDF's metadata.
    *   If the metadata title is empty or unavailable, it currently defaults to "Untitled". (A potential enhancement could be to identify the largest or most prominent text on the first page as a fallback title, though this is not implemented in the provided code).
2.  **Outline Extraction:**
    *   **Golden Path (Table of Contents):** The primary method is to use the PDF's built-in Table of Contents (ToC). If a ToC exists and contains entries up to level 3 (H1, H2, H3), it is used directly for the outline.
    *   **Fallback (Heuristic Analysis):** If no usable ToC is found, the code falls back to a heuristic approach:
        *   It scans all text spans across the document to build a summary of font sizes and their frequency.
        *   It identifies the most common font size, assuming this represents the body text.
        *   It identifies font sizes larger than the body text and sorts them in descending order.
        *   It maps the top 3 distinct larger font sizes to heading levels: the largest -> H1, the second largest -> H2, the third largest -> H3.
        *   It iterates through the pages again, identifying text lines that consist of a single span with a font size matching one of the mapped heading sizes.
        *   It adds these identified lines to the outline, trying to avoid obvious duplicates (like headers/footers) by checking if an identical heading text at the same level already exists.

## Models and Libraries Used

*   **`PyMuPDF` (fitz)**: A powerful Python library for PDF processing. It provides fine-grained access to text, fonts, and structure within PDFs, making it suitable for tasks like heading detection without relying solely on OCR or basic text extraction. This is the core library used for all PDF parsing logic in this solution.

## How to Build and Run

### Prerequisites

*   Docker installed and running.

### Docker Execution (As Required by Challenge)

1.  **Build the Docker Image:**
    *   Navigate to the project root directory (where this `README.md` and your `Dockerfile` are located).
    ```bash
    docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
    ```
    *   Replace `mysolutionname:somerandomidentifier` with your desired image name and tag, ensuring it matches the build command specified in the challenge rules.

2.  **Prepare Input Data:**
    *   Ensure your input PDF files are placed in a directory on your host machine (e.g., `./input`).
    *   Ensure an output directory exists on your host machine (e.g., `./output`).

3.  **Run the Docker Container:**
    *   Use the `docker run` command to execute the container. Mount the input and output directories from your host machine into the expected locations (`/app/input`, `/app/output`) inside the container.
    *   The command uses `$(pwd)` to represent the current working directory. Adjust the paths if your input/output directories are located elsewhere.
    ```bash
    # Example assuming input PDFs are in ./input and output should go to ./output
    mkdir -p ./output # Ensure output directory exists
    docker run --rm \
      -v "$(pwd)/input:/app/input" \
      -v "$(pwd)/output:/app/output" \
      --network none \
      mysolutionname:somerandomidentifier
    ```
    *   **Note for Windows Command Prompt (`cmd`):** Use `%cd%` instead of `$(pwd)`:
        ```cmd
        REM Example for Command Prompt
        mkdir output
        docker run --rm -v %cd%\input:/app/input -v %cd%\output:/app/output --network none mysolutionname:somerandomidentifier
        ```

4.  **Check Output:**
    *   After the container finishes running, check the mounted output directory on your host machine (e.g., `./output`).
    *   For each input file `filename.pdf` in the input directory, a corresponding `filename.json` will be generated containing the extracted outline.
