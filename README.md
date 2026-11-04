# 콤보 타자기 (Combo Typer) + 온라인 리더보드

tkinter 코드 타자 콤보 게임 + 직접 만든 리더보드 REST API (FastAPI + SQLite).

## 파일

| 파일 | 역할 |
|---|---|
| `combo_typer.py` | 게임 (tkinter 창) |
| `leaderboard.py` | API 클라이언트 (urllib, 스레드 + after) |
| `server.py` | 리더보드 API 서버 (FastAPI, `scores.db`에 저장) |
| `plan.md` | 기획/체크리스트 |

## 실행

```bash
uv sync                          # 처음 한 번
uv run uvicorn server:app        # 터미널 1: 서버 (http://127.0.0.1:8000, 문서: /docs)
uv run python combo_typer.py     # 터미널 2: 게임
```

서버를 켜지 않아도 게임은 되고, 리더보드 자리에 "오프라인" 안내만 뜹니다.

## API

- `GET /scores?limit=10` → `[{"rank":1,"name":"...","score":610,"combo":28,"created":"..."}]`
- `POST /scores` body `{"name":"상훈","score":1234,"combo":42}` → `{"ok":true,"rank":1}`
  - name 1~12자, score 0~1,000,000 정수, combo 0~100,000 정수. 어기면 422

```bash
curl -X POST localhost:8000/scores -H 'Content-Type: application/json' -d '{"name":"상훈","score":1234,"combo":42}'
curl "localhost:8000/scores?limit=10"
```

## 진짜 "온라인"으로 만들기 (선택)

- **같은 와이파이(LAN)**: 서버 컴퓨터에서 `uv run uvicorn server:app --host 0.0.0.0`,
  `ipconfig getifaddr en0` 으로 IP 확인 후 친구 컴퓨터에서
  `LEADERBOARD_URL=http://<그 IP>:8000 uv run python combo_typer.py` (Windows PowerShell: `$env:LEADERBOARD_URL="http://<IP>:8000"`)
- **인터넷 공개**: Render / Railway 같은 무료 호스팅에 올리고 시작 명령을
  `uvicorn server:app --host 0.0.0.0 --port $PORT` 로 지정. (무료 플랜은 디스크가 초기화될 수 있어 SQLite 기록이 사라질 수 있음)
- 임시 공유는 `cloudflared tunnel --url http://localhost:8000` 같은 터널도 가능

## 참고

uv 가상환경에서 tkinter가 `init.tcl` 을 못 찾는 문제가 있어 `combo_typer.py` 맨 위에서 `TCL_LIBRARY`/`TK_LIBRARY`를 자동 설정합니다.
