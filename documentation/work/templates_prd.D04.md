COMPLETE

# T04: Integrate templates into existing functions with fallback

## Context

- **PRD**: [templates_prd.md](templates_prd.md)
- **PRD Section**: Lines 22-28 (template creation for 4 functions with fallback)
- **User Value**: Enables the system to automatically use user-customized prompt templates from the database when running AI functions, while maintaining backward compatibility with hardcoded prompts as fallback if database templates are unavailable.

## Outcome

The 4 existing prompt-using functions automatically load their active template from the `prompt_templates` table when executed. If no active template is found in the database (or database is unavailable), they fall back to the original hardcoded prompts. Users can customize prompts via the UI and see their changes take effect immediately in subsequent AI operations.

## Scope

**In scope:**
- Modify 4 existing modules to load templates from database:
  1. `src/psychrag/retrieval/query_expansion.py` - Query Expansion
  2. `src/psychrag/augmentation/augment.py` - RAG Augmented Prompt
  3. `src/psychrag/chunking/suggested_chunks.py` - Vectorization Suggestions
  4. `src/psychrag/sanitization/suggest_heading_changes.py` - Heading Hierarchy Corrections
- Create shared helper function for loading templates with fallback
- Use LangChain's `PromptTemplate.from_template()` to convert stored strings to PromptTemplate objects
- Maintain existing function signatures and behavior
- Ensure backward compatibility (no breaking changes)
- Handle database connection failures gracefully
- Add logging for template loading (success/fallback)

**Out of scope:**
- Caching template loads (future optimization)
- Template hot-reloading (changes require new function call)
- Template versioning history tracking at runtime
- Template performance metrics/telemetry
- Template variable validation at runtime (validation happens at save in T02)

## Implementation plan

### Backend

#### 1. Create shared template loader utility

File: `src/psychrag/data/template_loader.py`

This module provides a reusable function for loading templates with fallback:

```python
"""
Template loader utility for prompt templates.

Provides functions to load LangChain PromptTemplates from the database
with fallback to hardcoded defaults.
"""

from typing import Callable
import logging
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from psychrag.data.database import get_session
from psychrag.data.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


def load_template(
    function_tag: str,
    fallback_builder: Callable[[], str]
) -> LCPromptTemplate:
    """
    Load active template from database with fallback.

    This function attempts to load the active template for a given function_tag
    from the database. If no active template is found or if there's a database
    error, it falls back to calling fallback_builder() to get the hardcoded
    template string.

    Args:
        function_tag: The function tag to load (e.g., 'query_expansion')
        fallback_builder: Callable that returns the hardcoded template string

    Returns:
        LangChain PromptTemplate ready for formatting

    Example:
        >>> def get_hardcoded_prompt():
        ...     return "You are an assistant. Query: {query}"
        >>> template = load_template("query_expansion", get_hardcoded_prompt)
        >>> result = template.format(query="test")
    """
    try:
        # Attempt to load from database
        with get_session() as session:
            db_template = session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == function_tag,
                PromptTemplate.is_active == True
            ).first()

            if db_template:
                logger.info(
                    f"Loaded template from database: {function_tag} v{db_template.version}"
                )
                return LCPromptTemplate.from_template(db_template.template_content)

        # No active template found, use fallback
        logger.info(
            f"No active template in database for {function_tag}, using fallback"
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)

    except Exception as e:
        # Database error or other issue, use fallback
        logger.warning(
            f"Failed to load template from database for {function_tag}: {e}. "
            f"Using fallback."
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)
```

**Design notes:**
- `fallback_builder` is a callable (lambda or function) that returns the template string
- This allows lazy evaluation - fallback is only built if needed
- Catches all exceptions to ensure graceful fallback
- Logs template source for debugging

#### 2. Update Query Expansion function

File: `src/psychrag/retrieval/query_expansion.py`

**Changes:**

Add imports:
```python
from psychrag.data.template_loader import load_template
```

Modify `generate_expansion_prompt()` function (currently lines 56-143):

**Before:**
```python
def generate_expansion_prompt(query: str, n: int = 3) -> str:
    """Generate the LLM prompt for query expansion.

    ...
    """
    return f"""You are a query expansion assistant for a psychology...
    ...
    """
```

