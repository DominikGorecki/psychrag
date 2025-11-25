"""
Conversion Router - Document conversion operations.

Endpoints:
    POST /conv/epub       - Convert EPUB to markdown
    POST /conv/pdf        - Convert PDF to markdown
    GET  /conv/status/{id} - Get conversion job status
    GET  /conv/formats    - List supported formats
"""

from fastapi import APIRouter, File, UploadFile, status

from psychrag_api.schemas.conversion import (
    ConversionJobResponse,
    ConversionStatusResponse,
    SupportedFormatsResponse,
)

router = APIRouter()


@router.get(
    "/formats",
    response_model=SupportedFormatsResponse,
    summary="List supported formats",
    description="Get a list of all supported input and output formats for conversion.",
)
async def get_supported_formats() -> SupportedFormatsResponse:
    """
    Get supported conversion formats.
    
    Returns:
    - Input formats (EPUB, PDF, etc.)
    - Output formats (Markdown, etc.)
    """
    return SupportedFormatsResponse(
        input_formats=["epub", "pdf"],
        output_formats=["markdown"],
        converters={
            "epub": {
                "description": "EPUB e-book format",
                "extensions": [".epub"],
                "module": "psychrag.conversions.conv_epub2md",
            },
            "pdf": {
                "description": "PDF document format", 
                "extensions": [".pdf"],
                "module": "psychrag.conversions.conv_pdf2md",
            },
        },
    )


@router.post(
    "/epub",
    response_model=ConversionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Convert EPUB to markdown",
    description="Upload an EPUB file and convert it to markdown format.",
    responses={
        202: {"description": "Conversion job started"},
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"},
    },
)
async def convert_epub(
    file: UploadFile = File(
        ...,
        description="EPUB file to convert",
    ),
) -> ConversionJobResponse:
    """
    Convert an EPUB file to markdown.
    
    The conversion runs asynchronously. Use the returned job_id
    to check the status and retrieve the result.
    """
    # TODO: Implement using psychrag.conversions.conv_epub2md
    return ConversionJobResponse(
        job_id="conv_epub_12345",
        status="queued",
        message=f"Stub: Would convert {file.filename} to markdown",
        input_filename=file.filename or "unknown.epub",
    )


@router.post(
    "/pdf",
    response_model=ConversionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Convert PDF to markdown",
    description="Upload a PDF file and convert it to markdown format.",
    responses={
        202: {"description": "Conversion job started"},
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"},
    },
)
async def convert_pdf(
    file: UploadFile = File(
        ...,
        description="PDF file to convert",
    ),
) -> ConversionJobResponse:
    """
    Convert a PDF file to markdown.
    
    The conversion runs asynchronously. Use the returned job_id
    to check the status and retrieve the result.
    """
    # TODO: Implement using psychrag.conversions.conv_pdf2md
    return ConversionJobResponse(
        job_id="conv_pdf_12345",
        status="queued",
        message=f"Stub: Would convert {file.filename} to markdown",
        input_filename=file.filename or "unknown.pdf",
    )


@router.get(
    "/status/{job_id}",
    response_model=ConversionStatusResponse,
    summary="Get conversion status",
    description="Check the status of a conversion job.",
    responses={
        200: {"description": "Job status retrieved"},
        404: {"description": "Job not found"},
    },
)
async def get_conversion_status(job_id: str) -> ConversionStatusResponse:
    """
    Get the status of a conversion job.
    
    Returns current status and result if complete.
    """
    # TODO: Implement job status tracking
    return ConversionStatusResponse(
        job_id=job_id,
        status="completed",
        progress=100,
        output_path="/output/converted_file.md",
        message="Stub: Conversion complete",
    )


