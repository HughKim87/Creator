from pathlib import Path
import importlib.util,json,tempfile,unittest,hashlib
ROOT=Path(__file__).resolve().parents[2]
def module(name):
 p=ROOT/'.agents/skills/coordinate-video-production/scripts'/name
 spec=importlib.util.spec_from_file_location(name.replace('.','_'),p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
BUNDLE=module('check_skill_bundle.py');REVIEW=module('validate_video_job.py')
class ImprovementTests(unittest.TestCase):
 def test_bundle_detects_missing_and_changed_files_without_modifying_them(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'.agents/skills/example/SKILL.md';p.parent.mkdir(parents=True);p.write_text('reviewed');manifest=root/'manifest.json'
   manifest.write_text(json.dumps({'schema_version':'video-skill-bundle-v1','files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()}}))
   self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'valid')
   p.write_text('changed');self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'invalid');self.assertEqual(p.read_text(),'changed')
   p.unlink();self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'invalid')
 def test_text_fingerprint_survives_git_line_ending_normalization(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'SKILL.md';p.write_bytes(b'one\r\ntwo\r\n');expected=BUNDLE.digest(p)
   p.write_bytes(b'one\ntwo\n');self.assertEqual(expected,BUNDLE.digest(p))
 def test_required_review_separates_listening_from_transcript_read(self):
  review={'status':'reviewed','findings':[],'checked_at':'2026-10-10T00:00:00+09:00','summary':'claims reviewed','video':'v.mp4','captions':'s.srt','artifact_hashes':{'video':'a'*64,'captions':'b'*64},'review_scope':{'narration_full_read':True,'visual_method':'scene_samples','direct_listening':'not_run','limitations':['Direct listening was not performed.']}}
  def check():
   errors=[];REVIEW.validate_content_review({'content_review':review},{'video':'complete','captions':'complete'}, {},errors,root=None,check_artifacts=False,required=True);return errors
  self.assertEqual(check(),[])
  review['review_scope']['limitations']=[];self.assertIn('unperformed listening requires a disclosed limitation',check())
  review['review_scope']['limitations']=['No listening'];review['review_scope']['visual_method']='not_run';self.assertIn('content_review requires recorded visual review',check())
  review['review_scope']['visual_method']='scene_samples';review['review_scope']['narration_full_read']=False;self.assertIn('content_review requires full narration review',check())
if __name__=='__main__':unittest.main()