**After:**
```python
def generate_expansion_prompt(query: str, n: int = 3) -> str:
    """Generate the LLM prompt for query expansion.

    This function creates the prompt text without calling the LLM,
    allowing for manual execution of the prompt.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        query: The original user query.
        n: Number of alternative queries to generate (default 3).

    Returns:
        The complete prompt string to send to an LLM.
    """
    # Define fallback template builder
    def get_fallback_template():
        return """You are a query expansion assistant for a psychology and cognitive science literature RAG system
(textbooks, articles, lecture notes, and research summaries).

Given a user query, you must:
1. Generate {n} alternative phrasings of the query (Multi-Query Expansion).
2. Write a hypothetical answer paragraph that would appear in a psychology textbook (HyDE).
3. Determine the query intent (one label only).
4. Extract key entities (names, theories, key constructs).

CRITICAL FORMAT REQUIREMENTS:
- Respond ONLY with a single valid JSON object.
- No extra text before or after the JSON.
- Use double quotes for all keys and string values.
- Do NOT include comments.
- Do NOT include trailing commas.

User query:
{query}

Your JSON MUST have exactly this structure and keys:

{{
  "queries": ["alternative query 1", "alternative query 2", ...],
  "hyde_answer": "A detailed hypothetical answer paragraph (2-4 sentences) that would appear in a psychology textbook answering this query...",
  "intent": "DEFINITION | MECHANISM | COMPARISON | APPLICATION | STUDY_DETAIL | CRITIQUE",
  "entities": ["entity1", "entity2", ...]
}}

DETAILED INSTRUCTIONS:

1) "queries" (Multi-Query Expansion):
- Generate EXACTLY {n} alternative queries.
- Each query should be 5–15 words.
- Write them as search queries, not full questions (avoid question marks).
- Avoid vague pronouns like "this", "it", "they" that depend on context.
- Make the queries distinct, covering different angles, such as:
  - synonyms and paraphrases,
  - specific theory names or constructs,
  - key researchers or paradigm names,
  - outcomes, mechanisms, or populations involved.
- Focus on psychologically meaningful terms that are likely to appear in headings, abstracts, or key sentences.
- Do NOT answer the question here; these are for retrieval only.

2) "hyde_answer" (Hypothetical Document Embedding – HyDE):
- Write a single paragraph, 2–4 sentences long.
- Tone: neutral, academic, and suitable for a psychology textbook.
- Provide a plausible, high-level answer to the query using established psychological concepts.
- Clearly define key terms and, when appropriate, mention well-known theories or researchers.
- Do NOT refer to "this question", "the user", or the retrieval system.
- Do NOT include citations or references; plain prose only.

3) "intent":
- Choose EXACTLY ONE of the following labels:
  - "DEFINITION"   : The user is asking what something is.
  - "MECHANISM"    : The user is asking how or why something works.
  - "COMPARISON"   : The user is comparing two or more things.
  - "APPLICATION"  : The user is asking for examples or real-world use.
  - "STUDY_DETAIL" : The user is asking about specific study details, results, or methodology.
  - "CRITIQUE"     : The user is asking about limitations, criticisms, or weaknesses.
- If multiple could apply, pick the SINGLE best-fitting label.

4) "entities":
- Return a list of 1–10 key entities.
- Entities can include:
  - researcher names (e.g., "Baumeister", "Spearman"),
  - theory/model names (e.g., "Process Overlap Theory", "CHC model"),
  - core constructs (e.g., "negativity bias", "working memory capacity"),
  - named tasks/paradigms (e.g., "Stroop task", "marshmallow test").
- Avoid generic words like "people", "study", "research" unless they are part of a standard term.
- Prefer concise noun phrases or proper names.
- Do not duplicate entities in the list.

Remember:
- Output MUST be valid JSON matching the schema above.
- Do not include any explanation or commentary outside the JSON."""

    # Load template from database with fallback
    template = load_template("query_expansion", get_fallback_template)

    # Format template with variables
    return template.format(query=query, n=n)
```

**Key changes:**
- Extract hardcoded f-string into `get_fallback_template()` function
- Call `load_template()` with function_tag and fallback
- Use `template.format()` to substitute variables
- Function signature and return type unchanged

#### 3. Update RAG Augmented Prompt function

File: `src/psychrag/augmentation/augment.py`

**Changes:**

Add imports:
```python
from psychrag.data.template_loader import load_template
```

Modify `generate_augmented_prompt()` function (currently lines 160-285):

**Before:**
```python
def generate_augmented_prompt(query_id: int, top_n: int = 5) -> str:
    """Generate complete RAG prompt with instructions, context, and question.
    ...
    """
    # Get query and contexts
    query, top_contexts = get_query_with_context(query_id, top_n)

    # Extract query data
    user_question = query.original_query
    intent = query.intent or "GENERAL"
    entities = query.entities or []

    # Format entities as comma-separated string
    if isinstance(entities, list):
        entities_str = ", ".join(str(e) for e in entities) if entities else "None specified"
    else:
        entities_str = str(entities) if entities else "None specified"

    # Format context blocks
    with get_session() as session:
        context_blocks = format_context_blocks(top_contexts, session)

    # Generate the complete prompt using the template
    prompt = f"""You are an academic assistant that answers questions using a set of retrieved source passages
plus your own general knowledge when appropriate.
...
{context_blocks}
...
{user_question}
"""

    return prompt
```

