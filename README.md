# 콤보 타자기 (Combo Typer) v2 — 메인 메뉴 + Supabase 온라인 리더보드

tkinter 코드 따라 치기 콤보 게임. 점수는 Supabase(REST API)에 모여서 친구들과 같은 순위표를 봅니다.
클라이언트는 표준 라이브러리(`urllib`)만 사용합니다 (외부 패키지 없음).

## 파일

| 파일 | 역할 |
|---|---|
| `combo_typer.py` | 실행 진입점 + 메뉴/난이도/결과/리더보드/설정 화면 전환 |
| `game.py` | 게임 화면: 스니펫, 콤보, 점수, 흔들림, 난이도 데이터 |
| `leaderboard.py` | Supabase REST 클라이언트 + 스레드/after 도우미 + `settings.json` 읽기/쓰기 |
| `plan.md` | 기획/체크리스트 |

## Supabase 설정 (처음 한 번)

1. https://supabase.com 에서 새 프로젝트 생성 (예: `combo-typer`)
2. SQL Editor 에서 실행:

```sql
create table public.scores (
  id bigint generated always as identity primary key,
  name text not null check (char_length(name) between 1 and 12),
  score integer not null check (score between 0 and 1000000),
  combo integer not null check (combo between 0 and 100000),
  mode text not null default 'normal',
  created_at timestamptz not null default now()
);
alter table public.scores enable row level security;
create policy "anyone can read"   on public.scores for select to anon using (true);
create policy "anyone can insert" on public.scores for insert to anon with check (true);
```

3. Project Settings → API 에서 **Project URL** 과 **anon public 키**를 복사
   (⚠️ `service_role` 키는 절대 코드/깃에 넣지 마세요)
4. 환경변수로 지정하거나 `leaderboard.py` 위쪽 기본값을 바꿉니다:

```bash
export SUPABASE_URL="https://<ref>.supabase.co"
export SUPABASE_ANON_KEY="<anon key>"
```

설정하지 않으면 게임은 되지만 리더보드에 "Supabase 미설정" 안내만 뜹니다.

## 실행

```bash
uv sync
uv run python combo_typer.py
```

## 게임 방법

- 메인 메뉴: 게임 시작 / 리더보드 / 설정 / 종료 (내 최고 기록 표시)
- 난이도: 쉬움(짧은 단어) / 보통(한 줄 코드) / 어려움(긴 코드, 리셋시간 짧음)
- 정타마다 콤보 +1, 콤보 10마다 배율 +1 (최대 x5), 콤보 30 이상이면 화면 흔들림
- 오타 또는 리셋시간 동안 입력 없음 → COMBO BREAK. ESC: 일시정지
- 시간이 끝나면 결과(점수·최대 콤보·정확도·CPM) → 닉네임 입력 → [등록] → "현재 N위"
- 설정(게임 시간 30/60/90초, 화면 흔들림, 닉네임)과 개인 최고 기록은 `settings.json` 에 저장

## 사용하는 API (Supabase REST)

헤더: `apikey` / `Authorization: Bearer <anon key>`

- TOP 10: `GET /rest/v1/scores?select=name,score,combo,created_at&mode=eq.normal&order=score.desc&limit=10`
- 등록: `POST /rest/v1/scores` body `{"name","score","combo","mode"}`
- 내 순위: `HEAD /rest/v1/scores?mode=eq.normal&score=gt.<내점수>` + `Prefer: count=exact` → `Content-Range` 의 개수 + 1

네트워크 요청은 스레드에서 보내고 `queue` + `after()` 로 결과를 화면에 반영해서 창이 멈추지 않습니다.
오프라인이면 안내문만 뜨고 게임은 계속됩니다.

## 참고

uv 가상환경에서 tkinter가 `init.tcl` 을 못 찾는 문제가 있어 `combo_typer.py` 맨 위에서 `TCL_LIBRARY`/`TK_LIBRARY`를 자동 설정합니다.
