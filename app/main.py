from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.evaluator import analyze_source, run_cases
from app.ml_model import predict_quality

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="AI Assignment Code Evaluator", version="1.0.0", description="Test-based grading with a supervised code-quality model.")
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")


class TestCase(BaseModel):
    args: list = Field(default_factory=list)
    kwargs: dict = Field(default_factory=dict)
    expected: object


class EvaluationRequest(BaseModel):
    source: str = Field(min_length=1, max_length=30000)
    function_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    test_cases: list[TestCase] = Field(min_length=1, max_length=30)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Assignment Code Evaluator"}


@app.post("/api/evaluate")
def evaluate(request: EvaluationRequest):
    features, syntax_error = analyze_source(request.source)
    if syntax_error:
        return {"correctness_score": 0, "quality_score": 0, "final_score": 0,
                "passed": 0, "total": len(request.test_cases), "feedback": [syntax_error], "cases": []}
    cases = [case.model_dump() for case in request.test_cases]
    results = run_cases(request.source, request.function_name, cases)
    passed = sum(bool(result.get("passed")) for result in results)
    features.update(passed_tests=passed, total_tests=len(cases))
    quality, sample_count = predict_quality(features)
    correctness = round(100 * passed / len(cases), 1)
    final = round(correctness * 0.7 + quality * 0.3, 1)
    feedback = []
    if passed < len(cases):
        feedback.append(f"Review failing cases ({len(cases) - passed} of {len(cases)} did not pass).")
    if features["docstring_count"] == 0:
        feedback.append("Add a docstring to explain the function's purpose and expected inputs.")
    if features["function_count"] > 1:
        feedback.append("The submission defines multiple functions; keep the solution focused on the requested function.")
    if not feedback:
        feedback.append("All provided tests passed. Keep adding edge cases to validate the solution.")
    return {"correctness_score": correctness, "quality_score": quality, "final_score": final,
            "passed": passed, "total": len(cases), "model_training_examples": sample_count,
            "score_weights": {"correctness": 0.7, "supervised_quality": 0.3},
            "feedback": feedback, "cases": results, "features": features}
