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
3. If the document is found in src\psychrag\data\models\work.py, read the ToC JSON 
4. Pass in the codeblock into the LLM and the ToC to try to get the LLM to best approximate the changes to be made for a proper hierarchy when comparing the ToC from the DB to the titles in the `markdown_file.titles.md`
   a) ToC main chapter should be H1
   b) Anything in between (or based on the ToC) that is a Section is H2
   c) Anything identified as a subsection should be H3
   d) ...
   e) Anything that shouldn't be a heading should be identified as `REMOVE HEADING`
5. To determine the title headings I want the search to be turned on the thee LLM can rely on the following to make the best possible approximation on the headings:
   a) It's own knowledge--perhaps it knows the breakdown of the work already
   b) Pass in the title and author of the work so the LLM can run a search to see if there is anything in the web
   c) The ToC passed in from the DB
   d) The Title Codeblock from `markdown_file.titles.md`
6. The output should be based on the the codeblock with all the titles in `markdown_file.titles.md`:
   a) [line number:] [NO_CHANGE | REMOVE | H1 | H2 | H3 | H4]
   b) Example if this is the original titles codeblock:
        ```md
        ./book.md

        # All TITLES IN DOC
        10: # Title of the book
        13: ## Table of Contents
        18: ## Chapter 1
        19: ## Section 1.1
        20: ## Subsection 1.1.1
        ...
        ```

    **THE EXPECTED OUTPUT COULD BE**
        ```md
        # CHANGES TO HEADINGS
        10: NO_CHANGE
        13: H1
        18: H1
        19: H2
        20: H3
        ...
        ```
    c) Save the output to a file in the same folder in the following format `markdown_file.title_changes.md`

    # CLI FOR src\psychrag\sanitization\extract_titles.py

    Create a CLI for `src\psychrag\sanitization\extract_titles.py` and remember to follow the instructions and add documentation at the top for how to use it in both `src\psychrag\sanitization\extract_titles.py` and the new cli filee. 