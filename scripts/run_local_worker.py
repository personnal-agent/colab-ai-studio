import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datetime import datetime

import uvicorn

from app.colab_worker.model_swapper import ModelSwapper
from app.colab_worker.server import create_worker_app

swapper = ModelSwapper(idle_timeout_seconds=300.0)
today_str = datetime.now().strftime("%Y-%m-%d")
storage_dir = REPO_ROOT / "outputs" / today_str
storage_dir.mkdir(parents=True, exist_ok=True)

app = create_worker_app(
    model_swapper=swapper,
    storage_dir=storage_dir,
    simulation_mode=False,
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8190)
