from pathlib import Path
import shutil, uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.pipeline import ReconciliationPipeline
from app.models.schemas import ReconciliationResponse, ReviewRequest
from app.services.file_utils import SUPPORTED
configure_logging(); app=FastAPI(title="Intelligent Invoice Reconciliation",version="1.0.0")
review_decisions: dict[str, ReviewRequest] = {}
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/reconcile",response_model=ReconciliationResponse)
def reconcile(files:list[UploadFile]=File(...)):
    run_dir=settings.input_dir/str(uuid.uuid4()); run_dir.mkdir(parents=True,exist_ok=True); paths=[]
    try:
        for f in files:
            suffix=Path(f.filename or "").suffix.lower()
            if suffix not in SUPPORTED: raise HTTPException(400,f"Unsupported file: {f.filename}")
            target=run_dir/Path(f.filename or "upload").name
            with target.open("wb") as out: shutil.copyfileobj(f.file,out)
            paths.append(target)
        result=ReconciliationPipeline().run(paths)
        settings.output_dir.mkdir(parents=True,exist_ok=True)
        (settings.output_dir/f"{run_dir.name}.json").write_text(result.model_dump_json(indent=2),encoding="utf-8")
        return result
    finally:
        shutil.rmtree(run_dir,ignore_errors=True)

@app.post("/review")
def review(request: ReviewRequest):
    review_decisions[request.document_id] = request
    return {
        "document_id": request.document_id,
        "decision": request.decision,
        "reason": request.reason,
        "decided_by": request.decided_by,
        "status": "recorded",
    }
