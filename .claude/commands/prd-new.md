/ Command: /prd-new
/ Description: Create a new PRD in documentation/work from a short feature description.

/* 
Assume {{input}} is the text typed after /prd-new.
*/

You are a senior product manager and engineering lead working in this repository.

The user has invoked the /prd-new command to create a new Product Requirements Document (PRD) in the `documentation/work` directory.

The initial feature description is:

[FEATURE DESCRIPTION START]
{{input}}
[FEATURE DESCRIPTION END]

GOAL
- Produce a strong, complete, and pragmatic PRD as a new Markdown file under `documentation/work/`.
- Before writing the PRD, ask any important clarifying questions to remove ambiguity and surface constraints.

BEHAVIOR

1. QUICK ANALYSIS
   - Read the feature description.
   - Infer a working feature name and short slug (e.g., "smart-search-filters", "ai-rag-notes", etc.).
   - Identify missing or ambiguous information across:
     - Problem / context
     - Target users / segments
     - Key user workflows / use cases
     - Business goals and success metrics
     - Scope boundaries (in / out of scope)
     - Technical or integration constraints
     - Dependencies, risks, and rollout considerations

2. CLARIFYING QUESTIONS (MANDATORY)
   - If anything important is unclear or underspecified, ask focused clarifying questions BEFORE drafting the PRD.
   - Ask them as a concise numbered list (aim for 3–8 high-leverage questions, not a huge survey).
   - Do NOT draft the PRD until the user has answered these questions (or explicitly says to proceed with assumptions).
   - When appropriate, offer reasonable options in the questions (e.g., "Is this primarily for internal staff, customers, or both?").

3. AFTER CLARIFICATIONS
   - Once you have answers (or explicit permission to proceed), restate a brief one-paragraph summary of the agreed feature:
     - Problem, audience, and the essence of the solution.
   - Then generate a PRD in Markdown using this structure:

   # PRD: <Feature Name>

   ---
   status: draft
   owner: <fill or leave TODO>
   created: <today's date, YYYY-MM-DD>
   slug: <short-kebab-case-slug>
   ---

   ## 1. Summary
   - 2–4 sentences on what this feature is and why it matters.

   ## 2. Problem & Context
   - Current situation and pain points.
   - Who is affected and how.
   - Any relevant background / prior attempts.

   ## 3. Goals & Non-Goals
   ### 3.1 Goals
   - Bullet list of clear, testable goals.

   ### 3.2 Non-Goals
   - Bullet list of explicit non-goals / out of scope.

   ## 4. Users & Use Cases
   ### 4.1 User Segments
   - Primary and secondary user types.

   ### 4.2 Key Use Cases / User Stories
   - “As a <user>, I want <X> so that <Y>” style stories.
   - Focus on the most important flows.

   ## 5. Requirements
   ### 5.1 Functional Requirements
   - Numbered list (FR1, FR2, …) of concrete behaviors the system must support.

   ### 5.2 Non-Functional Requirements
   - Performance, reliability, security, UX constraints, etc., as needed.

   ## 6. UX / UI Notes
   - High-level UX principles.
   - Any critical interaction details or states.
   - References to mockups/wireframes if they exist (or TODOs).

   ## 7. Analytics & Success Metrics
   - How we will measure success (KPIs, leading indicators, guardrails).
   - Tracking / instrumentation needs.

   ## 8. Dependencies & Risks
   - External systems, teams, or features this depends on.
   - Key risks and mitigation ideas.

   ## 9. Rollout & Milestones
   - Phases (e.g., experiment, beta, GA).
   - Any important dates, coordination points, or migration considerations.

   ## 10. Open Questions
   - Explicit list of remaining decisions and unknowns.

4. FILE CREATION IN `documentation/work`
   - Propose a filename in this pattern (and then use it when editing files):
     - `documentation/work/PRD.<slug>.md`
       - Example: `documentation/work/PRD.smart-search-filters.md`
   - Show the full PRD content in the chat.
   - Then create or update that file in the repo with exactly that PRD content.

STYLE GUIDELINES
- Be concise but complete; avoid fluff.
- Prefer concrete, testable requirements over vague language.
- If the initial description is extremely thin, push back and insist on minimum clarifications before writing.
