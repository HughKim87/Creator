import json, re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent

def number(s):
    return None if s == '—' else float(s.replace(',', '').rstrip('%'))

text = (ROOT / 'studio-content-28d.txt').read_text(encoding='utf-8')
lines = [s.strip() for s in text.splitlines() if s.strip()]
start = lines.index('합계')
raw_totals = lines[start+1:start+8]
rows = []
i = start + 8
while i < len(lines) and re.fullmatch(r'\d+:\d{2}(?::\d{2})?', lines[i]):
    length, title = lines[i:i+2]
    values = lines[i+2:i+14]
    if len(values) != 12:
        raise ValueError((title, values))
    rows.append(dict(title=title, duration=length, engaged_views=number(values[0]),
                     views=number(values[2]), watch_hours=number(values[4]),
                     subscriber_net=number(values[6]), impressions=number(values[10]),
                     ctr_pct=number(values[11])))
    i += 14
assert len(rows) == 50, len(rows)

periods = {
 'growth_90d': dict(start='2026-04-28', end='2026-07-26', days=90, views=1035635, engaged_views=559334, watch_hours=16643.5, gained=593, lost=144, net=449, impressions=3183936, ctr_pct=7.0),
 'recent_90d': dict(start='2026-07-27', end='2026-10-24', days=90, views=56990, engaged_views=17690, watch_hours=384.4, gained=18, lost=21, net=-3, impressions=190955, ctr_pct=4.9),
 'recent_28d': dict(start='2026-09-27', end='2026-10-24', days=28, views=45540, engaged_views=12181, watch_hours=216.8, gained=10, lost=12, net=-2, impressions=135985, ctr_pct=3.9),
}
a,b = periods['recent_90d'], periods['recent_28d']
periods['preceding_62d'] = dict(start='2026-07-27',end='2026-09-26',days=62, derived=True,
    **{k:round(a[k]-b[k],4) for k in ['views','engaged_views','watch_hours','gained','lost','net']})
for p in periods.values():
    assert p['gained'] - p['lost'] == p['net']
    p['gained_per_day'] = p['gained']/p['days']
    p['lost_per_day'] = p['lost']/p['days']
    p['engaged_per_day'] = p['engaged_views']/p['days']
    p['acquisitions_per_1000_engaged'] = 1000*p['gained']/p['engaged_views']

sources90 = [
 ['YouTube 보기 페이지',7,0],['Shorts 피드',5,0],['YouTube 검색',1,0],
 ['기타',1,1],['구독 피드',0,1],['계정 삭제',1,3],['내 YouTube 채널',3,8],['구독 채널 목록',0,7]]
sources28 = [
 ['YouTube 보기 페이지',4,0],['Shorts 피드',3,0],['YouTube 검색',1,0],
 ['기타',0,0],['계정 삭제',1,2],['내 YouTube 채널',1,4],['구독 채널 목록',0,5]]
for items,key in [(sources90,'recent_90d'),(sources28,'recent_28d')]:
    assert sum(x[1] for x in items)==periods[key]['gained']
    assert sum(x[2] for x in items) <= periods[key]['lost']

uploads = [
 ['2026-07-04','서비스 종료하기 전, 신규 유저 받아라 !!! ㅋㅋㅋ','10:34'],
 ['2026-10-06','제우스 한 달, 초반엔 재밌었는데 왜 멤버십을 연장하지 않았을까?','11:49'],
 ['2026-10-09','영화 백룸 속에 직접 들어가 봤다','21:38'],
 ['2026-10-11','도깨비의세계 첫날 후기｜메인퀘만 밀었더니 산군대호에서 3번 막혔습니다','15:19'],
 ['2026-10-14','과금을 안 시키는 게 오히려 돈이 된다고? #도깨비의세계','14:50'],
 ['2026-10-14','도깨비의 세계 | 열심히 강화했는데 딜이 밀린다면? 이 덱부터 보세요','3:02'],
 ['2026-10-15','여러분이 궁금한 게임, 제가 대신 해드립니다｜댓글로 신청해주세요','4:42'],
 ['2026-10-21','사람 살리려다 제가 먼저 죽었습니다ㅋㅋ｜워독스 초보 메딕 적응기','20:30']]
gap=(date(2026,10,6)-date(2026,7,4)).days
assert gap==94

official = [
 dict(id='O1',title='YouTube 조회수 집계 변경',url='https://blog.youtube/inside-youtube/engaged-views-youtube-explained/',published='2026-08-19',effective='2026-08-24'),
 dict(id='O2',title='유효 조회·평균 시청 시간 정의',url='https://support.google.com/youtube/answer/9313698?hl=en'),
 dict(id='O3',title='구독 소스의 의미',url='https://support.google.com/youtube/answer/9717879?hl=en'),
 dict(id='O4',title='신규·일반·고정 시청자 정의',url='https://support.google.com/youtube/answer/10246996?hl=en'),
 dict(id='O5',title='CTR 해석 시 주의점',url='https://support.google.com/youtube/answer/7628154?hl=en'),
 dict(id='O6',title='유지율과 유사 길이 비교',url='https://support.google.com/youtube/answer/9314415'),
 dict(id='O7',title='제목·썸네일 A/B 테스트',url='https://support.google.com/youtube/answer/16391400?hl=en'),
 dict(id='O8',title='형식별 시청자 겹침 정의',url='https://support.google.com/youtube/answer/12942217?co=YOUTUBE._YTVideoType%3Dvideo&hl=en')]
