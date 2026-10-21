"""Synthetic mechanical regressions; no claims of game/semantic review."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'extension/src'),str(ROOT/'extension/tests'),str(ROOT/'.agents/skills/edit-gameplay-video/scripts')]
import postprocess as post
import test_edit_gameplay_video_skill as existing
from video_editing.subtitle import Cue, _render, parse_srt


def profile():
    return dict(version=1,operation='layers',captions=dict(font='Arial',size=10,emphasis_size=14,outline=1,margin=4),
                caption_overrides=[],images=[],zooms=[],audio=dict(integrated_lufs=-14,true_peak_dbtp=-1),chunk_frames=120)


def manifest(path):
    return dict(path=str(path),sha256=post.digest(path),bytes=path.stat().st_size)


class PlanTests(unittest.TestCase):
    def setUp(self):self.p=profile()

    def check(self):post.check_plan(self.p,240,160,90,60)

    def test_cli_requires_job_context_before_media_access(self):
        with patch.object(sys,'argv',['postprocess','--plan','missing.json','--output',str(ROOT/'extension/.runtime/no-output.mp4')]), patch.object(post.cut,'current_job_paths',return_value=None):
            with self.assertRaisesRegex(ValueError,'creator_job'):post.main()

    def test_profile_and_duplicate_emphasis(self):
        self.check()
        self.p['caption_overrides']=[dict(cue=1,style='emphasis',color='FFFF00')]*2
        with self.assertRaisesRegex(ValueError,'duplicate'):self.check()

    def test_hud_anchor_and_zoom_boundaries(self):
        self.p['images']=[dict(start_frame=5,end_frame=20,anchor='observed reaction',rect=[0,0,20,20])]
        self.p['protected_rects']=[[0,0,30,30]]
        with self.assertRaisesRegex(ValueError,'protected'):self.check()
        self.p['protected_rects']=[];self.p['images'][0]['anchor']=''
        with self.assertRaisesRegex(ValueError,'anchor'):self.check()
        self.p['images']=[]
        self.p['zooms']=[dict(start_frame=0,end_frame=20,anchor='reaction',factor=1.2,x=.5,y=.5),dict(start_frame=19,end_frame=30,anchor='reaction',factor=1.2,x=.5,y=.5)]
        with self.assertRaisesRegex(ValueError,'overlapping'):self.check()

    def test_nonfinite_and_hot_final_meter_rejected(self):
        for meter in (dict(input_i='-inf',input_tp='-2'),dict(input_i='-14',input_tp='-0.2'),dict(input_i='-18',input_tp='-2')):
            with self.assertRaises(ValueError):post.verify_audio(meter,self.p['audio'])
        self.p['audio']['integrated_lufs']=float('nan')
        with self.assertRaises(ValueError):self.check()

    def test_ass_emphasis_replaces_literal_cue(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'extension/.runtime') as d:
            path=Path(d)/'x.ass'
            post.ass_file(path,[Cue(1,0,1000,('Hi {\\b1}',))],self.p['captions'],{1:dict(style='emphasis',color='FF0000')},160,90)
            text=path.read_text(encoding='utf-8')
            self.assertEqual(text.count('Dialogue:'),1)
            self.assertIn('Arial,14,&H000000FF',text)
            self.assertIn('｛＼b1｝',text)

    def test_srt_offset_keeps_body_and_rejects_bad_duration(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'extension/.runtime') as d:
            a,b,c=(Path(d)/n for n in ('a.srt','b.srt','c.srt'))
            body=[Cue(1,100,1900,('Body',))];outro=[Cue(1,100,1700,('Outro',))]
            a.write_text(_render(body),encoding='utf-8-sig');b.write_text(_render(outro),encoding='utf-8')
            c.write_text(post.join_srt(a,b,4000,6000),encoding='utf-8')
            joined=parse_srt(c)
            self.assertEqual(joined[0],body[0]);self.assertEqual(joined[1],Cue(2,4100,5700,('Outro',)))
            for offset,total in ((0,6000),(4000,4000),(1500,6000),(4000,5000)):
                with self.assertRaises(ValueError):post.join_srt(a,b,offset,total)


@unittest.skipUnless(os.name=='nt','mandatory read locks require Windows')
class MediaTests(existing.RealCandidateRender):
    # Reuse immutable synthetic source fixture, without inheriting its tests.
    test_render_source_binding_pixels_audio_and_no_approval=None
    test_existing_output_is_not_replaced=None
    test_source_drift_does_not_publish=None

    def setUp(self):
        super().setUp()
        from editorial_test_support import synthetic_state
        tagged=self.scratch/'tagged.mkv'
        post.cut.run([self.ffmpeg,'-v','error','-i',self.source,'-c','copy','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-n',tagged],self.scratch)
        self.source=tagged
        self.value['source_manifest'].update(path=str(tagged),content_sha256=post.digest(tagged),byte_size=tagged.stat().st_size)
        self.state=synthetic_state(self.value)
        self.srt=self.scratch/'body.srt'
        self.srt.write_text(_render([Cue(1,200,1300,('Medic?',)),Cue(2,2200,3300,('Down!',))]),encoding='utf-8')
        self.p=profile();self.p.update(editorial_fingerprint=post.cut.editorial_fingerprint(self.value),srt=manifest(self.srt))
        self.p['caption_overrides']=[dict(cue=1,style='emphasis',color='FFFF00')]

    def execute(self,name='post.mp4',p=None):
        return post.execute(p or self.p,work=self.scratch,output=self.scratch/name,ffmpeg=self.ffmpeg,ffprobe=self.ffprobe,value=self.value,state=self.state)

    def image(self,path,frame):
        return post.cut.run([self.ffmpeg,'-v','error','-i',path,'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],self.scratch)

    def test_srt_cli_atomic_append_and_no_overwrite(self):
        from contextlib import redirect_stdout
        import io
        outro=self.scratch/'outro.srt';outro.write_text(_render([Cue(1,100,1700,('Outro',))]),encoding='utf-8')
        target=self.scratch/'final.srt'
        argv=['postprocess','--body-srt',str(self.srt),'--outro-srt',str(outro),'--offset-ms','4000','--total-ms','6000','--output',str(target)]
        with patch.object(sys,'argv',argv),patch.object(post.cut,'current_job_paths',return_value={'outputs':self.scratch}),redirect_stdout(io.StringIO()):
            post.main();before=target.read_bytes()
            with self.assertRaises(ValueError):post.main()
        self.assertEqual(target.read_bytes(),before)
        cues=parse_srt(target)
        self.assertEqual(cues[:2],parse_srt(self.srt));self.assertEqual(cues[2].start_ms,4100)

    def test_layers_pixels_cache_and_delta(self):
        image=self.scratch/'red.png'
        post.cut.run([self.ffmpeg,'-v','error','-f','lavfi','-i','color=red:s=24x20','-frames:v','1','-n',image],self.scratch)
        self.p['images']=[dict(start_frame=30,end_frame=90,anchor='fixture source reaction',rect=[100,10,24,20],asset=manifest(image))]
        self.p['zooms']=[dict(start_frame=140,end_frame=200,anchor='fixture source action',factor=1.2,x=.5,y=.5)]
        before=deepcopy(self.value);source_hash=post.digest(self.source);srt_bytes=self.srt.read_bytes()
        result=self.execute()
        self.assertEqual((result['frames'],result['duration_seconds']),(240,4))
        self.assertEqual((result['technical_status'],result['semantic_status'],result['user_approval']),('passed','not_run','pending'))
        self.assertLessEqual(result['true_peak_dbtp'],-.95)
        self.assertEqual(self.value,before);self.assertEqual(post.digest(self.source),source_hash);self.assertEqual(self.srt.read_bytes(),srt_bytes)
        pixels=self.image(self.scratch/'post.mp4',50);idx=(15*160+110)*3
        self.assertGreater(pixels[idx],200);self.assertLess(pixels[idx+1],40)
        off=self.image(self.scratch/'post.mp4',100)
        source_off=self.image(self.source,100)
        self.assertLess(sum(abs(a-b) for a,b in zip(off[:160*40*3],source_off[:160*40*3]))/(160*40*3),8)
        # A layer-free frame stays close to its exact original content.
        actual,expected=self.image(self.scratch/'post.mp4',235),self.image(self.source,416)
        self.assertLess(sum(abs(a-b) for a,b in zip(actual,expected))/len(actual),8)
        cache=self.scratch/'post-cache';old={x.name:post.digest(x) for x in cache.glob('*.mp4')}
        base=next(x for x in cache.glob('*.mp4') if json.loads(x.with_suffix('.json').read_text()).get('origin'))
        zoomed,plain=self.image(self.scratch/'post.mp4',180),self.image(base,180)
        self.assertGreater(sum(abs(a-b) for a,b in zip(zoomed[:160*40*3],plain[:160*40*3]))/(160*40*3),3)
        result=self.execute('reuse.mp4');self.assertEqual(result['reused_chunks'],2)
        self.p['caption_overrides'][0]['color']='00FFFF'
        result=self.execute('delta.mp4');self.assertEqual(result['reused_chunks'],1)
        self.assertTrue(all(post.digest(cache/name)==sha for name,sha in old.items()))
        self.assertNotEqual(self.image(self.scratch/'post.mp4',50),self.image(self.scratch/'delta.mp4',50))
        self.assertEqual(self.image(self.scratch/'post.mp4',180),self.image(self.scratch/'delta.mp4',180))

    def test_corrupt_cache_and_source_drift_fail_closed(self):
        self.execute()
        cache=self.scratch/'post-cache'
        meta=next(x for x in cache.glob('*.json') if 'start_frame' in json.loads(x.read_text()))
        data=json.loads(meta.read_text());data['sha256']='sha256:'+'0'*64;meta.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'damaged chunk'):self.execute('bad-cache.mp4')
        self.assertFalse((self.scratch/'bad-cache.mp4').exists())
        with self.source.open('ab') as f:f.write(b'drift')
        with self.assertRaisesRegex(ValueError,'source hash mismatch'):self.execute('drift.mp4')
        self.assertFalse((self.scratch/'drift.mp4').exists())

    def test_append_different_fps_timebase_and_packet_identity(self):
        self.execute()
        body=self.scratch/'body.mp4';outro=self.scratch/'outro.mp4'
        post.cut.run([self.ffmpeg,'-v','error','-i',self.scratch/'post.mp4','-c','copy','-video_track_timescale','60000','-n',body],self.scratch)
        post.cut.run([self.ffmpeg,'-v','error','-f','lavfi','-i','testsrc2=s=160x90:r=30:d=2','-f','lavfi','-i','sine=frequency=880:sample_rate=48000:duration=2','-vf','setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709','-ac','2','-c:v','libx264','-bf','0','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-c:a','aac','-n',outro],self.scratch)
        plan=dict(version=1,operation='append',body=manifest(body),outro=manifest(outro),audio=self.p['audio'])
        result=self.execute('joined.mp4',plan)
        self.assertEqual((result['frames'],result['duration_seconds'],result['outro_output_frames']),(360,6,120))
        self.assertTrue(result['body_video_packets_identical'])
        self.assertEqual(post.packet_hashes(self.ffprobe,body,self.scratch),post.packet_hashes(self.ffprobe,self.scratch/'joined.mp4',self.scratch)[:240])
        self.assertLessEqual(result['true_peak_dbtp'],-.95)
        self.assertEqual(result['semantic_status'],'not_run')

    def test_failures_publish_nothing_and_keep_old_output(self):
        self.p['editorial_fingerprint']='stale'
        with self.assertRaisesRegex(ValueError,'stale'):self.execute()
        self.assertFalse((self.scratch/'post.mp4').exists())
        self.p['editorial_fingerprint']=post.cut.editorial_fingerprint(self.value)
        self.p['srt']['sha256']='sha256:'+'0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.execute()
        self.assertFalse((self.scratch/'post.mp4').exists())
        (self.scratch/'post.mp4').write_bytes(b'old')
        with self.assertRaisesRegex(ValueError,'new MP4'):self.execute()
        self.assertEqual((self.scratch/'post.mp4').read_bytes(),b'old')

    def test_width_and_final_peak_gate(self):
        self.srt.write_text(_render([Cue(1,200,1300,('W'*90,))]),encoding='utf-8');self.p['srt']=manifest(self.srt)
        with self.assertRaisesRegex(ValueError,'rendered width'):self.execute()
        self.assertFalse((self.scratch/'post.mp4').exists())
        self.srt.write_text(_render([Cue(1,200,1300,('Medic?',))]),encoding='utf-8');self.p['srt']=manifest(self.srt)
        real=post.measured_audio
        def meter(ffmpeg,path,temp,profile=None):
            if Path(path).name=='result.mp4':return dict(input_i='-14',input_tp='-0.2')
            return real(ffmpeg,path,temp,profile)
        with patch.object(post,'measured_audio',side_effect=meter):
            with self.assertRaisesRegex(ValueError,'final integrated'):self.execute()
        self.assertFalse((self.scratch/'post.mp4').exists())


if __name__=='__main__':unittest.main()
