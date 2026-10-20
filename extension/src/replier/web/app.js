const form = document.querySelector('#search-form');
const input = document.querySelector('#query');
const button = document.querySelector('#recommend');
const status = document.querySelector('#status');
const list = document.querySelector('#suggestions');
const source = document.querySelector('#source');
const empty = document.querySelector('#empty');
const selection = document.querySelector('#selection');
let busy = false;
let history = {query: '', cursor: 0, seen: []};
try {
  const saved = JSON.parse(localStorage.getItem('24hreplier:discovery') || 'null');
  if (saved && typeof saved.query === 'string' && Number.isInteger(saved.cursor) &&
      saved.cursor >= 0 && saved.cursor <= 1000000 && Array.isArray(saved.seen)) {
    history = {...saved, seen: saved.seen.filter(s => typeof s === 'string' && s.length <= 200).slice(-300)};
  }
} catch {}

function choose(term, url, card) {
  document.querySelectorAll('.term').forEach(el => {
    const chosen = el === card;
    el.classList.toggle('chosen', chosen);
    el.setAttribute('aria-pressed', String(chosen));
  });
  document.querySelector('#selected-term').textContent = term;
  document.querySelector('#youtube-link').href = url;
  selection.hidden = false;
  try { localStorage.setItem('24hreplier:selected', term); } catch {}
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  const query = input.value.trim();
  busy = true;
  button.disabled = true;
  button.textContent = '여러 게임 분야를 살펴보는 중…';
  status.textContent = '서로 다른 네 가지 주제로 YouTube 추천을 확인하고 있어요.';
  status.classList.remove('error');
  list.replaceChildren();
  source.hidden = true;
  empty.hidden = true;
  selection.hidden = true;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);
  try {
    const response = await fetch('/api/topics', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query, cursor: history.query === query ? history.cursor : 0, excluded: history.seen}),
      signal: controller.signal
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '추천을 가져오지 못했습니다.');
    history = {query, cursor: result.next_cursor,
      seen: [...history.seen, ...result.suggestions.map(item => item.term)].slice(-300)};
    try { localStorage.setItem('24hreplier:discovery', JSON.stringify(history)); } catch {}
    source.textContent = result.source + ' · 확인 ' + new Date(result.checked_at).toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'}) + ' KST';
    source.hidden = false;
    status.textContent = result.suggestions.length ? '새로운 게임 주제예요. 마음에 드는 검색어를 선택하세요.' : '이번 분야에는 아직 보지 않은 추천이 없어요. 한 번 더 눌러 다른 분야를 찾아보세요.';
    if (result.failed_sources) status.textContent += ' 일부 분야는 연결되지 않아 확인된 결과만 표시합니다.';
    empty.hidden = result.suggestions.length > 0;
    for (const item of result.suggestions) {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'term';
      card.setAttribute('aria-pressed', 'false');
      const content = document.createElement('span');
      const text = document.createElement('span');
      text.textContent = item.term;
      const origin = document.createElement('small');
      origin.className = 'term-origin';
      origin.textContent = '발견 경로 · ' + item.discovered_from;
      content.append(text, origin);
      const arrow = document.createElement('span');
      arrow.textContent = '↗';
      arrow.setAttribute('aria-hidden', 'true');
      card.append(content, arrow);
      card.addEventListener('click', () => choose(item.term, item.search_url, card));
      list.append(card);
    }
  } catch (error) {
    status.classList.add('error');
    status.textContent = error.name === 'AbortError' ? '조회 시간이 길어지고 있어요. 잠시 후 다시 눌러주세요.' : error.message;
  } finally {
    clearTimeout(timer);
    busy = false;
    button.disabled = false;
    button.textContent = '다른 게임 주제 추천받기 ↗';
  }
});
