# docling hierarchical pdf
When converting PDFs, I want to try to better approximatee the correct title hierarchy. One way to do that is to use `docling-hierarchical-pdf`.

Here is one example of how it can be done:

```python
from docling_hierarchical_pdf.pipeline import StandardPdfPipeline
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure the converter to use the hierarchical pipeline
pipeline_options = PdfFormatOption(pipeline_cls=StandardPdfPipeline)
converter = DocumentConverter(format_options={InputFormat.PDF: pipeline_options})

# Convert your file
result = converter.convert("my_document.pdf")
print(result.document.export_to_markdown())
```

# Santization 

Let's now create a new module in `src\psychrag\sanitization` to pull out all the titles of a markdown files to help us then determine the proper hierarchy of the document. For now here is what I would like to see a module that allows me to read the markdown file and save that to a file.

Input: `[markdown_file].md` (the markdown file to analyze)

Output: `markdown_file.titles.md`
