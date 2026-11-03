# CPT-RAG research core

Selected numerical tools, retrieval questions, evidence-coverage arithmetic, and
framework interfaces for knowledge-assisted cone penetration test interpretation.

## Contents

- `benchmarks/`: literature and standards questions, scoring structures, and
  source metadata. See [the benchmark guide](docs/benchmarks.md).
- `cpt_core/`: Bayesian error calibration, correlated fusion, weight optimization,
  prediction intervals, local cone-factor calibration, Bayesian regression, and
  evidence-coverage arithmetic.
- `docs/framework.md`: roles and interface boundaries in the engineering framework.
- `examples/`: a deterministic synthetic calculation and a scoring example.
- `tests/`: focused numerical and scoring checks.

## Run

Python 3.10 or newer and NumPy/SciPy are required. From this directory:

```sh
python -m pip install -r requirements.txt
python -m examples.synthetic_analysis
python -m examples.score_example
python -m unittest discover -s tests -v
```

The numerical example prints JSON. Its data are synthetic and are not the
measurements or results used in the paper. It requires no model API or network.

The fusion API accepts a fixed combination of method predictions. For a comparison
with and without a standards-derived prior, retain the same matrix columns and
change only the prior center. See [the numerical guide](docs/numerics.md).

## Scope

This package distributes selected research components. Complete agent orchestration,
model prompts, the web service, source documents, Wiki cards, indexes, and original
engineering datasets are not included. The interface definitions cover requests,
evidence references and retrieval. A separate synthetic example calls the numerical
API with a fixed matrix of method predictions; it does not implement an autonomous
agent. Obtain third-party source documents and datasets from their
providers under the applicable terms.

The question collections and numerical kernels support reuse of the released
components. Recreating full retrieval experiments additionally requires the source
corpus, matching text extraction, retrieval implementation, model access and
experiment configurations. The package does not claim one-command reproduction of
all manuscript figures.
