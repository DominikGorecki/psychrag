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
import threading
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from hierarchical.postprocessor import ResultPostprocessor
from hierarchical.hierarchy_builder import create_toc
from hierarchical.hierarchy_builder_metadata import HierarchyBuilderMetadata


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False,
    ocr: bool = False,
    hierarchical: bool = True
) -> str:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Optional path for the output Markdown file.
                    If provided, the markdown will be written to this file.
        verbose: If True, print progress information.
        ocr: If True, enable OCR for scanned PDFs. Default False for text PDFs.
        hierarchical: If True, apply hierarchical heading detection. Default True.

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
    if hierarchical:
        if verbose:
            print("Applying hierarchical heading detection...")

        # First check if TOC-based approach will have too many missing titles
        use_style_based = False
        try:
            hbm = HierarchyBuilderMetadata(result, pdf_path)
            toc = hbm.toc
            if toc:
                # Count how many TOC entries are missing coordinates (not found)
                missing_count = sum(1 for _, _, _, info in toc if "coords" not in info)
                total_count = len(toc)
                if missing_count > 0 and verbose:
                    print(f"TOC has {missing_count}/{total_count} entries not found in document")
                # If more than 20% of entries are missing, use style-based approach
                if total_count > 0 and missing_count / total_count > 0.2:
                    if verbose:
                        print("Too many missing TOC entries, falling back to style-based approach")
                    use_style_based = True
            else:
                # No TOC found at all - use style-based approach
                if verbose:
                    print("No TOC found in document, using style-based approach")
                use_style_based = True
        except Exception as e:
            if verbose:
                print(f"TOC extraction failed: {e}, using style-based approach")
            use_style_based = True

        # Run hierarchical processing with timeout
        error_container = [None]
        timed_out = [False]

        def run_hierarchical():
            try:
                postprocessor = ResultPostprocessor(result, pdf_path)
                if use_style_based:
                    # Force style-based by clearing the TOC cache
                    postprocessor.result = result
                    headings = postprocessor.get_headers()
                    if headings:
                        from hierarchical.postprocessor import flatten_hierarchy_tree
                        from docling_core.types.doc.document import SectionHeaderItem
                        root = create_toc(headings)
                        flat_hierarchy = flatten_hierarchy_tree(root, 0)
                        by_ref = {el[0].doc_ref: el for el in flat_hierarchy}
                        for item, _ in result.document.iterate_items():
                            if item.self_ref in by_ref and isinstance(item, SectionHeaderItem):
                                _, level = by_ref[item.self_ref]
                                item.level = level
                else:
                    postprocessor.process()
            except Exception as e:
                error_container[0] = e

        thread = threading.Thread(target=run_hierarchical, daemon=True)
        thread.start()
        thread.join(timeout=60)  # 60 second timeout

        if thread.is_alive():
            timed_out[0] = True
            if verbose:
                print("Warning: Hierarchical processing timed out")
            # Try style-based as fallback
            if not use_style_based:
                if verbose:
                    print("Attempting style-based fallback...")
                try:
                    postprocessor = ResultPostprocessor(result, pdf_path)
                    headings = postprocessor.get_headers()
                    if headings:
                        from hierarchical.postprocessor import flatten_hierarchy_tree
                        from docling_core.types.doc.document import SectionHeaderItem
                        root = create_toc(headings)
                        flat_hierarchy = flatten_hierarchy_tree(root, 0)
                        by_ref = {el[0].doc_ref: el for el in flat_hierarchy}
                        for item, _ in result.document.iterate_items():
                            if item.self_ref in by_ref and isinstance(item, SectionHeaderItem):
                                _, level = by_ref[item.self_ref]
                                item.level = level
                        if verbose:
                            print("Style-based fallback successful")
                except Exception as e:
                    if verbose:
                        print(f"Style-based fallback failed: {e}")
        elif error_container[0]:
            if verbose:
                print(f"Warning: Hierarchical processing failed: {error_container[0]}")

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

    parser.add_argument(
        "--no-hierarchical",
        action="store_true",
        help="Disable hierarchical heading detection (use if conversion hangs)"
    )

    args = parser.parse_args()

    try:
        markdown_content = convert_pdf_to_markdown(
            pdf_path=args.pdf_path,
            output_path=args.output,
            verbose=args.verbose,
            ocr=args.ocr,
            hierarchical=not args.no_hierarchical
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
