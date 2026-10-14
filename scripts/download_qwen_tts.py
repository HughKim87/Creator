"""Download public Qwen weights without credentials; preserve pinned revisions."""
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
runtime = root / "extension" / ".runtime" / "qwen-tts"
os.environ.update({"HF_HOME": str(runtime / "hf-cache"),
                   "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                   "HF_HUB_DISABLE_TELEMETRY": "1"})
from huggingface_hub import HfApi, snapshot_download

manifest_path = root / "extension" / "config" / "qwen-tts-local.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
api = HfApi(token=False)
for repo in manifest["models"]:
    revision = repo.get("revision") or api.model_info(repo["id"]).sha
    print(f"Downloading {repo['id']} @ {revision}", flush=True)
    snapshot_download(repo_id=repo["id"], revision=revision, token=False,
                      local_dir=runtime / "models" / repo["directory"], max_workers=3,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model",
                                      "*.tiktoken", "LICENSE", "README.md"])
    repo["revision"] = revision
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("Model downloads complete", flush=True)
