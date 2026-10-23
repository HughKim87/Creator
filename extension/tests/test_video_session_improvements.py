from pathlib import Path
import importlib.util,json,tempfile,unittest,hashlib,shutil
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[2]
def module(name):
 p=ROOT/'.agents/skills/coordinate-video-production/scripts'/name
 spec=importlib.util.spec_from_file_location(name.replace('.','_'),p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
BUNDLE=module('check_skill_bundle.py');REVIEW=module('validate_video_job.py')
class ImprovementTests(unittest.TestCase):
 def test_managed_skills_are_complete_without_installed_copies(self):
  manifest=json.loads((ROOT/BUNDLE.MANIFEST).read_text(encoding='utf-8'))
  names=('youtube-channel-coach','youtube-timestamp-hashtag','create-shorts')
  for name in names:
   self.assertIn(f'.agents/skills/{name}/SKILL.md',manifest['files'])
   self.assertIn(f'.agents/skills/{name}/agents/openai.yaml',manifest['files'])
  with tempfile.TemporaryDirectory(dir=ROOT/'extension/work',prefix='managed-skill-bundle-') as d:
   root=Path(d)
   # Copy only the recorded project files, never the installed plugin cache.
   for rel in manifest['files']:
    target=root/rel;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/rel,target)
   target=root/BUNDLE.MANIFEST;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_text(json.dumps(manifest),encoding='utf-8')
   self.assertEqual(BUNDLE.inspect(root)['status'],'valid')
   resource=root/'.agents/skills/create-shorts/assets/review.html'
   original=resource.read_bytes();resource.unlink()
   self.assertEqual(BUNDLE.inspect(root)['status'],'invalid')
   resource.write_bytes(original)
   self.assertEqual(BUNDLE.inspect(root)['status'],'valid')
   missing=root/'.agents/skills/youtube-channel-coach/SKILL.md'
   missing.unlink()  # This test's isolated copy, not the project source.
   result=BUNDLE.inspect(root)
   self.assertEqual(result['status'],'invalid')
   self.assertTrue(any('youtube-channel-coach/SKILL.md' in e for e in result['errors']))
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
 def test_html_bundle_accepts_line_endings_but_rejects_content_changes(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'extension/work',prefix='html-line-ending-test-') as d:
   root=Path(d);p=root/'.agents/skills/example/assets/review.html'
   p.parent.mkdir(parents=True)
   original='<!doctype html>\n<title>쇼츠 후보</title>\n'.encode('utf-8')
   p.write_bytes(original)
   manifest=root/'manifest.json'
   manifest.write_text(json.dumps({'schema_version':'video-skill-bundle-v1','files':{p.relative_to(root).as_posix():BUNDLE.digest(p)}}),encoding='utf-8')
   p.write_bytes(original.replace(b'\n',b'\r\n'))
   self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'valid')
   p.write_bytes(original)
   self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'valid')
   p.write_bytes(original.replace('쇼츠 후보'.encode('utf-8'),'다른 내용'.encode('utf-8')))
   self.assertEqual(BUNDLE.inspect(root,manifest)['status'],'invalid')
 def test_required_review_separates_listening_from_transcript_read(self):
  review={'status':'reviewed','findings':[],'checked_at':'2026-10-10T00:00:00+09:00','summary':'claims reviewed','video':'v.mp4','captions':'s.srt','artifact_hashes':{'video':'a'*64,'captions':'b'*64},'review_scope':{'narration_full_read':True,'visual_method':'scene_samples','direct_listening':'not_run','limitations':['Direct listening was not performed.']}}
  def check():
   errors=[];REVIEW.validate_content_review({'content_review':review},{'video':'complete','captions':'complete'}, {},errors,root=None,check_artifacts=False,required=True);return errors
  self.assertEqual(check(),[])
  review['review_scope']['limitations']=[];self.assertIn('unperformed listening requires a disclosed limitation',check())
  review['review_scope']['limitations']=['No listening'];review['review_scope']['visual_method']='not_run';self.assertIn('content_review requires recorded visual review',check())
  review['review_scope']['visual_method']='scene_samples';review['review_scope']['narration_full_read']=False;self.assertIn('content_review requires full narration review',check())
class ContentCorrectionBoundaryTests(unittest.TestCase):
 def errors_for(self, finding):
  review={'status':'reviewed','findings':[deepcopy(finding)],'checked_at':'2026-10-17T00:00:00+09:00','summary':'Synthetic correction record, not an actual media review','video':'v.mp4','captions':'s.srt','artifact_hashes':{'video':'a'*64,'captions':'b'*64},'review_scope':{'narration_full_read':True,'visual_method':'scene_samples','direct_listening':'not_run','limitations':['Synthetic metadata only; no actual listening.']}}
  errors=[]
  REVIEW.validate_content_review({'status':'complete','content_review':review},{'video':'complete','captions':'complete'}, {}, errors,root=None,check_artifacts=False,required=True)
  return errors

 def finding(self):
  return {'location':'00:10','claim':'Unsupported guarantee','kind':'unsupported_claim','severity':'material','reason':'Changes viewer understanding','evidence':['fixture://verified-source'],'status':'open'}

 def test_resolved_local_correction_uses_existing_review_without_user_approval_record(self):
  finding=self.finding()
  finding.update(status='resolved',resolution={'method':'video_corrected','note':'Correction checked against source; original retained.'})
  self.assertEqual(self.errors_for(finding),[])

 def test_open_material_issue_cannot_be_approved_or_disclosed_away(self):
  finding=self.finding()
  finding['approval']={'status':'approved','method':'explicit_user'}
  self.assertTrue(any('open issues prevent' in error for error in self.errors_for(finding)))
  finding.update(status='disclosed',resolution={'method':'guide_note','note':'Viewer caution only'})
  self.assertTrue(any('material issues cannot' in error for error in self.errors_for(finding)))

if __name__=='__main__':unittest.main()