for s in official:s['verified_on_kst']='2026-10-26'

evidence = [
 dict(id='E01',claim='성장기와 최근 90일의 구독 증감',kind='직접 관측',source='studio-90d-comparison.txt',period='성장기 2026-04-28~07-26 / 최근 2026-07-27~10-24',limitation='비교 표의 콘텐츠는 상위 50개; 합계는 화면 표시 채널 합계. 형식 혼합.'),
 dict(id='E02',claim='최근 28일 동일 열 구성 상세 지표',kind='직접 관측',source='studio-detail-28d.txt',period='2026-09-27~10-24',limitation='다른 보고서의 조회수 합계와 38회, 유효 조회수와 5회 차이가 관측됨. 원인 미확정.'),
 dict(id='E03',claim='최근 28일 유효 조회수순 콘텐츠 50개',kind='직접 관측',source='studio-content-28d.txt',period='2026-09-27~10-24',limitation='관측 당시 전체 조회 45,578 / 유효 12,186; 이후 상세 표와 소폭 다름. 전체 영상 전수 아님.'),
 dict(id='E04',claim='일반 영상 게시 사이 94일 공백',kind='직접 관측+날짜 계산',source='studio-upload-dates.txt',period='2026-07-04~10-06',limitation='현재 보이는 공개 일반 영상 기준. Shorts·라이브 전체 무활동을 뜻하지 않음. 삭제·과거 공개 상태 이력 미확인.'),
 dict(id='E05',claim='Shorts 27개가 10월 10~14일 집중 게시',kind='직접 관측',source='studio-shorts-dates.txt',period='2026-10-10~14',limitation='집중 게시가 추천 불이익이나 이탈을 유발했다는 인과 증거 없음.'),
 dict(id='E06',claim='신청 영상은 현재 전체 79회, 순 시청자 18명, 노출 676, CTR 3.1%',kind='직접 관측',source='https://studio.youtube.com/video/Ms1PaHog3BM/analytics/tab-reach_viewers/period-default',period='2026-10-15~확인 시점',limitation='순 시청자는 추정치. 일부 상세 카드 10/24까지: 노출 673, CTR 3.0%, 노출발 유효 20. 기간 혼합 금지.'),
 dict(id='E07',claim='신청 영상의 같은 기간 유효 조회 32, 전체 76, 평균 1:08, 평균 조회율 24.4%',kind='직접 관측',source='studio-detail-90d.txt',period='2026-07-27~10-24 (영상 게시 10/15)',limitation='상단 게시 이후 전체 79회와 집계 끝점이 다름. 이탈 곡선·전체 발화 분석 미완료.'),
 dict(id='E08',claim='스텔라 블레이드 매우 어려움 엔딩 요청 1건과 크리에이터 답글 확인',kind='직접 관측',source='https://studio.youtube.com/video/Ms1PaHog3BM/comments/inbox',period='2026-10-26 확인',limitation='미응답 필터 해제 후 확인. 사용자 계정명은 보존하지 않음. 총 댓글 수는 고유 요청자 수가 아님.'),
 dict(id='E09',claim='워독스 본편: 전체 22회, 유효 9회, 순 시청자 6명, 노출 167, CTR 3.6%',kind='직접 관측',source='studio-wardogs-reach.txt',period='2026-10-21~확인 시점',limitation='유효 9회는 studio-wardogs-engagement.txt. 유지율 그래프 데이터 부족. 품질 비교 결론 유보.'),
 dict(id='E10',claim='7시간29분 워독스 라이브 및 여러 현재 비공개 다시보기',kind='직접 관측',source='studio-live-dates.txt',period='2026-10-18 등',limitation='방송 당시의 공개 상태와 비공개 전환 시점은 미확인. 비공개가 하락 원인이라고 단정하지 않음.'),
 dict(id='E11',claim='최근 90일 구독 소스: 증가18, 감소21, 계정삭제 행 순감 -2',kind='직접 관측',source='studio-subscription-sources-90d.txt',period='2026-07-27~10-24',limitation='취소 위치는 취소 동기가 아님. 계정삭제 행에도 증가1·감소3이 함께 표시됨.'),
 dict(id='E12',claim='최근28일 신규90.2%, 일반9.8%, 고정<0.1%; 형식 겹침1%',kind='앞선 동일 대화에서 직접 관측',source='https://studio.youtube.com/channel/UCp9Pn5dAUByhBDkH1K59HiQ/analytics/tab-build_audience/period-default',period='2026-09-27~10-24',limitation='겹침1%는 재방문 시청자 중 동영상·Shorts 양쪽 시청 비중. Shorts→본편 이동률 아님. 절대 인원 미확인.'),
 dict(id='E13',claim='도깨비 경제 영상의 현재 누적 평균1:39, 30초유지47%, 종료화면클릭0%',kind='앞선 동일 대화에서 직접 관측',source='https://studio.youtube.com/video/IDA9FbXDSmQ/analytics/tab-interest_viewers/period-default',period='2026-10-14~확인 시점',limitation='47%는 Studio에서 일반적 실적으로 표시. 종료화면 노출 횟수 미확인. 전체 영상 음성·장면별 원인 미검증.'),
 dict(id='E14',claim='리니지 플레이 종료, 함께 궁금한 게임을 하는 방향, 주15~20시간, 광고 없음',kind='사용자 설명',source='2026-10-26 현재 대화의 사용자 답변',period='현재 운영 제약',limitation='정확한 리니지 종료 날짜는 미지정. 삭제 없음은 사용자의 기억에 따른 설명. 공개상태 변경 이력은 별도 미확인.'),
 dict(id='E15',claim='모집 영상 0:07의 인포그래픽 화면 및 설명의 최대3시간 조건',kind='직접 관측',source='request-intro-00m07s.png',period='정지 화면 0:07 / 설명 확인 2026-10-26',limitation='한 프레임과 설명 검토. 영상 전체가 같은 형식이라는 검증이나 음성 평가 아님.'),
 dict(id='E16',claim='신규 구독 감소가 순증 하락을 대부분 설명',kind='계산',source='E01',period='두 90일 비교',limitation='회계적 분해이며 신규 유입 감소의 원인 분해가 아님.'),
]
growth,recent=periods['growth_90d'],periods['recent_90d']
calcs = dict(
 gain_change=recent['gained']-growth['gained'],
 loss_change=recent['lost']-growth['lost'],
 net_change=recent['net']-growth['net'],
 gains_decline_pct=100*(1-recent['gained']/growth['gained']),
 losses_decline_pct=100*(1-recent['lost']/growth['lost']),
 engaged_decline_pct=100*(1-recent['engaged_views']/growth['engaged_views']),
 impressions_decline_pct=100*(1-recent['impressions']/growth['impressions']),
 loss_improvement= growth['lost']-recent['lost'],
 gap_days=gap,
 recent_28_vs_62_engaged_daily_ratio=periods['recent_28d']['engaged_per_day']/periods['preceding_62d']['engaged_per_day'],
 recent_28_vs_62_gains_daily_ratio=periods['recent_28d']['gained_per_day']/periods['preceding_62d']['gained_per_day'],
 current28_excluding_closed_net=-2-(1-2),
 current90_excluding_closed_net=-3-(1-3),
 request_impression_engaged_views_estimate=673*.03,
 war_impression_engaged_views_estimate=163*.031,
)
assert calcs['gain_change']+calcs['loss_improvement']==calcs['net_change']==-452

