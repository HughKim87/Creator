"""Source-based layers or explicitly selected finished-file append; technical QA only."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True
import render_candidate as cut
from video_editing.subtitle import parse_srt, validate_cues, _render


def digest(path):
    with Path(path).open('rb') as f:
        return cut._sha256_handle(f)[0]


def number(x, low, high):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not low <= x <= high:
        raise ValueError('numeric setting outside supported range')
    return x


def interval(item, frames):
    a, b = item['start_frame'], item['end_frame']
    if type(a) is not int or type(b) is not int or not 0 <= a < b <= frames:
        raise ValueError('invalid layer frame interval')
    if not isinstance(item.get('anchor'), str) or not item['anchor'].strip():
        raise ValueError('layer needs an observed source anchor')
    return a, b


def check_plan(p, frames, width, height, rate):
    if p.get('version') != 1:
        raise ValueError('post plan version must be 1')
    if Fraction(rate).denominator!=1 or not 1<=rate<=120:
        raise ValueError('post layers require integer CFR 1-120')
    cfg = p['captions']
    if not re.fullmatch(r'[\w .-]{1,80}', cfg['font']):
        raise ValueError('invalid font family')
    for key, bounds in {'size': (8, height/3), 'emphasis_size': (8, height/3),
                        'outline': (0, 12), 'margin': (2, min(width,height)/3)}.items():
        number(cfg[key], *bounds)
    cue_ids = [x['cue'] for x in p.get('caption_overrides', [])]
    if any(type(x) is not int for x in cue_ids) or len(cue_ids) != len(set(cue_ids)):
        raise ValueError('duplicate caption override; emphasis replaces its cue')
    for item in p.get('caption_overrides', []):
        if item.get('style') not in ('normal','emphasis') or not re.fullmatch(r'[0-9A-Fa-f]{6}',item['color']):
            raise ValueError('invalid caption style/color')
    for rect in p.get('protected_rects', []):
        if len(rect)!=4 or any(type(v) is not int for v in rect):raise ValueError('invalid protected rect')
        x,y,w,h=rect
        if not (0<=x<x+w<=width and 0<=y<y+h<=height):raise ValueError('protected rect outside frame')
    for item in p.get('images', []):
        interval(item, frames)
        x,y,w,h = item['rect']
        if any(type(v) is not int for v in (x,y,w,h)) or not (0 <= x and 0 <= y and 0 < w <= width/2 and 0 < h <= height/2 and x+w <= width and y+h <= height):
            raise ValueError('image rect outside frame or larger than half screen')
        for rx,ry,rw,rh in p.get('protected_rects', []):
            if x < rx+rw and rx < x+w and y < ry+rh and ry < y+h:
                raise ValueError('image overlaps protected action/HUD rect')
    zs = sorted(p.get('zooms', []), key=lambda x:x['start_frame'])
    for i,z in enumerate(zs):
        interval(z,frames)
        number(z['factor'],1,2)
        number(z['x'],0,1);number(z['y'],0,1)
        if i and z['start_frame'] < zs[i-1]['end_frame']:
            raise ValueError('overlapping zooms unsupported')
    number(p.get('chunk_frames', 1800),1,36000)
    if type(p.get('chunk_frames',1800)) is not int:
        raise ValueError('chunk_frames must be integer')
    loudness_config(p['audio'])


def loudness_config(a):
    number(a['integrated_lufs'],-30,-10)
    number(a['true_peak_dbtp'],-9,-1)
    number(a.get('tolerance_lu',0.8),0.1,2)


def ass_text(text):
    # Treat captions as literal text; never allow ASS override injection.
    return text.replace('\\','＼').replace('{','｛').replace('}','｝').replace('\n',r'\N')


def ass_stamp(t):
    n=round(t*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100)
    return f'{h}:{m:02}:{s:02}.{n:02}'


def ass_file(path, cues, cfg, overrides, width, height, start=0, end=10**12):
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    styles=[];events=[]
    for cue in cues:
        a,b=max(cue.start_ms/1000,start),min(cue.end_ms/1000,end)
        if b <= a:continue
        style=overrides.get(cue.index, {'style':'normal','color':'FFFFFF'})
        size=cfg['emphasis_size'] if style['style']=='emphasis' else cfg['size']
        rgb=style['color'];color=rgb[4:6]+rgb[2:4]+rgb[0:2]
        name=f'C{cue.index}'
        styles.append(f'Style: {name},{cfg["font"]},{size},&H00{color},&H00{color},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{cfg["outline"]},0,2,{cfg["margin"]},{cfg["margin"]},{cfg["margin"]},1')
        events.append(f'Dialogue: 0,{ass_stamp(a-start)},{ass_stamp(b-start)},{name},,0,0,0,,{ass_text(chr(10).join(cue.text_lines))}')
    style_part,event_part=header.split('[Events]')
    path.write_text(style_part+'\n'.join(styles)+'\n[Events]'+event_part+'\n'.join(events)+'\n',encoding='utf-8')


def caption_width_check(cues,cfg,overrides,width,height,ffmpeg,temp):
    """Measure actual libass glyph raster on a wider canvas, not char count."""
    seen=set();threshold=bytes(1 if v>32 else 0 for v in range(256))
    for cue in cues:
        if len(cue.text_lines)>2:raise ValueError('caption exceeds two lines')
        style=overrides.get(cue.index,{'style':'normal','color':'FFFFFF'})
        key=(cue.text_lines,json.dumps(style,sort_keys=True))
        if key in seen:continue
        seen.add(key)
        ass_file(temp/'measure.ass',[replace(cue,start_ms=0,end_ms=1000)],cfg,{cue.index:dict(style,color='FFFFFF')},width*3,height)
        raw=cut.run([ffmpeg,'-v','error','-f','lavfi','-i',f'color=black:s={width*3}x{height}:r=1:d=1',
                     '-vf','ass=measure.ass','-frames:v','1','-f','rawvideo','-pix_fmt','gray','pipe:1'],temp)
        # TV-range black is 16 after conversion to gray in some builds.
        left,right=width*3,-1
        mask=raw.translate(threshold)
        for y in range(height):
            row=mask[y*width*3:(y+1)*width*3]
            first=row.find(b'\x01')
            if first>=0:left=min(left,first);right=max(right,row.rfind(b'\x01'))
        if right<0:raise ValueError('font produced no visible glyphs')
        if right-left+1+2*cfg['outline'] > width-2*cfg['margin']:
            raise ValueError(f'caption {cue.index} exceeds actual rendered width')


def measured_audio(ffmpeg,path,temp,profile=None):
    # FFmpeg's meter writes stderr, not stdout.
    import subprocess
    a=profile or {'integrated_lufs':-14,'true_peak_dbtp':-1}
    filt=f'loudnorm=I={a["integrated_lufs"]}:TP={a["true_peak_dbtp"]}:LRA=11:print_format=json'
    p=subprocess.run([str(ffmpeg),'-hide_banner','-nostdin','-i',str(path),'-af',filt,'-vn','-f','null','-'],cwd=temp,capture_output=True,check=False)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf-8',errors='replace')[-3000:])
    text=p.stderr.decode('utf-8',errors='replace')
    return json.loads(text[text.rfind('{'):text.rfind('}')+1])


def verify_audio(m,a):
    if not all(math.isfinite(float(m[k])) for k in ('input_i','input_tp')):
        raise ValueError('silent/nonfinite loudness requires explicit audio review')
    if abs(float(m['input_i'])-a['integrated_lufs']) > a.get('tolerance_lu',.8) or float(m['input_tp']) > a['true_peak_dbtp']+.05:
        raise ValueError('final integrated loudness or true peak outside profile')


def normalize_audio(ffmpeg,source,target,a,samples,rate,channels,temp):
    measured=measured_audio(ffmpeg,source,temp,dict(a,true_peak_dbtp=a['true_peak_dbtp']-.4))
    if not math.isfinite(float(measured['input_i'])):raise ValueError('silent audio cannot be normalized')
    filt=(f'loudnorm=I={a["integrated_lufs"]}:TP={a["true_peak_dbtp"]-.4}:LRA=11:'
          f'measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:'
          f'measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:'
          f'offset={measured["target_offset"]}:linear=true,aresample={rate},apad,atrim=end_sample={samples},asetpts=N/SR/TB')
    cut.run([ffmpeg,'-v','error','-nostdin','-i',source,'-vn','-af',filt,'-ar',rate,'-ac',channels,'-c:a','aac','-b:a','256k','-n',target],temp)


def checked_media(probe,path,temp):
    m=cut.probe(probe,path,temp);v,a=m['video'],m['audio']
    rate=Fraction(v['r_frame_rate'])
    if rate.denominator!=1 or rate<1 or rate>120 or Fraction(a['sample_rate'])/rate%1:
        raise ValueError('integer CFR and integer audio samples/frame required')
    if a['channels'] not in (1,2) or v['width']%2 or v['height']%2:
        raise ValueError('even geometry and mono/stereo required')
    cut._check_timestamps(probe,path,temp,m,rate)
    frames=int(v['nb_read_frames'])
    return m,rate,frames


def finish(video,audio,result,ffmpeg,rate,temp):
    cut.run([ffmpeg,'-v','error','-nostdin','-i',video,'-i',audio,'-map','0:v:0','-map','1:a:0','-c','copy',
             '-video_track_timescale',int(rate)*256,'-movflags','+faststart','-n',result],temp)


def video_concat(files,frames,rate,target,ffmpeg,temp):
    # Normalize video timebases before concat; all streams here have no B-frames.
    names=[]
    for i,path in enumerate(files):
        name=f'normalized-{i}.mp4'
        cut.run([ffmpeg,'-v','error','-nostdin','-i',path,'-map','0:v:0','-an','-c','copy',
                 '-video_track_timescale',int(rate)*256,'-n',temp/name],temp)
        names.append(name)
    (temp/'list.txt').write_text('ffconcat version 1.0\n'+''.join(f'file {n}\nduration {f/float(rate):.12f}\n' for n,f in zip(names,frames)),encoding='utf-8')
    cut.run([ffmpeg,'-v','error','-nostdin','-f','concat','-safe','0','-i','list.txt','-map','0:v:0','-an','-c','copy',
             '-bsf:v',f'setts=pts=N*256:dts=N*256:duration=256:time_base=1/{int(rate)*256}',
             '-video_track_timescale',int(rate)*256,'-n',target],temp)


def x264(ffmpeg,source,target,filters,frames,rate,temp):
    cut.run([ffmpeg,'-v','error','-nostdin','-i',source,'-map','0:v:0','-an','-vf',filters,
             '-frames:v',frames,'-c:v','libx264','-crf','18','-preset','fast','-bf','0','-pix_fmt','yuv420p',
             '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
             '-fps_mode','passthrough','-video_track_timescale',int(rate)*256,'-n',target],temp)


def locked_manifest(stack,manifest):
    path=cut.canonical(manifest['path'])
    handle=stack.enter_context(cut._locked_source(path))
    if cut._sha256_handle(handle)!=(manifest['sha256'],manifest['bytes']):raise ValueError('source/asset hash mismatch')
    return path,handle


def layers(p,value,state,work,ffmpeg,ffprobe,temp,stack,references):
    timeline,rate,spf,frames,_=cut.checked_spec(value,state,**(references or {}))
    if p['editorial_fingerprint']!=cut.editorial_fingerprint(timeline):raise ValueError('stale post plan baseline')
    source=timeline['source_manifest'];w,h=source['video']['width'],source['video']['height']
    check_plan(p,frames,w,h,rate)
    original=stack.enter_context(cut._locked_source(cut.canonical(source['path'])))
    if cut._sha256_handle(original)!=(source['content_sha256'],source['byte_size']):raise ValueError('source hash mismatch')
    source_video=cut.probe(ffprobe,source['path'],temp)['video']
    if any(source_video.get(k)!='bt709' for k in ('color_space','color_transfer','color_primaries')) or source_video.get('sample_aspect_ratio','1:1')!='1:1':
        raise ValueError('layers require identified bt709 and square pixels; colour adapter needed')
    holds=[(original,(source['content_sha256'],source['byte_size']))]
    subtitle,handle=locked_manifest(stack,p['srt']);holds.append((handle,(p['srt']['sha256'],p['srt']['bytes'])))
    cues=parse_srt(subtitle);validate_cues(cues,media_end_ms=round(frames/float(rate)*1000))
    if any('\x00' in line or '\ufffd' in line for c in cues for line in c.text_lines):raise ValueError('invalid subtitle characters')
    overrides={x['cue']:x for x in p.get('caption_overrides',[])}
    if set(overrides)-{c.index for c in cues}:raise ValueError('unknown overridden cue')
    caption_width_check(cues,p['captions'],overrides,w,h,ffmpeg,temp)
    images=[]
    for i,item in enumerate(p.get('images',[])):
        path,handle=locked_manifest(stack,item['asset']);holds.append((handle,(item['asset']['sha256'],item['asset']['bytes'])))
        x,y,iw,ih=item['rect'];name=f'image-{i}.png'
        cut.run([ffmpeg,'-v','error','-i',path,'-vf',f'scale={iw}:{ih}:force_original_aspect_ratio=decrease,pad={iw}:{ih}:(ow-iw)/2:(oh-ih)/2:color=black@0,format=rgba','-frames:v','1','-n',temp/name],temp)
        images.append((item,name))
    # Reusable original-derived base; never accept a delivered edited MP4 here.
    cache=work/'post-cache';cache.mkdir(exist_ok=True)
    key=hashlib.sha256(json.dumps(timeline,sort_keys=True).encode()).hexdigest()
    base=cache/(key+'.mp4');record=cache/(key+'.json')
    if base.exists():
        if not record.exists() or json.loads(record.read_text())['sha256']!=digest(base):raise ValueError('damaged base cache')
    else:
        cut.render(value,state,work=work,output=base,ffmpeg=ffmpeg,ffprobe=ffprobe,references=references)
        record.write_text(json.dumps({'sha256':digest(base),'origin':'source-derived stage','renderer':digest(Path(cut.__file__))}))
    if json.loads(record.read_text()).get('renderer')!=digest(Path(cut.__file__)):raise ValueError('base cache renderer changed')
    files=[];counts=[];reused=0;chunk=p.get('chunk_frames',1800)
    for a in range(0,frames,chunk):
        b=min(frames,a+chunk);lo,hi=a/float(rate),b/float(rate)
        local_cues=[c for c in cues if c.start_ms/1000<hi and c.end_ms/1000>lo]
        active=[(im,n) for im,n in images if im['start_frame']<b and im['end_frame']>a]
        zooms=[z for z in p.get('zooms',[]) if z['start_frame']<b and z['end_frame']>a]
        ass_file(temp/'chunk.ass',local_cues,p['captions'],overrides,w,h,lo,hi)
        ass=(temp/'chunk.ass').read_bytes()
        key_data=[key,a,b,hashlib.sha256(ass).hexdigest(),[im for im,n in active],zooms,digest(Path(__file__))]
        ck=hashlib.sha256(json.dumps(key_data,sort_keys=True).encode()).hexdigest()
        target=cache/(ck+'.mp4');meta=cache/(ck+'.json')
        if target.exists():
            if not meta.exists() or json.loads(meta.read_text())['sha256']!=digest(target):raise ValueError('damaged chunk cache')
            reused+=1
        else:
            filters=[f'trim=start_frame={a}:end_frame={b}',f'setpts=N/({rate}*TB)']
            if zooms:
                expr='1';cx=cy='0.5'
                for z in zooms:
                    s,e=(z['start_frame']-a),(z['end_frame']-a)
                    cond=f'gte(on,{s})*lt(on,{e})';amount=f'1+({z["factor"]}-1)*min(1,max(0,(on-{s})/{max(1,e-s-1)}))'
                    expr=f'if({cond},{amount},{expr})';cx=f'if({cond},{z["x"]},{cx})';cy=f'if({cond},{z["y"]},{cy})'
                filters.append(f"zoompan=z='{expr}':x='(iw-iw/zoom)*({cx})':y='(ih-ih/zoom)*({cy})':d=1:s={w}x{h}:fps={rate}")
            graph='[0:v]'+','.join(filters)+'[base];'
            label='base'
            for i,(item,name) in enumerate(active):
                x,y,iw,ih=item['rect'];s=(item['start_frame']-a)/float(rate);e=(item['end_frame']-a)/float(rate)
                graph+=f"movie={name}[im{i}];[{label}][im{i}]overlay={x}:{y}:enable='gte(t,{s})*lt(t,{e})':eof_action=repeat[o{i}];";label=f'o{i}'
            graph+=f'[{label}]ass=chunk.ass,format=yuv420p[v]'
            staged=temp/'chunk.mp4'
            cut.run([ffmpeg,'-v','error','-nostdin','-i',base,'-filter_complex_threads','1','-filter_complex',graph,'-map','[v]','-an','-frames:v',b-a,'-c:v','libx264','-crf','18','-preset','fast','-bf','0','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-fps_mode','passthrough','-video_track_timescale',int(rate)*256,'-n',staged],temp)
            os.link(staged,target);staged.unlink()
            meta.write_text(json.dumps({'sha256':digest(target),'start_frame':a,'end_frame':b}))
        files.append(target);counts.append(b-a)
    video_concat(files,counts,rate,temp/'video.mp4',ffmpeg,temp)
    normalize_audio(ffmpeg,base,temp/'audio.m4a',p['audio'],frames*spf,source['audio']['sample_rate'],source['audio']['channels'],temp)
    return rate,frames,holds,{'reused_chunks':reused,'chunks':len(files),'caption_raster_width':'passed','hud_rectangles':'checked_declared_rects_only','colour_fidelity':'not_run'},cues


def packet_hashes(probe,path,temp):
    d=json.loads(cut.run([probe,'-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=data_hash','-show_data_hash','sha256','-of','json',path],temp))
    return [x['data_hash'] for x in d['packets']]


def append(p,work,ffmpeg,ffprobe,temp,stack):
    if p.get('version')!=1 or p.get('operation')!='append':raise ValueError('explicit append operation required')
    body,bh=locked_manifest(stack,p['body']);outro,oh=locked_manifest(stack,p['outro'])
    holds=[(bh,(p['body']['sha256'],p['body']['bytes'])),(oh,(p['outro']['sha256'],p['outro']['bytes']))]
    m,rate,n=checked_media(ffprobe,body,temp);o,other,on=checked_media(ffprobe,outro,temp)
    v,a=m['video'],m['audio'];ov,oa=o['video'],o['audio']
    if v['codec_name']!='h264' or v.get('has_b_frames')!=0:raise ValueError('packet-preserving append supports H264 without B frames')
    if any(v.get(k)!='bt709' for k in ('color_space','color_transfer','color_primaries')) or v.get('sample_aspect_ratio','1:1')!='1:1':raise ValueError('body must use identified bt709 and square pixels')
    if (v['width'],v['height'])!=(ov['width'],ov['height']):raise ValueError('geometry mismatch; explicit fit adapter required')
    if (a['sample_rate'],a['channels'])!=(oa['sample_rate'],oa['channels']):raise ValueError('audio format mismatch')
    count=Fraction(on,1)*rate/other
    if count.denominator!=1:raise ValueError('outro duration is not an exact output frame count')
    count=int(count);w,h=v['width'],v['height'];matrix={'bt709':'bt709','bt470bg':'bt601','smpte170m':'bt601'}
    if ov.get('color_space') not in matrix:raise ValueError('outro colour matrix must be identified before conversion')
    if ov.get('color_transfer') not in ('bt709','smpte170m','gamma22','gamma28') or ov.get('color_primaries') not in ('bt709','smpte170m','bt470bg','bt470m'):
        raise ValueError(f'outro needs identified SDR primaries and transfer: {ov.get("color_primaries")}, {ov.get("color_transfer")}')
    vf=f'fps={rate},colorspace=all=bt709:format=yuv420p,scale={w}:{h},setsar=1'
    x264(ffmpeg,outro,temp/'outro.mp4',vf,count,rate,temp)
    video_concat([body,temp/'outro.mp4'],[n,count],rate,temp/'video.mp4',ffmpeg,temp)
    samples=int(Fraction(a['sample_rate'])/rate);joined=temp/'audio.wav'
    cut.run([ffmpeg,'-v','error','-nostdin','-i',body,'-i',outro,'-filter_complex',
             f'[0:a]apad,atrim=end_sample={n*samples},asetpts=N/SR/TB[a];[1:a]apad,atrim=end_sample={count*samples},asetpts=N/SR/TB[b];[a][b]concat=n=2:v=0:a=1[out]',
             '-map','[out]','-c:a','pcm_f32le','-n',joined],temp)
    loudness_config(p['audio'])
    normalize_audio(ffmpeg,joined,temp/'audio.m4a',p['audio'],(n+count)*samples,a['sample_rate'],a['channels'],temp)
    return rate,n+count,holds,{'body_video_packets_identical':True,'body_frames':n,'outro_output_frames':count},body


def execute(p,*,work,output,ffmpeg,ffprobe,value=None,state=None,references=None):
    target,work=cut.canonical(output),cut.canonical(work)
    if target.exists() or target.suffix.lower()!='.mp4' or not target.parent.is_dir() or not work.is_dir():raise ValueError('new MP4 and existing work/output directories required')
    with ExitStack() as stack, tempfile.TemporaryDirectory(prefix='post-',dir=work) as td:
        temp=Path(td)
        if p.get('operation')=='layers':
            rate,frames,holds,details,_=layers(p,value,state,work,ffmpeg,ffprobe,temp,stack,references)
        elif p.get('operation')=='append':
            rate,frames,holds,details,body=append(p,work,ffmpeg,ffprobe,temp,stack)
        else:raise ValueError('operation must be layers or append')
        result=temp/'result.mp4';finish(temp/'video.mp4',temp/'audio.m4a',result,ffmpeg,rate,temp)
        observed,rr,nn=checked_media(ffprobe,result,temp)
        if rr!=rate or nn!=frames or abs(Fraction(observed['video']['duration'])-Fraction(frames,1)/rate)>Fraction(1,1000):raise ValueError('final frame/rate/duration mismatch')
        if abs(Fraction(observed['audio']['duration'])-Fraction(frames,1)/rate)>Fraction(1,1000):raise ValueError('final audio duration mismatch')
        cut.run([ffmpeg,'-v','error','-xerror','-nostdin','-i',result,'-f','null','-'],temp)
        meter=measured_audio(ffmpeg,result,temp);verify_audio(meter,p['audio'])
        if p['operation']=='append' and packet_hashes(ffprobe,body,temp)!=packet_hashes(ffprobe,result,temp)[:details['body_frames']]:raise ValueError('body coded video changed')
        for handle,expected in holds:
            if cut._sha256_handle(handle)!=expected:raise ValueError('input changed before publication')
        sha=digest(result);os.link(result,target)
    return {'status':'working_candidate','output':str(target),'sha256':sha,'frames':frames,'duration_seconds':frames/float(rate),
            'technical_status':'passed','semantic_status':'not_run','direct_listening':'not_run','user_approval':'pending',
            'loudness_lufs':float(meter['input_i']),'true_peak_dbtp':float(meter['input_tp']),**details}


def join_srt(body,outro,offset_ms,total_ms):
    if type(offset_ms) is not int or type(total_ms) is not int or not 0 < offset_ms < total_ms:raise ValueError('invalid SRT assembly duration')
    a,b=parse_srt(body),parse_srt(outro)
    if any('\x00' in line or '\ufffd' in line for c in a+b for line in c.text_lines):raise ValueError('invalid subtitle characters')
    validate_cues(a,media_end_ms=offset_ms);validate_cues(b,media_end_ms=total_ms-offset_ms)
    cues=a+[replace(c,index=len(a)+i,start_ms=c.start_ms+offset_ms,end_ms=c.end_ms+offset_ms) for i,c in enumerate(b,1)]
    validate_cues(cues,media_end_ms=total_ms)
    return _render(cues)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--plan',type=Path)
    cli.add_argument('--timeline-json',type=Path);cli.add_argument('--editorial-state-json',type=Path)
    cli.add_argument('--calibration-timeline-json',type=Path);cli.add_argument('--baseline-timeline-json',type=Path)
    cli.add_argument('--reference-timeline-json',type=Path,action='append',default=[])
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--body-srt',type=Path);cli.add_argument('--outro-srt',type=Path)
    cli.add_argument('--offset-ms',type=int);cli.add_argument('--total-ms',type=int)
    args=cli.parse_args();paths=cut.current_job_paths(cut.ROOT)
    if paths is None:raise ValueError('Run through creator_job.py run')
    target=cut.canonical(args.output)
    if not target.is_relative_to(paths['outputs']):raise ValueError('output must stay in current job')
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    if args.body_srt:
        if target.suffix!='.srt' or not args.outro_srt or args.offset_ms is None or args.total_ms is None:raise ValueError('SRT append requires exact offset and total duration')
        from video_editing.subtitle import _write_atomic
        with ExitStack() as stack:
            sources=[stack.enter_context(cut._locked_source(cut.canonical(path))) for path in (args.body_srt,args.outro_srt)]
            hashes=[cut._sha256_handle(f) for f in sources]
            payload=join_srt(args.body_srt,args.outro_srt,args.offset_ms,args.total_ms).encode('utf-8')
            if hashes != [cut._sha256_handle(f) for f in sources]:raise ValueError('subtitle input changed')
            _write_atomic(target,payload,overwrite=False)
        print(json.dumps({'status':'structure_checked','output':str(target),'semantic_status':'not_run'}));return
    if not args.plan:raise ValueError('--plan required')
    p=read(args.plan)
    if p['operation']=='layers' and (not args.timeline_json or not args.editorial_state_json):raise ValueError('original timeline/state required for layers')
    tools=cut.runtime_path('ffmpeg',cut.ROOT)/'bin'
    references=dict(calibration_reference=read(args.calibration_timeline_json) if args.calibration_timeline_json else None,
                    baseline_reference=read(args.baseline_timeline_json) if args.baseline_timeline_json else None,
                    reference_payloads=[read(p) for p in args.reference_timeline_json])
    result=execute(p,work=paths['work'],output=target,ffmpeg=tools/'ffmpeg.exe',ffprobe=tools/'ffprobe.exe',
                   value=read(args.timeline_json) if args.timeline_json else None,state=read(args.editorial_state_json) if args.editorial_state_json else None,references=references)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,RuntimeError,KeyError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
