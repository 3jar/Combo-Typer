# 콤보 타자기 v2 — 메인 메뉴 + Supabase 온라인 리더보드 (개발 문서)

> 상태: **기획 확정 대기** (이 문서 확인 후 개발 시작). 현재 코드(v1: tkinter 게임 + FastAPI 자체 서버)는 커밋 `9fd36a0`.

## 뭘 만들고 싶은지

3주차에 기획한 CodeCombo(코드 따라 치기 콤보 게임)를 tkinter 창 게임으로 만들고,
**API(Supabase REST)** 로 온라인 리더보드를 붙인다. 게임을 켜면 **메인 메뉴**에서
게임 시작 / 리더보드 보기 / 설정 등을 고를 수 있다.
(11/5 과제: "5주차 실습 과제에 API 추가해보기 + Git으로 프로젝트 업데이트하기")

## 누가 씀

타자 연습을 게임처럼 하고 싶은 나와 친구들. 같은 Supabase 프로젝트에 점수가 모여서
각자 컴퓨터에서 실행해도 같은 순위표를 본다.

## 아키텍처 결정: 자체 FastAPI 서버 → Supabase

| | v1 자체 서버 (FastAPI) | v2 Supabase |
|---|---|---|
| 서버 실행 | 내가 켜 둬야 함 | 항상 켜져 있음 (호스팅) |
| 진짜 "온라인" | LAN/배포 필요 | 바로 인터넷 공유 |
| 프레임워크 규칙 | FastAPI가 "프레임워크 금지"에 걸릴 수 있음 | 클라이언트는 `urllib`로 HTTP만 보냄 → 프레임워크 없음 |
| 파일 수 | 서버 파일 1개 차지 | 서버 코드 없음 |

→ **Supabase 채택.** `server.py` 와 `fastapi`/`uvicorn` 의존성은 삭제. 클라이언트는 표준 라이브러리만 사용(`dependencies = []`).

### Supabase 사용 방식

- 테이블 `scores` (Supabase SQL Editor에서 한 번 실행):
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
  -- update/delete 정책은 만들지 않음 → anon은 수정·삭제 불가
  ```
- 요청 (헤더: `apikey: <anon key>`, `Authorization: Bearer <anon key>`)
  - TOP 10: `GET https://<ref>.supabase.co/rest/v1/scores?select=name,score,combo,created_at&order=score.desc&limit=10`
    (모드별: `&mode=eq.hard`)
  - 등록: `POST /rest/v1/scores` + `Content-Type: application/json`, `Prefer: return=representation`, body `{"name","score","combo","mode"}`
  - 내 순위: `HEAD /rest/v1/scores?score=gt.<내점수>` + `Prefer: count=exact` → `Content-Range` 헤더의 개수 + 1
- 설정값: `SUPABASE_URL`, `SUPABASE_ANON_KEY` 를 환경변수로 받고, 없으면 코드 안의 기본값 사용
- 보안: **anon(public) 키는 클라이언트에 들어가도 되는 키**(RLS로 보호). **service_role 키는 절대 코드/깃에 넣지 않는다.**
  RLS 체크 제약으로 이름 길이·점수 범위는 서버(DB)에서도 검증된다. 점수 조작 방지는 범위 밖.
- 네트워크는 horror_reader 방식: 스레드에서 요청 → `queue` + `after()` 로 메인 스레드에서 화면 갱신. 실패 시 오프라인 안내만 띄우고 게임은 계속.

## 한번 켜서 끝까지

1. 켜면 **메인 메뉴**: [게임 시작] [리더보드] [설정] [종료] + 내 최고 기록 표시
2. 게임 시작 → (난이도 선택: 쉬움/보통/어려움) → 60초 동안 코드 스니펫 따라 치기
   - 정타마다 콤보 +1, 콤보 10마다 배율 +1 (최대 x5), 콤보 30 이상 화면 흔들림
   - 오타 또는 리셋시간 동안 입력 없음 → COMBO BREAK
   - ESC: 일시정지/메뉴로
3. 시간 끝 → 결과 화면 (점수, 최대 콤보, 정확도, 내 최고 기록 갱신 여부) → 닉네임(지난번 이름 자동 입력) → [등록] → "현재 N위"
4. 리더보드 화면: TOP 10 (난이도 탭), [새로고침] [메뉴로]. 오프라인이면 안내문
5. 설정 화면: 게임 시간(30/60/90초), 화면 흔들림 켜기/끄기, 닉네임 → `settings.json` 에 저장
6. 종료: 창 닫기 / [종료]. 설정·최고 기록은 로컬 파일에 남고, 점수는 Supabase에 남는다

## 필수 구현

- 메인 메뉴 화면과 화면 전환 (메뉴 / 게임 / 결과 / 리더보드 / 설정)
- v1 게임 로직 유지 (스니펫, 콤보, 배율, 브레이크, 흔들림, 남은 시간)
- Supabase REST: TOP 10 조회, 점수 등록, 등록 후 순위 표시
- 백그라운드 스레드 + `after` 로 네트워크 처리, 실패 시 오프라인 안내 (게임은 계속)
- 로컬 `settings.json` (상대 경로, 프로젝트 폴더): 닉네임 기억, 개인 최고 기록, 게임 시간, 흔들림 on/off
- 난이도 = 스니펫 묶음 3종 (쉬움: 짧은 단어 / 보통: 한 줄 코드 / 어려움: 긴 코드) + 리셋시간 차등

