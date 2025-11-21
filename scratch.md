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

# Sanitization Document for Hierarchy 
The next step is to create a cli command for a work (`<work_file.md>`). This should be implemented in the <<drcli>> and and in a seperate sanitize_commands.py in the cli folder. 

When running `drcli <work_file.md>` it should do the following:
1. Hash the file to ensure that the hash exists in the db and pull out the id of the <<work.py>> in the DB (to be used later)
2. If `<work_file.title_changes.md>` doesn't exist, then using the library of <<suggested_heading_changes.py>> we should generate the file:
   a) if `<work_file.titles.md>` doesn't exist then we should generate that using <<extract_titles_cli.py>>
   b) then run <<suggested_heading_changes.py>> accordingly
   c) if `<work_file.title_changes.md>` exists, we can skip this step and proceed to step 3:
3. Based on `<work_file.title_changes.md>` cop the `<work_file.md>` to `<work_file.sanitized.md>` and for each line make the relevant changes as described in `<work_file.title_changes.md>`:
   a) if `NO_CHANGE` then skip updating that line
   b) if `REMOVE` then remove the heading of that line (**DO NOT REMOVE THE LINE--Just the heading hash**)
   c) if H1 ... H4, change the heading accordingly for example if heading is `## SOME HEADING` but the change is `H1` it should be changed to `# SOME HEADING`
   d) Only adjust the heading hash (remove or adjust--`#`,`##`,`###`,`####`) and **NEVER DELETE OR ADD TO THE DOCUMENT SO THAT THE LINE NUMBERS CONTINUE TO MATCH UP**
4. After completing all the changes suggested in `<work_file.title_changes.md>` we need to update the database for the <<work.py>> model. For the ID saved in step 1, we should do the following:
   a) Update the new `markdown_path` to be the new `<work_file.sanitized.md>`
   b) Update the hash so it's the hash of the new `<work_file.sanitized.md>`

# Small Files -- Sanitize, Biblio, and ToC
Let's create a new module and CLI in `src\psychrag\chunking` that uses the LLM to do the Biblio, ToC, and Sanitization. The idea is that the whole markdown file is passed in to the LLM with a prompt to generate the following:
1) Bibliography
2) Sanitized Version -- the LLM should rewrite the markdown with appropriate headings
   a) H1 for Title
   b) H1 for Top Level Heading
   c) H2 for Sections under H1
   d) H3 for sub-section under H2
3) ToC based on contents (not actual ToC just based on the headings that were parsed)

Use the results from the LLM to do the following:
* Save a new sanitized version of the work to `<work.sanitized.md>` in the output folder
* Generate a new entry in the db for this work
   * Use the results to create the biblio and ToC in the work object
   * Based on the new `<work.sanitized.md>` update the `content_hash` and `markdown_path` in that work object


# Chunking Sanitized Work Part 1 -- determining what to chunk

Next lets create a new process in `src\psychrag\chunking` called `suggested_chunks.py` and it's corresponding cli file `suggested_chunks_cli.py`. This should do the following:
* Input `<work.sanitized.md>` file
* From this we should generate titles for this markdown using <<extract_titles>> into `<work.sanitized.titles.md>`
* We will then pass in the following information into the LLM (light) model with search turned on to try to determine what titles are worth sanitizing:
   * The new titles file (`<work.sanitized.titles.md>`) will be our index to work off of and pass in the titles codeblock into the llm
   * Pass in the bibliographical information on the work
   * Using search, memory, and reasoning, the llm should determine which data in H1 and H2 titles should be chunked and vectorized:
      * For example table of contents (ToC), indexes and references (and reference data) do not need to be chunked and vectorized
      * Important data should be vectorized
      * for each line in the titles codeblock we should get a return like the following: `[line number]: [SKIP | VECTORIZE]
      * The document is a hierarchy so if an `H1` title is set to `SKIP` than all the subordinate titles should be skipped, if on the other hand a single subordinate titles under an `H1` is set to `VECTORIZE` than the it's parent `H1` should be set to `VECTORIZE` as well
      * H1 - H5 is determined from the markdown (`#` = `H1`, `##` = `H2`...)
      * Example if this is the original titles codeblock:
        ```md
        ./book.md

        # All TITLES IN DOC
        10: # Title of the book
        13: # Table of Contents
        18: # Chapter 1
        19: ## Section 1.1
        20: ### Subsection 1.1.1
        ...
        ```

    **THE EXPECTED OUTPUT COULD BE**
        ```md
        # CHANGES TO HEADINGS
        10: SKIP
        13: SKIP
        18: VECTORIZE
        19: VECTORIZE
        20: VECTORIZE
        ...
        ```
   * The output should be saved to the same folder as `work.sanitized.vectorize_suggestions.md`

# Chunking Sanitizing Work Part 2 -- Chunk H1

Now we need to store the H1, H2, H3, H4 chunks into the database. For now, let's create a new object that is related to `src\psychrag\data\models\work.py` object--there will be many `chunk.py` objects for every one `work.py` object and here are the properties is should have:
* id: integer, auto-increment, primary key
* parent_id: integer references id of this object (set to null or -1 if it's an H1 and doesn't have a parent--whatever is best for postgres)
* work_id: integer, foreign key of the id in `work.py`
* level: varchar that will be either `H1 | H2 | H3 | H4 | H5 | sentence | chunk`
* content: TEXT -- the content of the actual chunk
* embedding: vector(768)
* start_line: integer -- the line number where the chunk begins in the markdown file
* end_line: integer -- the line number where the chunk ends in the markdown file
* vector_status: varchar that will be either `no_vec | to_vec | vec`

We should also ensure that an index is created on the embedding like the following:
```
CREATE INDEX ON chunk USING hnsw (embedding vector_cosine_ops);
```

Now I have data in my database, so any updates in `src\psychrag\data\init_db.py` need to be non-destructive, but ideally I want to be able to run it so that the new table is created in the DB without affecting the old one. If the I need to alter the work table, please generate a SQL script for me.

# Chunking Sanitizing Work Par 3 -- Chunk Headings
Now we need to insert all the headings into into `src\psychrag\data\models\chunk.py`. Create a new module and cli script called `chunk_headings.py` and `chunk_headings_cli.py` that does the following:
* Input: ID of the `src\psychrag\data\models\work.py` row in the database
* H1 Chunking First:
    * Lookup the `markdown_path` in the Database for the ID -- this will be `[work].sanitized.md`
    * using `[work].sanitized.md` and `[work].sanitized.vectorize_suggestions.md` do the following:
        * Any H1 marked in `[work].sanitized.vectorize_suggestions.md` as `VECTORIZE` create a new chunk in the the database:
            * parent_id is NULL (since it's an H1)
            * work_id is the `ID` of the input
            * level: `H1`
            * embedding: null
            * vector_status: `no_vec`
            * content: The entire H1 and all it's subheadings and contents:
                * Start: Beginning of the H1 line (include the heading)
                * End: Either until the next H1 or EOF
            * start_line: line number of start
            * end_line: line number of end
* H2 to H5 Chunking:
    * Follow a similar pattern as for H1
    * Start: To determine the beginning of the chunk: Start as the `Hx` including the title just like for H1
    * End: To determine the end for `Hx` will be until we hit another `Hx`, or `H(x+1)` -- a title with the same heading level or higher (or EOF). (BELOW `Hx`)
    * parent_id is the parent of the `Hx` heading--the heading above that is `H(x+1)` -- the higher level heading ABOVE `Hx` -- you can look up the parent_id using `start_line` of the `H(x+1)` heading
* Important start_line will be used often in querying, generate a sql script migration to create an index for it