**After:**
```python
def generate_augmented_prompt(query_id: int, top_n: int = 5) -> str:
    """Generate complete RAG prompt with instructions, context, and question.

    This function retrieves a query from the database, formats its retrieved
    contexts, and generates a comprehensive prompt for the LLM that includes:
    - Instructions on how to use the context
    - Formatted context blocks with citations
    - The original user question
    - Intent and entity metadata for guidance

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        query_id: ID of the query in the database
        top_n: Number of top contexts to include (default: 5)

    Returns:
        Complete formatted prompt string ready for LLM

    Raises:
        ValueError: If query_id not found in database

    Example:
        >>> prompt = generate_augmented_prompt(query_id=42, top_n=5)
        >>> print(prompt)
        You are an academic assistant...
    """
    # Get query and contexts
    query, top_contexts = get_query_with_context(query_id, top_n)

    # Extract query data
    user_question = query.original_query
    intent = query.intent or "GENERAL"
    entities = query.entities or []

    # Format entities as comma-separated string
    if isinstance(entities, list):
        entities_str = ", ".join(str(e) for e in entities) if entities else "None specified"
    else:
        entities_str = str(entities) if entities else "None specified"

    # Format context blocks
    with get_session() as session:
        context_blocks = format_context_blocks(top_contexts, session)

    # Define fallback template builder
    def get_fallback_template():
        return """You are an academic assistant that answers questions using a set of retrieved source passages
plus your own general knowledge when appropriate.

Your job is to:
1. Read and understand the source passages in the CONTEXT section below.
2. Answer the user's question as accurately and clearly as possible.
3. Clearly distinguish between:
   - Information that is directly supported by the provided sources.
   - Information that comes from your broader academic knowledge but is NOT explicitly in the sources.
4. Explicitly reference which source passages you are using, with the keys [S1], [S2], etc.

HYBRID EVIDENCE POLICY (VERY IMPORTANT)
- PRIMARY: Treat the provided sources as the main evidence base.
- SECONDARY: You MAY use general academic knowledge, but:
  - Only if it is standard and non-controversial in the relevant field.
  - You MUST clearly separate it from what is supported by the sources.
- If the sources do not contain enough information to fully answer the question:
  - Say what can be concluded from the sources.
  - Then optionally add a clearly marked section with general knowledge and search.

CITATION RULES
- Each context block below is tagged with a label like [S1], [S2], etc.
- Each block may also include metadata such as work_id, start_line and end_line in parentheses.
  Example header:
    [S1] Source: Some Book Title -- section title | (work_id=123, start_line=23, end_line=32)
- When you make a claim that is supported by one or more sources:
  - Add the relevant source labels at the end of the sentence or paragraph, e.g. [S1], [S1][S3].
  - Do NOT invent new source labels beyond those given.
  - Do NOT cite work_id or start_line or end_line directly in the prose; just use [S#].
- Our system will later map [S#] back to work_id, start_line, and end_line for linking to the original content.

STRUCTURE YOUR ANSWER AS FOLLOWS
1. **Answer**
   - Provide a direct, well-organized answer to the question.
   - Use citations [S#] whenever you rely on information from the sources.
   - If multiple sources contribute to a point, cite each of them.
2. **Explanation and Details**
   - Expand on key concepts, mechanisms, comparisons, or study details.
   - Group related ideas logically (e.g., definitions, mechanisms, evidence, limitations).
   - Continue to use [S#] citations where appropriate.
3. **From General Knowledge or Search (Outside Provided Sources)** (optional)
   - Only include this section if you add material that is NOT clearly supported by the sources.
   - Clearly mark that this section is based on your broader academic knowledge or search.
   - Do NOT attach [S#] citations to statements in this section.
4. **Sources Used**
   - List the source labels you actually relied on in your answer, e.g.:
     - Sources used: [S1], [S3], [S5]

INTENT AND ENTITIES (GUIDANCE ONLY)
- The question intent type is: {intent}
  Possible values include: DEFINITION, MECHANISM, COMPARISON, APPLICATION, STUDY_DETAIL, CRITIQUE.
- Key entities and concepts for this question are:
  {entities_str}

Use this information to shape your answer style:
- DEFINITION: Start with a clear definition, then elaborate.
- MECHANISM: Focus on explaining processes, causes, and "how/why".
- COMPARISON: Explicitly compare similarities and differences between entities.
- APPLICATION: Emphasize examples and real-world implications.
- STUDY_DETAIL: Highlight study design, samples, methods, and key findings.
- CRITIQUE: Emphasize limitations, criticisms, and alternative interpretations.

TONE AND STYLE
- Write in a clear, academic style suitable for an advanced student or researcher.
- Define technical terms when they first appear, if the context does not already define them.
- Do not simply repeat large chunks of the sources; synthesize and explain them.
- If the sources disagree or present multiple perspectives, acknowledge this explicitly.

============================================================
CONTEXT (RETRIEVED SOURCE PASSAGES)
Each block is labeled [S#] and may include work_id and parent_id metadata
that our system uses to link back to the original document.

{context_blocks}
============================================================

USER QUESTION
{user_question}
"""

    # Load template from database with fallback
    template = load_template("rag_augmentation", get_fallback_template)

    # Format template with variables
    return template.format(
        intent=intent,
        entities_str=entities_str,
        context_blocks=context_blocks,
        user_question=user_question
    )
```

