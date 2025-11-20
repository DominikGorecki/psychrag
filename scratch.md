# Santization - All Titles 

Let's now create a new module in `src\psychrag\sanitization` to pull out all the titles of a markdown files to help us then determine the proper hierarchy of the document. For now here is what I would like to see a module that allows me to read the markdown file and save that to a file.

Input: `[markdown_file].md` (the markdown file to analyze)

Output: 
* `markdown_file.titles.md`
* file contents:
    * URI of the where the original file is relative to this file
    * blank line
    * `# ALL TITLES IN DOC`
    * The titles in a code block in the following format:
       * [line-number]: [Literal title line]
       * Example `123: # Title 1`
    * Example of the output as a whole:
    ```md
    ./book.md

    # All TITLES IN DOC
    10: # Title of the book
    13: # Table of Contents
    18: ## Chapter 1
    ...
    ```
# Sanitization - AI Doc Hierarchy
Now I want to run the  `markdown_file.titles.md` and the ToC in the DB to try to get the AI to generate suggested changes to have a proper hierarchy in our markdown document. Here is what I want to happen:
1. input: `markdown_file.titles.md`
2. Read the original document (uri in the first line) and generate the SHA256 hash to find the document in the DB. If it's not found, it should error with an according message
3. If the document is found in src\psychrag\data\models\work.py, read the ToC
