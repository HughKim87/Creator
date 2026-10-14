# Claude(Cowork) 연결 폴더용 실행 환경. Codex에서는 사용하지 않는다.
# 사용: source "$HOME/mnt/Creator/.agents/skills/coordinate-video-production/scripts/claude_runtime.sh"
#
# - git shim: worktree 메타데이터의 Windows 경로(예: D:/AI Agent/GitHub/X)를
#   마운트 경로($HOME/mnt/X)로 변환한다. 저장소 파일은 바꾸지 않는다.
# - CREATOR_HOST_PATH_MAP: check_worktree.py가 작업 기록에 Codex와 같은
#   Windows root 문자열을 남기도록 한다.
# - 모든 worktree가 같은 부모 폴더 아래에 있다고 가정한다. 다르면
#   CREATOR_WIN_PREFIX를 직접 지정한 뒤 source 한다.

_creator_mnt="$HOME/mnt/"
if [ -z "${CREATOR_WIN_PREFIX:-}" ]; then
  for _gd in "$_creator_mnt"*/.git/worktrees/*/gitdir; do
    [ -f "$_gd" ] || continue
    _wt="$(sed -n '1p' "$_gd")"          # D:/AI Agent/GitHub/Creator-x/.git
    _wt="${_wt%/.git}"                   # D:/AI Agent/GitHub/Creator-x
    CREATOR_WIN_PREFIX="${_wt%/*}/"      # D:/AI Agent/GitHub/
    break
  done
fi
if [ -z "${CREATOR_WIN_PREFIX:-}" ]; then
  echo "claude_runtime: Windows worktree 경로를 찾지 못했습니다. CREATOR_WIN_PREFIX를 지정하세요." >&2
  return 1 2>/dev/null || exit 1
fi
export CREATOR_WIN_PREFIX
_creator_host="${CREATOR_WIN_PREFIX//\//\\}"
export CREATOR_HOST_PATH_MAP="${_creator_mnt}=${_creator_host}"

_creator_shim="$HOME/.creator-shim/bin"
mkdir -p "$_creator_shim"
cat > "$_creator_shim/git" <<'SHIM'
#!/usr/bin/env bash
[ -n "${CREATOR_WIN_PREFIX:-}" ] || exec /usr/bin/git "$@"
WIN="$CREATOR_WIN_PREFIX"
MNT="$HOME/mnt/"
dir="$PWD"; prev=""
for a in "$@"; do [ "$prev" = "-C" ] && dir="$a"; prev="$a"; done
d="$(cd "$dir" 2>/dev/null && pwd -P)"
while [ -n "$d" ] && [ "$d" != "/" ]; do
  if [ -f "$d/.git" ]; then
    gd="$(sed -n 's/^gitdir: //p' "$d/.git")"
    case "$gd" in "$WIN"*) export GIT_DIR="$MNT${gd#"$WIN"}" GIT_WORK_TREE="$d";; esac
    break
  fi
  [ -d "$d/.git" ] && break
  d="$(dirname "$d")"
done
/usr/bin/git "$@" | sed "s#${WIN}#${MNT}#g"
exit "${PIPESTATUS[0]}"
SHIM
chmod +x "$_creator_shim/git"
case ":$PATH:" in *":$_creator_shim:"*) ;; *) export PATH="$_creator_shim:$PATH";; esac
export PYTHONDONTWRITEBYTECODE=1
unset _creator_mnt _gd _wt _creator_host _creator_shim