#### 4. Update Vectorization Suggestions function

File: `src/psychrag/chunking/suggested_chunks.py`

**Changes:**

Add imports:
```python
from psychrag.data.template_loader import load_template
```

Modify `_build_prompt()` function (currently lines 43-212):

**Note**: This function has a `bib_info` parameter that is optionally used to build a `bib_section` string. The template needs to handle this conditional section.

**Strategy**: Include `{bib_section}` as a template variable, and pass it as empty string if bib_info is None.

**Before:**
```python
def _build_prompt(titles_content: str, bib_info: BibliographicInfo | None) -> str:
    """Build the LLM prompt for analyzing titles.
    ...
    """
    bib_section = ""
    if bib_info:
        bib_parts = []
        if bib_info.title:
            bib_parts.append(f"Title: {bib_info.title}")
        # ... build bib_section
        if bib_section:
            bib_section = "## Bibliographic Information\n" + "\n".join(bib_parts) + "\n\n"

    prompt = f"""You are analyzing a document's heading structure...
    {bib_section}## Document Headings

    {titles_content}
    ...
    """

    return prompt
```

**After:**
```python
def _build_prompt(titles_content: str, bib_info: BibliographicInfo | None) -> str:
    """Build the LLM prompt for analyzing titles.

    This function creates the prompt for the LLM to analyze document headings
    and suggest which sections to vectorize.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        titles_content: The titles codeblock content.
        bib_info: Optional bibliographic information about the work.

    Returns:
        Formatted prompt string.
    """
    # Build bibliographic section if available
    bib_section = ""
    if bib_info:
        bib_parts = []
        if bib_info.title:
            bib_parts.append(f"Title: {bib_info.title}")
        if bib_info.authors:
            bib_parts.append(f"Authors: {', '.join(bib_info.authors)}")
        if hasattr(bib_info, 'publication_date') and bib_info.publication_date:
            bib_parts.append(f"Publication Date: {bib_info.publication_date}")
        if hasattr(bib_info, 'year') and bib_info.year:
            bib_parts.append(f"Year: {bib_info.year}")
        if bib_info.publisher:
            bib_parts.append(f"Publisher: {bib_info.publisher}")
        if bib_parts:
            bib_section = "## Bibliographic Information\n" + "\n".join(bib_parts) + "\n\n"

    # Define fallback template builder
    def get_fallback_template():
        return """You are analyzing a document's heading structure to determine which sections contain valuable content worth vectorizing for a RAG (Retrieval Augmented Generation) system. Your goal is to include headings whose underlying sections contain explanatory, conceptual, or narrative content, and to exclude purely structural, navigational, or index-like sections.

{bib_section}## Document Headings

{titles_content}

## Task

For each heading line number, determine whether it should be:

* **VECTORIZE**: The section under this heading likely contains meaningful prose or explanatory content that would help answer questions about the document's subject matter.
* **SKIP**: The section is primarily structural, navigational, index-like, or otherwise not useful as semantic knowledge for RAG.

## Decision Strategy

First, classify each heading based on its title. Then, enforce hierarchy rules so that parent headings are consistent with their children.

### A. Hierarchy rules

* Infer heading levels from markdown markers ("#", "##", "###", etc.) and/or numbering (e.g., "1.", "1.1.", "2.3.4").
* If any sub-heading is **VECTORIZE**, all of its ancestor headings (its parent, the parent's parent, etc.) MUST also be **VECTORIZE**.
* If a high-level heading looks structural (e.g., "Appendices", "Back Matter") but has child headings that clearly describe substantive content (e.g., "Appendix A: Experimental Stimuli"), treat those child headings and their ancestors as **VECTORIZE**.
* Do NOT force children to SKIP just because a parent is SKIP; children can still be **VECTORIZE** if they look like substantive content sections.

### B. Content to SKIP (structural / non-semantic)

Mark a heading as **SKIP** when it clearly indicates one of the following:

* Table of contents and navigation:

  * "Contents", "Table of Contents", "Detailed Contents", "List of Chapters"
  * "List of Figures", "List of Tables", "List of Boxes", "List of Abbreviations", "List of Acronyms"
* Indexes:

  * "Index", "Subject Index", "Author Index", "Name Index"
* References and bibliographic material:

  * "References", "Reference List", "Bibliography", "Works Cited", "Notes" / "Endnotes" sections that are primarily citation notes
* Pure front matter:

  * "Title Page", "Copyright", "Imprint", "Publication Data", "Dedication"
  * "Acknowledgments" / "Acknowledgements", "About the Author", "Foreword" (unless clearly domain-explanatory)
* Pure back matter or raw reference material:

  * Headings that obviously denote only raw data, item lists, or mechanical material such as:

    * "Data Tables", "Codebook", "Questionnaire Items", "Survey Items", "Answer Key"
    * "Appendix: Tables", "Appendix: Data", "Appendix: Raw Scores"
* Any heading that is clearly just a navigation/structure label with no real prose under it (e.g., "Part I", "Section I" by itself), **unless** its children are VECTORIZE (in which case the parent must also be VECTORIZE).

Only mark a heading as **SKIP** if it is very likely to be structurally / mechanically focused rather than explanatory content.

### C. Content to VECTORIZE (semantic / explanatory)

Mark a heading as **VECTORIZE** when the section under it is likely to contain any of the following:

* Core chapters and numbered sections that present the main subject matter.

  * e.g., "Chapter 1: Introduction to Cognitive Psychology", "2.3 Working Memory Capacity"
* Sections that define, explain, or discuss concepts, theories, models, mechanisms, or arguments.

  * e.g., "Theories of Intelligence", "Reinforcement Learning", "Social Identity Theory"
* Sections that describe methods, procedures, or empirical findings in a way that could answer user questions.

  * e.g., "Method", "Participants", "Procedure", "Results", "Discussion", "Implications", "Limitations"
* Sections that summarize, synthesize, or generalize information.

  * e.g., "Summary", "Conclusion", "General Discussion", "Practical Applications", "Future Directions"
* Worked examples, case studies, and explanatory exercises that teach or illustrate concepts.

  * e.g., "Case Study: Phineas Gage", "Example Problems", "Worked Example"
* Appendices that look conceptual or explanatory rather than purely tabular / raw data.

  * e.g., "Appendix A: Mathematical Derivation", "Appendix B: Scale Construction and Interpretation"

When in doubt, if a heading sounds like it could contain substantive explanatory text that would help answer questions about the topic, prefer **VECTORIZE** over **SKIP**.

## Output Format

Return ONLY a list in this exact format, one line per heading, preserving the original order of headings:

```
[line_number]: [SKIP|VECTORIZE]
```

Example:

```
10: SKIP
13: SKIP
18: VECTORIZE
19: VECTORIZE
20: VECTORIZE
```

Do NOT include any other commentary, explanations, or text. Analyze the headings and provide only your final SKIP/VECTORIZE labels:"""

    # Load template from database with fallback
    template = load_template("vectorization_suggestions", get_fallback_template)

    # Format template with variables
    return template.format(
        bib_section=bib_section,
        titles_content=titles_content
    )
```

