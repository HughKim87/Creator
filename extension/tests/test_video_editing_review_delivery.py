from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from video_editing import write_review_premiere_xml, write_validated_premiere_xml
from video_editing.premiere_xml import PremiereXmlError, PREMIERE_CS6_V4_PROFILE
from video_editing.timeline_v2 import TimelineV2Error, editorial_fingerprint, task_payload_fingerprint, validate_timeline_v2, as_legacy_timeline
from editorial_test_support import synthetic_state
from video_editing.editorial_state import editorial_state_fingerprint
from video_editing.preflight import CHECKS, validate_preflight

ROOT = Path(__file__).resolve().parents[2]

def candidate():
    v = json.loads((ROOT / "extension/examples/video-edit-timeline-v2.json").read_text("utf-8"))
    v["validation"] = {"semantic_status": "not_run", "reviewed_editorial_fingerprint": None, "reviewer": None,
        "passes": {k: {"status": "not_run", "method": None, "reviewer": None, "checked_at": None, "evidence": None}
            for k in ("causal_space", "tempo_repetition", "av_boundary")}}
    for b in v["editorial_evidence"]["microbeats"]:
        b["boundary_review"] = "pending"
    return v

def report(v):
    return {"version": "review-preflight-v2", "editorial_state_fingerprint": editorial_state_fingerprint(synthetic_state(v)), "editorial_fingerprint": editorial_fingerprint(v),
        "task_payload_fingerprint": task_payload_fingerprint(v), "reviewer": "agent:synthetic-test",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": {k: {"status": "passed" if k == "source_mapping" else "recorded", "method": "synthetic fixture assertion", "evidence": "not a real editorial review"} for k in CHECKS},
        "boundary_microbeat_ids": [b["id"] for b in v["editorial_evidence"]["microbeats"]],
        "limitations": ["Actual audio/video playback not performed; user review pending."]}

class ReviewValidationTests(unittest.TestCase):
    def test_pending_is_only_valid_for_review_and_is_never_promoted(self):
        v = candidate(); before = deepcopy(v)
        validate_timeline_v2(v, purpose="premiere_review_xml")
        self.assertEqual(as_legacy_timeline(v, purpose="premiere_review_xml")["semantic_gate"]["status"], "pending")
        with self.assertRaises(TimelineV2Error): validate_timeline_v2(v, purpose="premiere_xml")
        with self.assertRaises(TimelineV2Error): as_legacy_timeline(v, purpose=None)
        self.assertEqual(v, before)

    def test_export_safety_rules_still_apply(self):
        for label, mutate in [
            ("rejected", lambda v: v["revision"].update(status="use_prohibited")),
            ("historical", lambda v: v["revision"].update(status="historical")),
            ("failed boundary", lambda v: v["editorial_evidence"]["microbeats"][0].update(boundary_review="failed")),
            ("pending defect", lambda v: v["editorial_evidence"]["feedback"]["defects"].append({"id":"d","scope":"opening","clip_ids":["V001"],"status":"pending","evidence":"known defect","approved_by":None})),
            ("unapproved expansion", lambda v: v.update(workflow_profile="new_full_edit")),
            ("bad range", lambda v: v["sequence"]["video_clips"][0].update(source_out=999999)),
            ("missing ownership", lambda v: v["editorial_evidence"]["microbeats"].clear()),
            ("missing baseline", lambda v: v.update(workflow_profile="approved_delta")),
        ]:
            with self.subTest(label=label):
                v=candidate();mutate(v)
                with self.assertRaises(TimelineV2Error): validate_timeline_v2(v,purpose="premiere_review_xml")

    def test_review_record_rejects_stale_incomplete_failed_and_future(self):
        for label,mutate in [
            ("stale",lambda p:p.update(editorial_fingerprint="sha256:"+"0"*64)),
            ("task stale",lambda p:p.update(task_payload_fingerprint="sha256:"+"0"*64)),
            ("coverage",lambda p:p.update(boundary_microbeat_ids=[])),
            ("failed",lambda p:p["checks"]["speech_boundaries"].update(status="failed")),
            ("empty evidence",lambda p:p["checks"]["visual_boundaries"].update(evidence=" ")),
            ("future",lambda p:p.update(checked_at="2999-01-01T00:00:00+00:00")),
            ("limits",lambda p:p.update(limitations=[])),
        ]:
            with self.subTest(label=label):
                v=candidate();p=report(v);mutate(p)
                with self.assertRaises(PremiereXmlError):validate_preflight(v,p,synthetic_state(v))

