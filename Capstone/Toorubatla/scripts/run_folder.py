import json,sys
from pathlib import Path
from app.pipeline import ReconciliationPipeline
folder=Path(sys.argv[1] if len(sys.argv)>1 else "data/input")
paths=[p for p in sorted(folder.iterdir()) if p.is_file()]
print(ReconciliationPipeline().run(paths).model_dump_json(indent=2))
