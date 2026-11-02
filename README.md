# AI Powered Assignment Code Evaluation and Code Intelligence System

A runnable supervised-learning project for evaluating Python programming assignments. It combines test-case correctness with a scikit-learn quality model and returns explainable feedback through a FastAPI API and browser interface.

## Features

- FastAPI endpoints: `GET /api/health`, `POST /api/evaluate`, and interactive OpenAPI docs at `/docs`.
- Test case runner with per-submission timeout and isolated child process.
- AST-derived code features: function, loop, branch, docstring, and line counts.
- Supervised `RandomForestRegressor` trained from `data/labeled_examples.csv`.
- Weighted score: 70% test correctness and 30% learned quality estimate.
- Browser UI served from the same API process.

## Requirements

- Python 3.10 or later
- pip

## Run locally

From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install and start:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> for the interface and <http://127.0.0.1:8000/docs> for API documentation.

## API example

```bash
curl -X POST http://127.0.0.1:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"source":"def add(a, b): return a + b", "function_name":"add", "test_cases":[{"args":[2,3],"expected":5},{"args":[-1,4],"expected":3}]}'
```

The response includes correctness, predicted quality, final score, pass/fail details, model sample count, extracted features, and feedback.

## Supervised learning data

`data/labeled_examples.csv` is a small illustrative starter dataset, not a validated grading corpus. Each record has source text, feature values, and a human-style `quality_score` target. Add representative instructor-reviewed examples, then keep feature columns consistent with `app/ml_model.py`. The model is trained when an evaluation request arrives so edits to the CSV take effect without a separate training step. Do not present metrics from this tiny starter data as evidence of model accuracy; evaluate against a larger held-out set before research or grading use.

## Safety and limitations

This is an educational local prototype. Student code execution is risky: the child process has a time limit and a reduced builtins dictionary, but it is **not a security sandbox** and can potentially escape those limits. Do not expose this service to the internet or run untrusted submissions on a personal or production host. A real deployment must execute submissions inside a hardened, disposable container or VM with network disabled, strict CPU/memory/process limits, filesystem isolation, and an external job timeout.

The supervised score is only as credible as its labeled training data. It should support instructor review, not make high-stakes decisions by itself.

## Project structure

```text
app/
  evaluator.py       # AST feature extraction and test runner
  main.py            # FastAPI routes and request validation
  ml_model.py        # supervised model training and prediction
data/
  labeled_examples.csv
web/
  index.html         # evaluation interface
requirements.txt
```
