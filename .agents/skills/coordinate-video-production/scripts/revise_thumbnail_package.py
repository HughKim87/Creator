"""Invalidate only the title/thumbnail revision and its dependent upload package."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path


def plan_revision(job: dict, title: dict, manual: dict, *, scope: str, revision: int) -> tuple[dict, dict, dict]:
    if scope not in {"title", "copy", "image"}:
        raise ValueError("scope must be title, copy or image")
    if type(revision) is not int or revision <= title.get("revision", 0):
        raise ValueError("revision must be greater than the current revision")
    if any(job["stages"][s]["status"] != "complete" for s in ("research", "video", "captions")):
        raise ValueError("upstream stages must be complete before thumbnail revision")
    job, title, manual = deepcopy((job, title, manual))
    stamp = datetime.now(timezone.utc).isoformat()
    job.update(status="active", updated_at=stamp, next_action=f"Complete {scope} revision {revision}, then rebuild the manual package")
    job.pop("completed_at", None)
    for name, status in (("title_thumbnail", "in_progress"), ("upload_package", "pending")):
        stage = job["stages"][name]
        stage.update(status=status, validation="", note=f"Invalidated by {scope} revision {revision}")
    title["revision"] = revision
    title["revision_scope"] = scope
    if scope == "title":
        title["title"]["status"] = "draft"
        for key in ("approved_at", "approved_text", "approval_method"):
            title["title"].pop(key, None)
    else:
        approvals = ("copy", "image_generation", "visual") if scope == "copy" else ("image_generation", "visual")
        for name in approvals:
            title["approval"][name] = {"status": "pending"}
        for key in ("generated_at", "normalization"):
            title["thumbnail"].pop(key, None)
        title.pop("visual_review", None)
        for flag in ("text_exact", "mobile_preview_reviewed", "clickability_reviewed"):
            title["validation"][flag] = False
        if "editorial" in title:
            title["editorial"].pop("review", None)
    # A title edit also requires a fresh assessment of its relationship to the image.
    title["validation"]["title_thumbnail_not_duplicate"] = False
    if "editorial" in title:
        title["editorial"]["brief"]["title_thumbnail_roles"] = ""
    manual["preparation"]["status"] = "pending"
    manual.pop("artifact_hashes", None)
    return job, title, manual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--scope", choices=("title", "copy", "image"), required=True)
    parser.add_argument("--revision", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        base = args.job.absolute().parent
        if args.job.name != "VIDEO_JOB.json":
            raise ValueError("job must be VIDEO_JOB.json")
        paths = [base / n for n in ("VIDEO_JOB.json", "youtube-title-thumbnail.json", "youtube-manual-upload.json")]
        if any(p.is_symlink() or p.resolve().parent != base.resolve() for p in paths):
            raise ValueError("revision files must be ordinary files in the job directory")
        values = [json.loads(p.read_text(encoding="utf-8-sig")) for p in paths]
        planned = plan_revision(*values, scope=args.scope, revision=args.revision)
        if args.apply:
            # Mark the job incomplete first: interruption cannot leave a false complete job.
            for path, data in zip(paths, planned):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "applied" if args.apply else "ready", "revision": args.revision, "scope": args.scope, "files": [str(p) for p in paths], "preserved_stages": ["research", "video", "captions"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
