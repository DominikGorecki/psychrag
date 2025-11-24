"""
Query expansion using Multi-Query Expansion (MQE) and HyDE.

This module expands user queries for better RAG retrieval by generating
alternative queries, hypothetical document answers, and extracting intent/entities.

Usage:
    from psychrag.retrieval.query_expansion import expand_query
    result = expand_query("What is working memory?", n=3)
"""

import json
from dataclasses import dataclass

from psychrag.ai.config import ModelTier
from psychrag.ai.llm_factory import create_langchain_chat
from psychrag.data.database import get_session
from psychrag.data.models import Query


@dataclass
class QueryExpansionResult:
    """Result of query expansion operation."""

    query_id: int
    original_query: str
    expanded_queries: list[str]
    hyde_answer: str
    intent: str
    entities: list[str]


def expand_query(
    query: str,
    n: int = 3,
    verbose: bool = False
) -> QueryExpansionResult:
    """Expand a query using MQE and HyDE with intent/entity extraction.

    Args:
        query: The original user query.
        n: Number of alternative queries to generate (default 3).
        verbose: Whether to print progress information.

    Returns:
        QueryExpansionResult with expanded queries, HyDE answer, intent, entities.

    Raises:
        ValueError: If LLM response cannot be parsed as JSON.
    """
    if verbose:
        print(f"Expanding query: {query}")
        print(f"Generating {n} alternative queries...")

    # Create LangChain chat with FULL model
    langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
    chat = langchain_stack.chat

    # Build the prompt
    prompt = f"""You are a query expansion assistant for a psychology literature RAG system.

Given a user query, you must:
1. Generate {n} alternative phrasings of the query (Multi-Query Expansion)
2. Write a hypothetical answer paragraph that would appear in a psychology textbook (HyDE)
3. Determine the query intent
4. Extract key entities

IMPORTANT: Respond ONLY with valid JSON, no other text.

Query: {query}

Respond with this exact JSON structure:
{{
  "queries": ["alternative query 1", "alternative query 2", ...],
  "hyde_answer": "A detailed hypothetical answer paragraph (2-4 sentences) that would appear in a psychology textbook answering this query...",
  "intent": "DEFINITION | MECHANISM | COMPARISON | APPLICATION | STUDY_DETAIL | CRITIQUE",
  "entities": ["entity1", "entity2", ...]
}}

Intent types:
- DEFINITION: "What is X?"
- MECHANISM: "How does X work?"
- COMPARISON: "Compare X vs Y"
- APPLICATION: "Example of X in real life?"
- STUDY_DETAIL: "What did Study Z find?"
- CRITIQUE: "What are limitations of X?"

Entities include:
- Key names (e.g., Baumeister, Spearman)
- Theory names (e.g., Process Overlap Theory, CHC model)
- Keywords (e.g., negativity bias, working memory capacity)
"""

    # Call the LLM
    if verbose:
        print("Calling LLM...")

    response = chat.invoke(prompt)
    response_text = response.content

    # Parse JSON response
    try:
        # Try to extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")

    expanded_queries = data.get("queries", [])
    hyde_answer = data.get("hyde_answer", "")
    intent = data.get("intent", "")
    entities = data.get("entities", [])

    if verbose:
        print(f"Generated {len(expanded_queries)} alternative queries")
        print(f"Intent: {intent}")
        print(f"Entities: {len(entities)}")

    # Save to database
    with get_session() as session:
        query_record = Query(
            original_query=query,
            expanded_queries=expanded_queries,
            hyde_answer=hyde_answer,
            intent=intent,
            entities=entities,
            vector_status="to_vec"
        )
        session.add(query_record)
        session.commit()
        query_id = query_record.id

        if verbose:
            print(f"Saved to database with ID: {query_id}")

    return QueryExpansionResult(
        query_id=query_id,
        original_query=query,
        expanded_queries=expanded_queries,
        hyde_answer=hyde_answer,
        intent=intent,
        entities=entities
    )
