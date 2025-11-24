# Retrieval

## Overview

1. **Query Expansion:** Multi Query Expansion (MQE) and Hypothetical Document Embeddings (HyDE)
2. **Understand Intent and Entities:** In the same LLM call as (1) above, also try to understand the intent of the original query and assign keywords/entities to it. 
3. **Generate Query Embeddings:** For all the questions (original + generated) we need to use the same embedding model to generate the embeddings to search in our DB with.
4. **Retrieval:** Dense and Lexical Retrieval (BM25) for candidates that the get combined and run reciprocal rank fusion to keep top candidates. 
5. **Re-Rank:** Run BGE-reranker on `(question, chunk_text) fore relevance score -- pick top results; bias results to intent and entities. 
6. **Context Assembly**: Group by section for any chunks under the same H1, H2, H3, H4... Then order groups by top most relevant (highest) chunk in each group

## Query Expansion and Intent with Entities (LLM FULL Query 1)

### Query Expansion

We expand the original LLM Query (`Q_orig`) for RAG with multi-query expansion (`Q_MQE_1 to Q_MQE_n`) and hypothetical document embeddings (`Q_HyDE`). We can have "n" number of alternative queries for multi-query expansion--the default is 3. One LLM call to the "FULL" version (**not LIGHT**) generates all the additional queries. That is the LLM will generate the following questions based on `Q_orig` if `n=3`: `Q_MQE_1, Q_MQE_2, Q_MQE_3, Q_HyDE.`

### Intent and Entities

This same LLM call should detrmine the intent based on the following list:

* DEFINITION (“What is X?”)
* MECHANISM (“How does X work?”)
* COMPARISON (“Compare X vs Y”)
* APPLICATION (“Example of X in real life?”)
* STUDY/DETAIL (“What did Study Z find?”)

At the same time this same call should also return entities for the given query. Entities are:
* Key names (Baumeister, Spearman, CHC model)
* Theory names (Process Overlap Theory, P-FIT)
* Keywords (negativity bias, working memory capacity)

### Results of the LLM call 

The results should be a JSON that has the new queries, hypothetical answer, intent and entities:

```json
{
  "queries": [...],
  "hyde_answer": "...",
  "intent": "DEFINITION | MECHANISM | COMPARISON | STUDY_DETAIL | APPLICATION | CRITIQUE"
  "entities": [...]
}
```

## Embeddings for Retrieval

Using the same embedding model that we used for our chunks, wee need to generate the 