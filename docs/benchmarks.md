# Retrieval questions and evidence scoring

## Collections

| Collection | Questions | Relationships |
|---|---:|---|
| Literature | 360 language texts | 180 query versions, each in English and Chinese; 120 base questions and 60 derived variants |
| Standards main set | 80 English queries | Four task types, 20 queries per type |
| Standards paired set | 80 language texts | 40 pairs, each asked in its source language and English |

Literature tasks are A (within-paper evidence), B1 (method discovery under specified
conditions), B2 (exploratory discovery with incomplete conditions), and C (known-method
source tracing). Standards task types are T1 (explicit requirements), T2 (applicability
conditions), T3 (engineering guidance), and T4 (comparison across sources).

Paired languages are Chinese, German, Korean, Vietnamese, Portuguese, Spanish,
Norwegian and Swedish. Each has five source-language/English pairs. English versions
target the same original-language material. These are distinct from the 80-query main
set and must not be pooled as independent questions.

`base_query_id` links literature variants. `pair_id` links paired-language queries.
Related variants and translations are not independent test cases. The questions
were used in the study and are not offered as a newly unseen test set.

## Files and source access

Each question file contains a `questions` list. Rubrics contain only query IDs,
answer-pool status, groups, parent information needs, compatible alternatives,
component IDs and source locators. Researcher notes, review discussions, source
passages and generated answers are omitted.

Match a rubric to its question using `query_id`; language versions can share one
rubric. Within each group, `points` identifies parent needs, and each alternative's
`components` maps those parents to child components and their supporting evidence
locators. Names such as `need_1` are structural identifiers, not answer text. To
interpret a scoring point, consult the question and the referenced evidence; these
identifiers alone do not specify a semantic answer.

Source files contain bibliographic identifiers and document hashes where available.
A physical PDF
page is counted from one, including cover pages. Locators such as
`SOURCE:p0005:c000123-000456:HASH` identify character intervals in the text extraction
used for the study. The character offsets are zero-based, start-inclusive and
end-exclusive; they are not PDF byte offsets. Different text extraction can require
re-establishing the correspondence locally. PDF hashes identify editions; a hash
does not grant access to or redistribution rights over the document.

The literature source list contains 100 documents. The standards source list has
20 language-specific assets representing 19 standards/guidance sources. Acquire
these documents independently. Source passages, OCR text, Wiki cards and indexes are
not distributed here.

## Scoring

`cpt_core.scoring.score_component_evidence` implements the coverage arithmetic on
externally validated evidence identities. Within a compatible alternative, child
components share their parent's weight. Parents have equal weight. Alternatives
are evaluated separately and the highest-coverage alternative is selected; support
is not assembled across incompatible alternatives. Group coverages are averaged.

A component's `supports` list is an OR over clauses, while each clause is an AND
over evidence IDs. Complete coverage requires all components in a valid alternative
for each required group. Rubric answer pools remain provisional; unlisted evidence
is unjudged rather than automatically incorrect.

Before scoring, establish that returned passages match the source text, cover the
referenced intervals, satisfy the evidence-length budget, and support the annotated
need. Passing arbitrary IDs to the arithmetic function does not perform these checks
or establish semantic correctness. Online model self-assessments are not grading
labels. The example uses artificial evidence IDs solely to demonstrate arithmetic.
