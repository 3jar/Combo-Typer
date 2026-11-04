"""리더보드 API 클라이언트 (표준 라이브러리 urllib만 사용).
서버 주소는 환경변수 LEADERBOARD_URL, 없으면 http://127.0.0.1:8000"""
import json
import os
import queue
import threading
import urllib.error
import urllib.request

서버 = os.environ.get("LEADERBOARD_URL", "http://127.0.0.1:8000").rstrip("/")
타임아웃 = 3


def 점수보내기(이름, 점수, 콤보):
    """POST /scores → {"ok": True, "rank": n}. 실패하면 예외."""
    데이터 = json.dumps({"name": 이름, "score": 점수, "combo": 콤보}).encode()
    요청 = urllib.request.Request(서버 + "/scores", data=데이터, method="POST",
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(요청, timeout=타임아웃) as r:
        return json.loads(r.read())


def 순위가져오기(개수=10):
    """GET /scores?limit=n → [{rank, name, score, combo, created}, ...]"""
    with urllib.request.urlopen(f"{서버}/scores?limit={개수}", timeout=타임아웃) as r:
        return json.loads(r.read())


def 백그라운드(함수, 완료, 위젯, *인자):
    """horror_reader 방식: 네트워크는 스레드에서, 결과 확인은 tkinter after로 메인 스레드에서.
    (tkinter는 메인 스레드에서만 만지도록 큐로 넘긴다) 완료(결과, 에러메시지) 형태로 호출."""
    상자 = queue.Queue()

    def 일():
        try:
            상자.put((함수(*인자), None))
        except urllib.error.HTTPError as e:
            상자.put((None, f"서버가 거절함 ({e.code})"))
        except Exception:
            상자.put((None, f"서버 연결 실패 ({서버}) - 게임은 계속할 수 있어요"))

    def 확인():
        try:
            완료(*상자.get_nowait())
        except queue.Empty:
            위젯.after(100, 확인)

    threading.Thread(target=일, daemon=True).start()
    위젯.after(100, 확인)