data=dict(schema='kim-silver-channel-audit-v1',observed_on_kst='2026-10-26',
 channel=dict(id='UCp9Pn5dAUByhBDkH1K59HiQ',name='신입 아재 유튜버, 김실버😎',current_subscribers=599),
 provenance='현재 대화에서 UI로 직접 확인한 값과 사용자 설명. 브라우저 비공개 API·쿠키·자격증명 접근 없음. 외부 게시·메타데이터 수정 없음.',
 reporting_caveat='기간합계는 동일 열 구성 상세 보고서를 기준으로 계산. 개요/유효조회수 단독 표에는 최근28일45,578·12,186, 최근90일57,028·384.5시간이 따로 표시됨. 차이를 보존하며 원인은 확정하지 않음.',
 periods=periods,calculations=calcs,subscription_sources_90d=sources90,subscription_sources_28d=sources28,
 subscription_source_reconciliation=dict(recent_90d_unexplained_loss_difference=21-sum(x[2] for x in sources90),recent_28d_unexplained_loss_difference=12-sum(x[2] for x in sources28),note='각 표의 표시 행 감소수 합계는 총계보다 1 작음. 이를 특정 소스로 배정하지 않음.'),
 uploads=uploads,content_sample_28d=rows,official_sources=official,evidence=evidence,
 author_constraints=dict(return_to_lineage=False,weekly_hours=[15,20],recording_cap_hours=3,paid_ads_reported=False,
 desired_direction='사람들과 궁금한 게임을 함께 진행·플레이하고 결과를 영상으로 공유',user_game_request_confirmed=1),
 limitations=['독립된 복수 분석가 검증은 실시하지 않음','일별 전체 CSV와 게시후 동일7일 코호트 미확보','개별 시청자의 이탈 이유·시청자별 이동 경로 미확인','전체 영상 음성 및 프레임별 편집 감사 미실시','경쟁 채널의 비공개 지표 미확보'])
(ROOT/'evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(rows=len(rows),calculations=calcs),ensure_ascii=False,indent=2))