@unittest.skipUnless(os.name=="nt", "mandatory source lock requires Windows")
class ReviewDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.source=self.root/"source.mp4"
        self.source.write_bytes(b"synthetic source")
        self.target=self.root/"candidate.xml";self.v=candidate()
        self.v["source_manifest"].update(path=str(self.source),content_sha256="sha256:"+hashlib.sha256(self.source.read_bytes()).hexdigest(),byte_size=self.source.stat().st_size)
        self.v["delivery"]["output_path"]=str(self.target)

    def write(self, preflight=None):
        return write_review_premiere_xml(self.v,self.target,preflight=report(self.v) if preflight is None else preflight,editorial_state=synthetic_state(self.v),profile=PREMIERE_CS6_V4_PROFILE)

    def test_real_guarded_write_preserves_candidate_and_clip_mapping(self):
        before=deepcopy(self.v);result=self.write();xml=ET.parse(self.target)
        self.assertEqual(result["validation_status"],"not_run")
        self.assertEqual(result["user_approval_status"],"not_approved")
        self.assertEqual(result["delivery_kind"],"review_candidate")
        self.assertEqual(self.v,before)
        seq=xml.find(".//sequence")
        self.assertTrue(seq.findtext("name").startswith("[REVIEW - NOT APPROVED]"))
        for actual,expected in zip(seq.findall("media/video/track/clipitem"),self.v["sequence"]["video_clips"]):
            self.assertEqual(int(actual.findtext("in")),expected["source_in"])
            self.assertEqual(int(actual.findtext("out")),expected["source_out"])
        self.assertEqual(len(xml.findall(".//pathurl")),1)

    def test_missing_preflight_and_semantic_route_create_nothing(self):
        with self.assertRaises(PremiereXmlError):write_review_premiere_xml(self.v,self.target,preflight=None,profile=PREMIERE_CS6_V4_PROFILE)
        with self.assertRaises(TimelineV2Error):write_validated_premiere_xml(self.v,self.target,profile=PREMIERE_CS6_V4_PROFILE)
        self.assertEqual({p.name for p in self.root.iterdir()},{"source.mp4"})

    def test_source_drift_and_existing_output_remain_protected(self):
        self.v["source_manifest"]["content_sha256"]="sha256:"+"0"*64
        with self.assertRaises(PremiereXmlError):self.write()
        self.assertFalse(self.target.exists())
        self.v["source_manifest"]["content_sha256"]="sha256:"+hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.target.write_bytes(b"user result")
        with self.assertRaises(PremiereXmlError):self.write()
        self.assertEqual(self.target.read_bytes(),b"user result")
        self.assertEqual({p.name for p in self.root.iterdir()},{"source.mp4","candidate.xml"})

    def test_cli_requires_preflight_and_returns_pending_status(self):
        inp=self.root/"timeline.json";pre=self.root/"preflight.json"
        inp.write_text(json.dumps(self.v),encoding="utf-8");pre.write_text(json.dumps(report(self.v)),encoding="utf-8")
        env=os.environ.copy();env["PYTHONPATH"]=str(ROOT/"extension/src");env["PYTHONDONTWRITEBYTECODE"]="1"
        args=[sys.executable,"-B","-m","video_editing","premiere-review-xml","--timeline-json",str(inp),"--output",str(self.target)]
        bad=subprocess.run(args,env=env,capture_output=True,text=True);self.assertEqual(bad.returncode,2);self.assertFalse(self.target.exists())
        state=self.root/"editorial-state.json";state.write_text(json.dumps(synthetic_state(self.v)),encoding="utf-8")
        ok=subprocess.run(args+["--preflight-json",str(pre),"--editorial-state-json",str(state)],env=env,capture_output=True,text=True)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["result"]["validation_status"],"not_run")