#### 5. Update Heading Hierarchy Corrections function

File: `src/psychrag/sanitization/suggest_heading_changes.py`

**Changes:**

Add imports:
```python
from psychrag.data.template_loader import load_template
```

Modify `_build_prompt()` function (currently lines 203-328):

**Before:**
```python
def _build_prompt(title: str, authors: str, toc: list, titles_codeblock: str) -> str:
    """Build the prompt for the LLM."""

    # Format ToC for the prompt
    toc_text = ""
    if toc:
        toc_lines = []
        for item in toc:
            level = item.get('level', 1)
            item_title = item.get('title', '')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}Level {level}: {item_title}")
        toc_text = "\n".join(toc_lines)
    else:
        toc_text = "No table of contents available"

    return f"""You are an expert at analyzing document structure...
    ...
    """
```

**After:**
```python
def _build_prompt(title: str, authors: str, toc: list, titles_codeblock: str) -> str:
    """Build the prompt for the LLM.

    This function creates the prompt for the LLM to analyze document headings
    and suggest hierarchy corrections.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        title: Document title
        authors: Document authors
        toc: Table of contents as list of dicts
        titles_codeblock: The titles content from extracted file

    Returns:
        Formatted prompt string
    """

    # Format ToC for the prompt
    toc_text = ""
    if toc:
        toc_lines = []
        for item in toc:
            level = item.get('level', 1)
            item_title = item.get('title', '')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}Level {level}: {item_title}")
        toc_text = "\n".join(toc_lines)
    else:
        toc_text = "No table of contents available"

    # Define fallback template builder
    def get_fallback_template():
        return """You are an expert at analyzing document structure and markdown formatting.

## Task
Analyze the headings from a markdown document and assign the correct heading levels so that:
- The overall structure is consistent with the document's table of contents (ToC)
- The hierarchy is as informative as possible for chunking and context
- No meaningful heading information from the current document is lost

## Document Information
- **Title:** {title}
- **Author(s):** {authors}

## Table of Contents from Database (authoritative high-level structure)
Use this ToC as the primary guide for:
- Overall ordering of sections
- Canonical wording of titles when possible
- The *relative* depth of major parts/chapters/sections

{toc_text}

## Current Headings in Document
Each line shows: [line_number]: [current_heading]
```

