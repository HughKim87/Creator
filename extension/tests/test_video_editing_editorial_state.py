from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from editorial_test_support import synthetic_state, refresh_review
from test_video_editing_review_delivery import candidate, report
from video_editing import write_review_premiere_xml, write_validated_premiere_xml
from video_editing.editorial_state import (derive_omissions, validate_editorial_state, record_editorial_feedback, editorial_state_fingerprint, editorial_basis_fingerprint)
from video_editing.preflight import validate_preflight
from video_editing.premiere_xml import PremiereXmlError
from video_editing.timeline_v2 import editorial_fingerprint


class EditorialStateTests(unittest.TestCase):
    def setUp(self):
        self.v = candidate()
        self.s = synthetic_state(self.v)

    def reject(self, state=None, pattern=None):
        with self.assertRaisesRegex(PremiereXmlError, pattern or 'editorial state'):
            validate_editorial_state(self.v, self.s if state is None else state)

    def test_actual_omissions_are_independent_video_and_audio_complements(self):
        rows = derive_omissions(self.v, self.s)
        self.assertEqual([(r['track'],r['source_in'],r['source_out']) for r in rows], [('video',120,300),('audio',118,300)])
        self.assertEqual(validate_editorial_state(self.v,self.s)['omissions'],2)

    def test_unrecorded_deletions_block_even_when_all_retained_beats_exist(self):
        self.s['reviews'][0]['omissions'] = []
        self.reject(pattern='every actual omission')

    def test_missing_partial_or_reordered_required_lookback_blocks(self):
        for a,b in [(150,180),(110,125)]:
            with self.subTest(a=a):
                s=deepcopy(self.s)
                s['scenes'][0]['anchors'].append(dict(id='look-back',source_in=a,source_out=b,media_scope='video',observation='Pursuer position is shown before renewed escape'))
                refresh_review(self.v,s)
                self.reject(s, 'required anchor')
        self.s['scenes'][0]['anchors'][0].update(source_in=0,source_out=120)
        c=self.v['sequence']['video_clips'][0]
        self.v['sequence']['video_clips'][0:1]=[dict(c,source_in=60,source_out=120,timeline_start=0),dict(c,source_in=0,source_out=60,timeline_start=60)]
        refresh_review(self.v,self.s)
        self.reject(pattern='reordered')

    def test_contiguous_microbeat_splits_preserve_anchor(self):
        self.s['scenes'][0]['anchors'][0].update(source_in=0,source_out=120)
        c=self.v['sequence']['video_clips'][0]
        self.v['sequence']['video_clips'][0:1]=[dict(c,source_out=60),dict(c,source_in=60,timeline_start=60)]
        refresh_review(self.v,self.s)
        validate_editorial_state(self.v,self.s)

    def test_dark_uncertain_deletion_cannot_be_marked_safe_by_reason_text(self):
        self.s['reviews'][0]['omissions'][0].update(certainty='uncertain',reason='Probably repeated running in dark frames')
        self.reject(pattern='uncertain omission')

    def test_duplicate_stale_and_empty_evidence_decisions_block(self):
        for kind in ('duplicate','stale','empty'):
            with self.subTest(kind=kind):
                s=deepcopy(self.s);rows=s['reviews'][0]['omissions']
                if kind=='duplicate': rows.append(deepcopy(rows[0]))
                elif kind=='stale': rows[0]['source_in']+=1
                else: rows[0]['observation']=' '
                self.reject(s)

    def test_leading_trailing_omissions_inside_scope_require_decisions(self):
        self.s['scenes'][0]['source_out']=500
        self.s['reviews'][0]['state_basis_fingerprint']=editorial_basis_fingerprint(self.s)
        self.reject(pattern='every actual omission')
        refresh_review(self.v,self.s)
        rows=derive_omissions(self.v,self.s)
        self.assertIn(('video',420,500),[(r['track'],r['source_in'],r['source_out']) for r in rows])
        validate_editorial_state(self.v,self.s)

    def test_source_outside_selected_scene_scope_is_not_silently_ignored(self):
        self.s['scenes'][0]['source_out']=400
        self.reject(pattern='outside planned scenes')

    def test_wrong_source_and_invalid_or_overlapping_plan_block(self):
        for mutate in (lambda s:s.update(source_manifest_fingerprint='sha256:'+'0'*64),lambda s:s['scenes'][0].update(viewer_learns=''),lambda s:s['scenes'].append(dict(s['scenes'][0],id='duplicate-scope')),lambda s:s.update(scenes=[])):
            s=deepcopy(self.s);mutate(s);self.reject(s)

    def test_planned_cause_must_precede_result_in_actual_timeline(self):
        one=deepcopy(self.s['scenes'][0]);two=deepcopy(one)
        one.update(source_out=300,anchors=[dict(one['anchors'][0],source_in=0,source_out=20)])
        two.update(id='result',source_in=300,depends_on=[one['id']],anchors=[dict(one['anchors'][0],id='result-anchor',source_in=300,source_out=320)])
        self.s['scenes']=[one,two]
        self.v['sequence']['video_clips'][0]['timeline_start']=120
        self.v['sequence']['video_clips'][1]['timeline_start']=0
        refresh_review(self.v,self.s)
        self.reject(pattern='cause appears after')

    def test_feedback_transition_preserves_plan_and_invalidates_reviews(self):
        before=deepcopy(self.s)
        new=record_editorial_feedback(self.v,self.s,feedback_id='lookback',symptom='Missing pursuer recheck',reported_by='user',required_anchor_ids=['first-video'])
        self.assertEqual(self.s,before)
        self.assertEqual(new['scenes'],self.s['scenes'])
        self.assertEqual(new['reviews'],[])
        self.assertEqual(new['generation'],2)
        self.reject(new,'defective edit')
        self.v['timeline_id']='new-id-same-edit'
        self.reject(new,'defective edit')

    def test_new_edit_requires_carried_feedback_resolution_and_anchor(self):
        self.s=record_editorial_feedback(self.v,self.s,feedback_id='lookback',symptom='Missing pursuer recheck',reported_by='user',required_anchor_ids=['first-video'])
        self.v['sequence']['video_clips'][0]['edit_reason']='Revised scene'
        refresh_review(self.v,self.s)
        self.reject(pattern='unresolved feedback')
        self.s['reviews'][0]['resolutions']=[dict(feedback_id='lookback',anchor_ids=['first-audio'],evidence='Only audio kept')]
        self.reject(pattern='omits required')
        self.s['reviews'][0]['resolutions'][0].update(anchor_ids=['first-video'],evidence='Required visual anchor preserved in changed edit')
        validate_editorial_state(self.v,self.s)

    def test_feedback_is_not_lost_when_another_defect_is_added(self):
        s=record_editorial_feedback(self.v,self.s,feedback_id='a',symptom='A',reported_by='user')
        s=record_editorial_feedback(self.v,s,feedback_id='b',symptom='B',reported_by='user')
        self.assertEqual([f['id'] for f in s['feedback']],['a','b'])
        with self.assertRaises(PremiereXmlError):record_editorial_feedback(self.v,s,feedback_id='a',symptom='A',reported_by='user')

    def test_stale_state_and_false_semantic_pass_in_preflight_block(self):
        p=report(self.v)
        validate_preflight(self.v,p,self.s)
        s=deepcopy(self.s);s['scenes'][0]['show']='Changed design'
        with self.assertRaisesRegex(PremiereXmlError,'stale editorial state'):validate_preflight(self.v,p,s)
        p['checks']['causal_continuity']['status']='passed'
        with self.assertRaisesRegex(PremiereXmlError,'actual observation level'):validate_preflight(self.v,p,self.s)
        p=report(self.v);p['version']='review-preflight-v1'
        with self.assertRaises(PremiereXmlError):validate_preflight(self.v,p,self.s)

    def test_both_writers_require_state_before_opening_media(self):
        with patch('video_editing.delivery._locked_source') as lock:
            with self.assertRaises(PremiereXmlError):write_review_premiere_xml(self.v,'not-created.xml',preflight=report(self.v),profile='premiere-cs6-v4')
            # Semantic route still applies its existing review gate first.
            from test_video_editing_timeline_v2 import ROOT
            v=json.loads((ROOT/'extension/examples/video-edit-timeline-v2.json').read_text('utf-8'))
            with self.assertRaises(PremiereXmlError):write_validated_premiere_xml(v,'not-created.xml',profile='premiere-cs6-v4')
            lock.assert_not_called()

    def test_stale_candidate_review_generation_and_renamed_ids_cannot_escape(self):
        self.s['generation']+=1
        self.reject(pattern='stale plan|stale candidate')

    def test_feedback_can_be_registered_before_scene_diagnosis(self):
        self.s['scenes']=[]
        self.s['reviews']=[]
        state=record_editorial_feedback(self.v,self.s,feedback_id='undated-source',symptom='Look-back missing; source position not yet known',reported_by='user')
        self.assertEqual(len(state['feedback']),1)
        self.reject(state,'scenes list required')

    def test_changed_plan_invalidates_candidate_review_on_both_export_paths(self):
        self.s['scenes'][0]['show']='Changed source interpretation'
        self.reject(pattern='stale plan')

    def test_cli_records_feedback_without_overwriting_old_state(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);v=root/'timeline.json';s=root/'state.json';out=root/'next.json'
            v.write_text(json.dumps(self.v),'utf-8');s.write_text(json.dumps(self.s),'utf-8');before=s.read_bytes()
            env=os.environ.copy();env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src');env['PYTHONDONTWRITEBYTECODE']='1'
            cmd=[sys.executable,'-B','-m','video_editing','record-feedback','--timeline-json',str(v),'--editorial-state-json',str(s),'--feedback-id','lookback','--symptom','Missing visual cause','--reported-by','user','--output',str(out)]
            result=subprocess.run(cmd,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            new=json.loads(out.read_text('utf-8'));self.assertEqual(new['reviews'],[]);self.assertEqual(s.read_bytes(),before)
            self.assertEqual(subprocess.run(cmd,env=env,capture_output=True).returncode,2)
            self.assertEqual(list(root.glob('.*.tmp')),[])


if __name__ == '__main__':
    unittest.main()
