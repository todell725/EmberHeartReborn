import os
import re
from pathlib import Path
from PyPDF2 import PdfReader
# We use ebooklib and bs4 which might need installation later
try:
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    # We will log the error if run, but for now we provide the logic
    print("Warning: ePub support requires 'ebooklib' and 'beautifulsoup4' libraries.")

def transcribe_to_markdown(input_dir, output_dir):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files recursively in the input directory
    for root, _, files in os.walk(input_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_stem = Path(file_name).stem

            # Check file type and select appropriate processing function
            try:
                if file_name.endswith('.pdf'):
                    print(f"Processing PDF: {file_name}")
                    markdown_content = process_pdf(file_path)
                elif file_name.endswith('.txt'):
                    print(f"Processing TXT: {file_name}")
                    markdown_content = process_txt(file_path)
                elif file_name.endswith('.epub'):
                    print(f"Processing EPUB: {file_name}")
                    markdown_content = process_epub(file_path)
                else:
                    # Silently skip unsupported types
                    continue

                # Save as a markdown file
                output_file = os.path.join(output_dir, f"{file_stem}.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                print(f"Transcription completed: {output_file}")

            except Exception as e:
                print(f"Failed to process {file_name}: {e}")


def process_pdf(file_path):
    reader = PdfReader(file_path)
    markdown_content = ""

    for number, page in enumerate(reader.pages, 1):
        markdown_content += f"\n# Page {number}\n\n"
        page_text = page.extract_text()
        markdown_content += page_text

    return process_text_to_markdown(markdown_content)


def process_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return process_text_to_markdown(text)


def process_epub(file_path):
    from ebooklib import epub
    from bs4 import BeautifulSoup
    book = epub.read_epub(file_path)
    markdown_content = ""

    for item in book.get_items():
        if item.get_type() == 9: # ebooklib.ITEM_DOCUMENT
            soup = BeautifulSoup(item.get_content(), "html.parser")
            markdown_content += soup.get_text() + "\n"

    return process_text_to_markdown(markdown_content)


def process_text_to_markdown(text):
    # Clean and format the text into Markdown
    text = re.sub(r'\n\n+', '\n\n', text)        # Remove excessive newlines
    text = text.replace("\n", "  \n")           # Markdown line breaks
    return text


import sys

if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_directory = sys.argv[1]
        output_directory = sys.argv[2]
    else:
        input_directory = input("Enter the directory containing books: ")
        output_directory = input("Enter the output directory for Markdown files: ")
    transcribe_to_markdown(input_directory, output_directory)
