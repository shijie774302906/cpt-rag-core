# Engineering framework and released interfaces

The engineering framework connects an engineer's request and site data to evidence
retrieval, method assessment, numerical calculation, interaction and result delivery.
Literature evidence supplies method definitions, variables and applicability
conditions. Standards evidence supplies requirements and, when applicable, reference
information. Numerical tools calibrate candidate predictions and produce uncertainty
estimates. The LLM organizes the task, assesses evidence and tool feedback, and
explains the resulting analysis.

The framework can seek additional evidence, ask the engineer about missing site
information, or adjust a calculation configuration in response to tool feedback.
These are task-dependent decisions, rather than a mandatory fixed sequence.

`cpt_core.interfaces` defines requests, evidence references and retrieval interfaces.
The synthetic example independently calls the fusion API with a fixed matrix of
method predictions. Users can implement the retrieval interfaces and call the
numerical API from their own orchestration code.
The package contains no autonomous planning policy, model prompts, persistent
memory, production service or live retrieval implementation.

Study evaluation has three purposes: evidence retrieval coverage; completion of
engineering commissions; and the prediction/uncertainty performance of numerical
schemes. Executable numeric examples do not replace commission validation. The
four-region numerical comparisons use a common literature-method pool, distinct
from the method combinations recommended in individual agent commissions.