## 선택 구현 (시간 남으면)

- 결과 화면 정확도(%)·타수(CPM) 표시 → 리더보드에는 점수만
- 리더보드 난이도 탭 (모드별 순위)
- 정타/브레이크 효과음 (`root.bell()` 정도, 외부 파일 없이)
- 카운트다운 3-2-1 시작 연출
- 게임 중 ESC 일시정지

## 구현 필요 없는 부분

- 로그인/회원가입, 점수 조작 방지, 점수 삭제·수정 기능
- 자체 서버 (FastAPI 삭제), 웹 페이지
- 외부 사운드/이미지 파일, BGM 박자 판정
- 패키징(exe/app 빌드)

## 파일 구조 (최대 3개, 각 200줄 이하)

| 파일 | 역할 | 예상 줄 수 |
|---|---|---|
| `combo_typer.py` | 실행 진입점 + 메인 메뉴/리더보드/설정/결과 화면 전환 | ~180 |
| `game.py` | 게임 화면: 스니펫, 콤보, 점수, 흔들림, 난이도 데이터 | ~170 |
| `leaderboard.py` | Supabase REST 클라이언트 (urllib) + 스레드/after 도우미 + settings.json 읽기/쓰기 | ~110 |

삭제: `server.py`, `pyproject.toml` 의 `fastapi`/`uvicorn` (→ `uv lock` 다시). `.gitignore` 에 `settings.json` 추가.
기타: `plan.md`, `README.md`(Supabase 설정 방법·SQL 포함), `chat.md`(AI 대화 원문), `pyproject.toml`, `uv.lock`, `.python-version`.

## 확인할 것 (사용자 / Canvas)

1. 외부 호스팅 API(Supabase)를 "API 추가"로 인정하는지 (공지에는 "API 추가해보기"만 있음)
2. 이번 과제에 보고서가 필요한지 (5주차는 A8/B6/C6 + 형식 감점이었음)
3. `chat.md` (AI 대화 원문, 요약 금지) 제출 필요 여부 → 일단 넣는 것으로 준비
4. 제출 형식: GitHub 저장소 링크인지 zip인지 (기말은 Git 저장소 제출)
5. Supabase 프로젝트: 기존 GreenLantern / MuseCalendar 는 둘 다 일시정지(INACTIVE) 상태 → **새 프로젝트 `combo-typer` 생성 권장** (사용자 확인 후)
6. anon 키를 저장소에 넣어도 될지 (공개 저장소면 누구나 점수 등록 가능 — 과제용으로는 허용 범위로 판단)

## 체크리스트

### 메뉴 / 화면
- [ ] 켜면 메인 메뉴가 뜨고 [게임 시작] [리더보드] [설정] [종료] 버튼이 있다
- [ ] 메인 메뉴에 내 최고 기록이 보인다
- [ ] 각 화면에서 [메뉴로] 로 돌아올 수 있다

### 게임
- [ ] 난이도 3종 중 고르면 해당 스니펫 묶음으로 시작한다
- [ ] 친 글자는 초록, 오타는 빨강으로 표시된다
- [ ] 정타마다 콤보 +1, 오타 시 COMBO BREAK
- [ ] 리셋시간 동안 입력 없으면 콤보 리셋
- [ ] 콤보 10마다 배율 +1 (최대 x5), 점수·남은 시간 표시
- [ ] 콤보 30 이상 화면 흔들림 (설정에서 끄면 안 흔들림)
- [ ] 시간이 끝나면 결과 화면 (점수, 최대 콤보, 최고 기록 갱신 여부)

### API (Supabase)
- [ ] 결과 화면에서 닉네임 입력 후 [등록] → Supabase `scores` 에 행이 생긴다
- [ ] 등록 후 "현재 N위" 가 표시된다
- [ ] 리더보드 화면에서 TOP 10 이 점수 내림차순으로 보인다
- [ ] 닉네임 1~12자가 아니면 등록되지 않고 안내가 뜬다
- [ ] 요청 중에도 창이 멈추지 않는다 (스레드 + after)
- [ ] 인터넷을 끄면 "오프라인" 안내만 뜨고 게임은 정상 진행
- [ ] service_role 키가 코드·깃에 없다

### 로컬 저장
- [ ] 닉네임이 다음 실행 때 자동으로 채워진다
- [ ] 최고 기록·설정이 `settings.json` (상대 경로)에 저장된다

### 과제 형식
- [ ] 파일 3개 이하, 각 200줄 이하, 다중 상속·프레임워크 없음
- [ ] uv 프로젝트 (pyproject.toml, uv.lock, .python-version), .venv/__pycache__ 제외
- [ ] 다른 폴더에 복사 → .venv 없이 `uv run python combo_typer.py` 실행 확인
- [ ] chat.md, README, Git 커밋 정리 후 GitHub 푸시
