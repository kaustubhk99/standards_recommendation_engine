"""PDF Loader module for extracting text from PDF documents."""
import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a PDF page-by-page preserving order.
    """
    doc = fitz.open(pdf_path)
    pages_text = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages_text.append(
                f"\n\n--- PAGE {page_number} ---\n\n{text}"
            )

    doc.close()
    return "\n".join(pages_text)


def process_pdf_folder(input_dir: Path, output_dir: Path):
    """
    Processes all PDFs in a folder and writes extracted text files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in input_dir.glob("*.pdf"):
        print(f"Extracting: {pdf_file.name}")

        extracted_text = extract_text_from_pdf(pdf_file)

        output_file = output_dir / pdf_file.with_suffix(".txt").name
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        print(f"Saved: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF Text Extraction")
    parser.add_argument("--input_dir", required=True, help="Folder with PDFs")
    parser.add_argument("--output_dir", required=True, help="Folder to save text files")

    args = parser.parse_args()

    process_pdf_folder(
        Path(args.input_dir),
        Path(args.output_dir)
    )