{titles_codeblock}

```

## Heading Hierarchy Rules
Treat markdown heading levels as a strict outline hierarchy:

- **H1 (#)**: Main parts, chapters, or major top-level sections
  - Usually mapped from top-level ToC entries
- **H2 (##)**: Sections within a part/chapter
- **H3 (###)**: Subsections
- **H4 (####)**: Sub-subsections (use for additional nesting; do not go deeper than H4)
- **REMOVE**: Only for non-semantic items that clearly are *not* headings
  (e.g., page numbers, running headers/footers, repeated book title on every page, copyright notices)
- **NO_CHANGE**: Heading level is already correct, but you may still normalize the title text

The hierarchy must be *nested and consistent*:
- Do not jump levels in a way that breaks outline logic (avoid H1 → H4 with no H2/H3 in between unless structure clearly demands it)
- Preserve the reading order of the original headings; do not reorder anything

## ToC vs Current Headings (VERY IMPORTANT)
The ToC from the database may be *shallower* (fewer levels) than the actual document headings. Handle this as follows:

1. **ToC as anchor, headings add detail**
   - Use the ToC to determine:
     - Which headings are major (H1) vs subordinate (H2–H4)
     - The canonical wording of titles where there is a clear match
   - Use the current headings to *refine and deepen* the structure under those ToC entries.

2. **Do NOT discard real structure just because ToC is shallow**
   - If the ToC only has chapter-level entries but the document headings clearly contain sections/subsections:
     - Map the chapter to **H1**
     - Map its internal headings to **H2/H3/H4** while preserving their relative nesting.
   - Do **not** REMOVE a heading solely because it is missing in the ToC.

3. **Relative hierarchy preservation**
   - When aligning to the ToC, preserve the *relative* nesting of headings:
     - Example rule: if for a group of headings the original levels are (H2, H3, H4) and you determine that the first one should actually be H1 (because it matches a top-level ToC entry), then the group should become (H1, H2, H3).
   - More generally:
     - If you "promote" or "demote" one heading to align with the ToC, apply the same offset to its direct descendants so that the internal structure under it stays the same.

4. **Matching titles**
   - If a heading clearly corresponds to a ToC entry:
     - Use the ToC title text as the authoritative `title_text` (fixing capitalization, punctuation, numbering if needed).
   - If there is no clear ToC match:
     - Keep the best, cleaned-up version of the current heading text as `title_text`, and assign a level (H1–H4) based on context.

5. **Special sections**
   - Common structural sections like "Foreword", "Preface", "Introduction", "Conclusion", "Appendix", "References", "Bibliography", "Glossary", "Index" should usually be kept as headings (often H1 or H2) unless they are clearly decorative repetitions.

## Instructions
1. Use your knowledge of this work (if you recognize it) to understand its typical structure.
2. If helpful, search the web for information about this specific work's structure (e.g., canonical chapter layout).
3. Compare the ToC from the database with the current headings:
   - Use text similarity, numbering patterns (e.g., "1.", "1.1"), and ordering to align them.
4. For **each line number** in the headings list:
   - Decide whether to assign H1, H2, H3, H4, NO_CHANGE, or REMOVE.
   - When in doubt between flattening or preserving additional structure, prefer preserving a *richer* and *consistent* hierarchy (i.e., more granularity, not less).
5. Do **not** suggest removing lower-level headings that are missing from the ToC. Instead:
   - Keep them, assign the best-fitting level (H2–H4), and maintain their relative position and nesting under the closest higher-level ToC-aligned parent.

## Output Format
Return **only** the mapping in the following format, one line **per heading line**:

[line_number] : [ACTION] : [title_text]

Where:
- `ACTION` is one of: `NO_CHANGE`, `REMOVE`, `H1`, `H2`, `H3`, `H4`
- `title_text` is:
  - The canonical title from the ToC, when there is a clear match, or
  - A cleaned-up version of the current heading text, when there is no ToC match
  - Empty only for `REMOVE`

Notes:
- Even for `NO_CHANGE`, still provide the authoritative `title_text` (which may normalize spacing/capitalization/numbering).
- Do **not** output anything other than these lines.

### Example
10 : NO_CHANGE : Introduction
13 : H1 : Chapter 1: Getting Started
18 : H1 : Methods
19 : H2 : Data Collection
20 : H3 : Survey Design
25 : REMOVE :

Provide the complete list of mappings for **all** headings shown above."""

    # Load template from database with fallback
    template = load_template("heading_hierarchy", get_fallback_template)

    # Format template with variables
    return template.format(
        title=title,
        authors=authors,
        toc_text=toc_text,
        titles_codeblock=titles_codeblock
    )
```

### Other / cross-cutting

