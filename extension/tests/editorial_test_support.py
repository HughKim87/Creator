"""Synthetic delivery setup only; never generates a production editorial plan."""
from video_editing.editorial_state import derive_omissions, editorial_basis_fingerprint
from video_editing.timeline_v2 import editorial_fingerprint, source_manifest_fingerprint


def synthetic_state(v):
    clips = v['sequence']['video_clips'] + v['sequence']['audio_clips']
    a, b = min(c['source_in'] for c in clips), max(c['source_out'] for c in clips)
    anchors = []
    for track in ('video', 'audio'):
        c = v['sequence'][track + '_clips'][0]
        anchors.append(dict(id='first-' + track, source_in=c['source_in'], source_out=c['source_in']+1, media_scope=track, observation='Synthetic fixture frame; not actual media review'))
    s = dict(version='editorial-state-v1', source_manifest_fingerprint=source_manifest_fingerprint(v['source_manifest']), generation=1,
             scenes=[dict(id='fixture-scene', source_in=a, source_out=b, show='Synthetic scene', viewer_learns='Fixture relationship', next_action_reason='Fixture continuation', depends_on=[], anchors=anchors)], feedback=[], reviews=[])
    refresh_review(v, s)
    return s


def refresh_review(v, s):
    s['reviews'] = [dict(editorial_fingerprint=editorial_fingerprint(v), state_basis_fingerprint=editorial_basis_fingerprint(s), generation=s['generation'], omissions=[dict(d, reason='Synthetic redundancy', observation='Synthetic source interval inspected for fixture only', certainty='confirmed') for d in derive_omissions(v,s)], resolutions=[])]
    return s
