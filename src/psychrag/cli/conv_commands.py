"""Conversion CLI commands."""

from pathlib import Path

from psychrag.conversions.conv_pdf2md import convert_pdf_to_markdown
from psychrag.conversions.conv_epub2md import convert_epub_to_markdown


SUPPORTED_FORMATS = {".pdf", ".epub"}


def run_conv2md(input_file: str, output_dir: Path, verbose: bool = False) -> int:
    """
    Convert a PDF or EPUB file to Markdown.

    Args:
        input_file: Path to the input file.
        output_dir: Directory for output files.
        verbose: If True, print progress information.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    suffix = input_path.suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        print(f"Error: Unsupported file format '{suffix}'. Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return 1

    # Create output path
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_path.stem}.md"

    try:
        if suffix == ".pdf":
            if verbose:
                print(f"Converting PDF: {input_path}")
            convert_pdf_to_markdown(input_path, output_path, verbose=verbose)

        elif suffix == ".epub":
            if verbose:
                print(f"Converting EPUB: {input_path}")
            convert_epub_to_markdown(input_path, output_path, verbose=verbose)

        print(f"Output: {output_path}")
        return 0

    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1