**Logging:**
- Template loader logs template source (database or fallback)
- Use existing Python logging module
- Log level: INFO for normal operation, WARNING for fallback due to errors

**Error handling:**
- Database connection failures gracefully fall back to hardcoded templates
- Template formatting errors (missing variables) will raise exceptions - caught by caller
- No silent failures - all errors are logged

**Performance:**
- Each function call loads template fresh from database (no caching in this ticket)
- Database query is simple indexed lookup (fast)
- Future optimization: cache templates in memory with TTL

**Backward compatibility:**
- Function signatures unchanged
- Return types unchanged
- Behavior unchanged when database has no templates
- Existing tests should pass without modification

## Unit tests

**Target**: Tests for each modified module

### 1. Test template_loader.py

File: `tests/unit/test_template_loader.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from psychrag.data.template_loader import load_template


def test_load_template_from_database(session):
    """Test loading active template from database."""
    from psychrag.data.models.prompt_template import PromptTemplate

    # Create active template in database
    template = PromptTemplate(
        function_tag="test_function",
        version=1,
        title="Test Template",
        template_content="Test prompt with {variable}",
        is_active=True
    )
    session.add(template)
    session.commit()

    # Load template
    result = load_template("test_function", lambda: "Fallback {variable}")

    # Should load from database
    assert result is not None
    formatted = result.format(variable="value")
    assert "Test prompt with value" in formatted


def test_load_template_fallback_when_no_active(session):
    """Test fallback when no active template in database."""
    from psychrag.data.models.prompt_template import PromptTemplate

    # Create inactive template
    template = PromptTemplate(
        function_tag="test_function",
        version=1,
        title="Test Template",
        template_content="Test prompt with {variable}",
        is_active=False
    )
    session.add(template)
    session.commit()

    # Load template
    result = load_template("test_function", lambda: "Fallback {variable}")

    # Should use fallback
    formatted = result.format(variable="value")
    assert "Fallback value" in formatted


def test_load_template_fallback_on_db_error():
    """Test fallback when database connection fails."""
    with patch('psychrag.data.template_loader.get_session') as mock_session:
        mock_session.side_effect = Exception("DB connection failed")

        # Load template
        result = load_template("test_function", lambda: "Fallback {variable}")

        # Should use fallback
        formatted = result.format(variable="value")
        assert "Fallback value" in formatted
```

### 2. Test modified functions

For each of the 4 modified functions, add tests to verify:

**Example for query_expansion:**

File: `tests/unit/test_query_expansion_integration.py`

```python
import pytest
from psychrag.retrieval.query_expansion import generate_expansion_prompt
from psychrag.data.models.prompt_template import PromptTemplate


def test_generate_expansion_prompt_uses_database_template(session):
    """Test that generate_expansion_prompt uses database template when available."""
    # Create custom template
    template = PromptTemplate(
        function_tag="query_expansion",
        version=2,
        title="Custom Query Expansion",
        template_content="CUSTOM TEMPLATE: Query is {query}, n is {n}",
        is_active=True
    )
    session.add(template)
    session.commit()

    # Generate prompt
    result = generate_expansion_prompt("test query", n=5)

    # Should use custom template
    assert "CUSTOM TEMPLATE" in result
    assert "test query" in result
    assert "5" in result


def test_generate_expansion_prompt_fallback(session):
    """Test that generate_expansion_prompt uses fallback when no DB template."""
    # No active template in database

    # Generate prompt
    result = generate_expansion_prompt("test query", n=3)

    # Should use hardcoded fallback
    assert "You are a query expansion assistant" in result
    assert "test query" in result


def test_generate_expansion_prompt_signature_unchanged():
    """Test that function signature is unchanged (backward compatibility)."""
    # Should work with same parameters as before
    result = generate_expansion_prompt("test query")
    assert isinstance(result, str)
    assert len(result) > 0

    result2 = generate_expansion_prompt("another query", n=5)
    assert isinstance(result2, str)
```

**Repeat similar tests for:**
- `test_augment_integration.py` - test `generate_augmented_prompt()`
- `test_suggested_chunks_integration.py` - test `_build_prompt()`
- `test_suggest_heading_changes_integration.py` - test `_build_prompt()`

### 3. Integration test with end-to-end flow

File: `tests/integration/test_template_e2e.py`

```python
def test_full_template_workflow(session):
    """Test full workflow: create template, use it in function, verify output."""
    from psychrag.data.models.prompt_template import PromptTemplate
    from psychrag.retrieval.query_expansion import generate_expansion_prompt

    # 1. Create custom template
    custom_template = PromptTemplate(
        function_tag="query_expansion",
        version=10,
        title="E2E Test Template",
        template_content="E2E TEST MARKER: {query} with {n} alternatives",
        is_active=True
    )
    session.add(custom_template)
    session.commit()

    # 2. Call function
    result = generate_expansion_prompt("cognitive load", n=3)

    # 3. Verify custom template was used
    assert "E2E TEST MARKER" in result
    assert "cognitive load" in result
    assert "3" in result
```

