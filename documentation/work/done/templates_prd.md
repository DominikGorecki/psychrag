# Prompt Templates PRD

This project is about creating templates for  we can modify in the UI. It should work as follows:

* New nav-link to templates page where there is a list of templates with their descriptions and the version that is active
* Thant links to a new page where the active template is shown in a text-input that the user can alter
* Above that, there is a drop-down showing all the active templates and a "Add New" at the top for example:

  * Add New
  * V3: [title of V3]
  * V2: [title of V2]
  * V1: [title of V1]

* If the user selects a new one, they will show a blank page with the ability to add a title

* A new model and table should be created to handle this:
  * associate templates to function by a simple tag like `query_expansion`
  * version should be incremented automatically based on the last version added (highest version number for that function plus one)
  * new migration for table should be added to `/migrations/` folder - use *.sql
  * should be added to `/src/psychrag/data/init_db.py`

* Create templates for the following:
  * Query Expansion (MQE + HyDE) - src/psychrag/retrieval/query_expansion.py
  * RAG Augmented Prompt - src/psychrag/augmentation/augment.py
  * Vectorization Suggestions - src/psychrag/chunking/suggested_chunks.py
  * Heading Hierarchy Corrections - src/psychrag/sanitization/suggest_heading_changes.py
  * Manual ToC Extraction - src/psychrag/conversions/manual_prompt__toc_titles.md (static prompt, no variables)

* Use existing prompts the V1 versions but leave as fallback in case there isn't anything in the DB -- add to migration script
* Use PromptTemplate from langchain_core.prompts
* Keep it simple