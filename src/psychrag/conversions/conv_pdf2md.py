"""
PDF to Markdown Converter using Docling.

This module provides functionality to convert PDF files to Markdown format
using the Docling library.

Example (as script):
    venv\\Scripts\\python -m psychrag.conversions.conv_pdf2md input.pdf -o output.md

Example (as library):
    from psychrag.conversions import convert_pdf_to_markdown
    markdown_content = convert_pdf_to_markdown("input.pdf")
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from hierarchical.postprocessor import ResultPostprocessor


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False,
    ocr: bool = False
) -> str:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Optional path for the output Markdown file.
                    If provided, the markdown will be written to this file.
        verbose: If True, print progress information.
        ocr: If True, enable OCR for scanned PDFs. Default False for text PDFs.

    Returns:
        The converted Markdown content as a string.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the file is not a PDF file.
    """
    pdf_path = Path(pdf_path)

    # Validate input file
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF file, got: {pdf_path.suffix}")

    if verbose:
        print(f"Converting: {pdf_path}")
        if ocr:
            print("OCR enabled for scanned content")

    # Configure PDF pipeline options
    pipeline_options = PdfPipelineOptions(do_ocr=ocr)

    # Initialize converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = converter.convert(str(pdf_path))

    # Apply hierarchical post-processing for better heading structure
    postprocessor = ResultPostprocessor(result, pdf_path)
    postprocessor.process()

    # Export to markdown
    markdown_content = result.document.export_to_markdown()

    # Write to output file if specified
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        if verbose:
            print(f"Output written to: {output_path}")

    return markdown_content


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown using Docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # Output to stdout
  %(prog)s document.pdf -o document.md     # Output to file
  %(prog)s document.pdf -o output/doc.md   # Output to subdirectory
  %(prog)s document.pdf -v                 # Verbose output
        """
    )

    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the input PDF file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path for the output Markdown file (default: print to stdout)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned PDFs (default: off for text PDFs)"
    )

    args = parser.parse_args()

    try:
        markdown_content = convert_pdf_to_markdown(
            pdf_path=args.pdf_path,
            output_path=args.output,
            verbose=args.verbose,
            ocr=args.ocr
        )

        # Print to stdout if no output file specified
        if not args.output:
            print(markdown_content)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