## Manual test plan

After implementing this ticket:

### 1. Verify fallback behavior (no database templates)

**Setup:** Start with fresh database (before running T01 migration)

1. Call each of the 4 functions programmatically
2. **Verify:** Functions return prompts (fallback to hardcoded)
3. **Verify:** Logs show "No active template in database, using fallback"

**Commands:**
```python
from psychrag.retrieval.query_expansion import generate_expansion_prompt
prompt = generate_expansion_prompt("test query", n=3)
print("Fallback works!" if "You are a query expansion assistant" in prompt else "FAILED")
```

### 2. Verify database template loading

**Setup:** Run T01 migration to seed V1 templates

1. Call each of the 4 functions
2. **Verify:** Functions return prompts using database templates
3. **Verify:** Logs show "Loaded template from database: {function_tag} v1"

**Commands:**
```python
from psychrag.retrieval.query_expansion import generate_expansion_prompt
prompt = generate_expansion_prompt("test query", n=3)
# Should still work, but may use DB template if available
print(prompt[:100])
```

### 3. Verify custom template usage (via UI)

**Setup:** Complete T02 (API) and T03 (UI)

1. Navigate to Settings > Templates
2. Edit "Query Expansion" template
3. Change first line to: "CUSTOM VERSION: You are a query expansion assistant..."
4. Save changes
5. Run query expansion via CLI or API
6. **Verify:** Generated prompt contains "CUSTOM VERSION"

**Commands:**
```python
from psychrag.retrieval.query_expansion import expand_query
result = expand_query("working memory", n=3)
# Check internal logs or add debug print to see prompt used
```

### 4. Test all 4 functions

Repeat steps 1-3 for:
- RAG Augmented Prompt (use `generate_augmented_prompt()`)
- Vectorization Suggestions (use `suggest_chunks_from_work()`)
- Heading Hierarchy Corrections (use `suggest_heading_changes_from_work()`)

### 5. Test error recovery

1. Stop PostgreSQL database
2. Call `generate_expansion_prompt()`
3. **Verify:** Function succeeds (uses fallback)
4. **Verify:** Logs show warning about database connection failure
5. Restart database
6. Call function again
7. **Verify:** Function uses database template (recovery works)

### 6. Test variable substitution

1. Create template with missing variable (e.g., remove `{query}` from query_expansion template)
2. Call `generate_expansion_prompt()`
3. **Verify:** Function raises error (or returns malformed prompt)
4. **Note:** This validates that T02's validation is important

## Dependencies and sequencing

**Depends on:**
- T01 (Database schema) - MUST be completed first (needs table and model)

**Does NOT block:**
- T02 or T03 - those are independent

**Recommended sequence:**
- Implement after T01 is complete and tested
- Can be tested independently before UI exists
- Provides immediate value (templates from DB work even without UI)

## Clarifications and assumptions

### Assumptions made:

1. **No template caching**: Templates are loaded fresh from database on each function call - acceptable performance cost for this ticket - **CLARIFY**: Should we implement in-memory caching with TTL?

2. **Fallback always available**: Hardcoded fallback templates remain in code indefinitely (not removed after database is seeded) - **CONFIRM**: This is correct for reliability?

3. **No version pinning**: Functions always use the "active" template, regardless of version number - users control which version is active via UI - **CONFIRM**: No need for functions to specify version?

4. **Variable validation at runtime**: No upfront validation that template contains required variables - errors will occur at format() time - **CONFIRM**: Acceptable? Or should load_template() validate variables?

5. **Template format validation**: Relying on LangChain's `from_template()` to validate format - if template is malformed, function will fail - **CONFIRM**: Acceptable? Should we add try/except around format()?

6. **Logging verbosity**: INFO level logs for template loading - may be noisy in production - **CLARIFY**: Should this be DEBUG level instead?

7. **Backward compatibility requirement**: Existing code that imports these functions should work unchanged - **CONFIRM**: This is critical for this ticket?

8. **No migration for existing data**: Functions immediately start using database templates after T01 migration - no gradual rollout or feature flag - **CONFIRM**: Direct cutover is acceptable?

9. **Template variable names**: Database templates must use exact same variable names as original f-strings (e.g., `{query}`, `{n}` for query_expansion) - **CONFIRM**: Variable names are part of contract?

10. **Bib_section handling**: For vectorization_suggestions, bib_section is pre-built and passed as a template variable (empty string if no bib_info) - **CONFIRM**: This approach works?

### Blocking questions:

**NONE** - Can proceed with implementation. Validate assumptions during code review and testing.

---

**Before implementing, review the Clarifications and assumptions section with the product owner. If any blocking item is unresolved, get explicit answers or update the ticket accordingly before writing code.**
