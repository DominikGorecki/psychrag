"""
Augmented prompt generation for RAG system.

This module generates complete RAG prompts by combining retrieved context
with user queries, instructions, and metadata (intent, entities).

Usage:
    from psychrag.augmentation import generate_augmented_prompt
    
    # Generate prompt for a query
    prompt = generate_augmented_prompt(query_id=1, top_n=5)
    print(prompt)

Functions:
    get_query_with_context(query_id, top_n) - Fetch query with top N contexts from DB
    format_context_blocks(contexts, session) - Format contexts as markdown blocks
    generate_augmented_prompt(query_id, top_n) - Generate complete RAG prompt
"""

from typing import Optional

from sqlalchemy.orm import Session

from ..data.database import get_session
from ..data.models.query import Query
from ..data.models.work import Work


def get_query_with_context(query_id: int, top_n: int = 5) -> tuple[Query, list]:
    """
    Fetch query from database with top N clean retrieval contexts.
    
    Args:
        query_id: ID of the query to fetch
        top_n: Number of top contexts to retrieve (default: 5)
        
    Returns:
        Tuple of (Query object, list of top N context dicts sorted by score)
        
    Raises:
        ValueError: If query_id not found
    """
    with get_session() as session:
        query = session.query(Query).filter(Query.id == query_id).first()
        
        if not query:
            raise ValueError(f"Query with id={query_id} not found")
        
        # Get clean retrieval context and sort by score (descending)
        contexts = query.clean_retrieval_context or []
        
        # Sort by score descending and take top N
        sorted_contexts = sorted(contexts, key=lambda x: x.get('score', 0), reverse=True)
        top_contexts = sorted_contexts[:top_n]
        
        return query, top_contexts


def format_context_blocks(contexts: list, session: Session) -> str:
    """
    Format contexts as markdown blocks with source citations.
    
    Each context is formatted as:
    [S#] Source: {work_title} -- {first_line} | (work_id={id}, start-line={start}, end-line={end})
    Text:
    {remaining_content_trimmed}
    
    Args:
        contexts: List of context dicts with work_id, content, start_line, end_line, score
        session: SQLAlchemy session for querying works
        
    Returns:
        Formatted markdown string with all context blocks
    """
    if not contexts:
        return "(No context available)"
    
    blocks = []
    
    for idx, context in enumerate(contexts, start=1):
        work_id = context.get('work_id')
        content = context.get('content', '')
        start_line = context.get('start_line', 0)
        end_line = context.get('end_line', 0)
        
        # Query work title
        work = session.query(Work).filter(Work.id == work_id).first()
        work_title = work.title if work else f"Unknown Work (id={work_id})"
        
        # Extract first line and remaining content
        lines = content.split('\n', 1)
        first_line = lines[0].strip() if lines else ""
        remaining_content = lines[1].strip() if len(lines) > 1 else ""
        
        # Trim empty lines at top and bottom of remaining content
        remaining_content = remaining_content.strip()
        
        # Format the block
        block = f"""[S{idx}] Source: {work_title} -- {first_line} | (work_id={work_id}, start-line={start_line}, end-line={end_line})
Text:
{remaining_content}"""
        
        blocks.append(block)
    
    return "\n\n".join(blocks)


def generate_augmented_prompt(query_id: int, top_n: int = 5) -> str:
    """
    Generate complete RAG prompt with instructions, context, and question.
    
    This function retrieves a query from the database, formats its retrieved
    contexts, and generates a comprehensive prompt for the LLM that includes:
    - Instructions on how to use the context
    - Formatted context blocks with citations
    - The original user question
    - Intent and entity metadata for guidance
    
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
    
    # Generate the complete prompt using the template
    prompt = f"""You are an academic assistant that answers questions using a set of retrieved source passages
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
    
    return prompt

