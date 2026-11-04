"""Supabase REST 리더보드 클라이언트 + 로컬 settings.json 읽기/쓰기 (표준 라이브러리 urllib만 사용).
설정값: 환경변수 SUPABASE_URL, SUPABASE_ANON_KEY (없으면 아래 기본값).
anon(public) 키만 사용한다. service_role 키는 절대 여기에 넣지 않는다."""
import json
import os
import queue
import threading
import urllib.error
import urllib.request

주소 = os.environ.get("SUPABASE_URL", "https://ainmgjpvxyebxxqivxwz.supabase.co").rstrip("/")
키 = os.environ.get("SUPABASE_ANON_KEY", "sb_publishable_pXWW-h-KAjDr7x9YomYKMA_QAiAVXYa")
타임아웃 = 4
설정파일 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
기본설정 = {"name": "", "time": 60, "shake": True, "best": {"easy": 0, "normal": 0, "hard": 0}}


def 설정읽기():
    """settings.json 을 읽는다. 없거나 깨졌으면 기본값. 빠진 항목은 기본값으로 채운다."""
    설정 = json.loads(json.dumps(기본설정))
    try:
        with open(설정파일, encoding="utf-8") as f:
            저장 = json.load(f)
        best = {**설정["best"], **저장.pop("best", {})}
        설정.update(저장)
        설정["best"] = best
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    return 설정


def 설정저장(설정):
    try:
        with open(설정파일, "w", encoding="utf-8") as f:
            json.dump(설정, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 저장 실패해도 게임은 계속


def _요청(경로, 방식="GET", 본문=None, 헤더=None):
    """Supabase REST 호출 → (응답 헤더, 응답 본문 bytes). 실패하면 예외."""
    if "YOUR" in 주소 or "YOUR" in 키:
        raise RuntimeError("Supabase 미설정 (README 참고) - 게임은 계속할 수 있어요")
    헤더 = {"apikey": 키, "Authorization": f"Bearer {키}", **(헤더 or {})}
    데이터 = json.dumps(본문).encode() if 본문 is not None else None
    if 데이터:
        헤더["Content-Type"] = "application/json"
    요청 = urllib.request.Request(f"{주소}/rest/v1/{경로}", data=데이터, method=방식, headers=헤더)
    with urllib.request.urlopen(요청, timeout=타임아웃) as r:
        return r.headers, r.read()


def 순위가져오기(모드, 개수=10):
    """TOP n (점수 내림차순) → [{name, score, combo, created_at}, ...]"""
    경로 = f"scores?select=name,score,combo,created_at&mode=eq.{모드}&order=score.desc&limit={개수}"
    return json.loads(_요청(경로)[1])


def 점수보내기(이름, 점수, 콤보, 모드):
    """점수 등록 후 같은 모드에서 내 순위 계산 → {"rank": n}"""
    _요청("scores", "POST", {"name": 이름, "score": 점수, "combo": 콤보, "mode": 모드},
          {"Prefer": "return=minimal"})
    헤더, _ = _요청(f"scores?select=id&mode=eq.{모드}&score=gt.{점수}", "HEAD", 헤더={"Prefer": "count=exact"})
    위 = int(헤더.get("Content-Range", "*/0").split("/")[-1])  # 나보다 높은 점수 개수
    return {"rank": 위 + 1}


def 백그라운드(함수, 완료, 위젯, *인자):
    """horror_reader 방식: 네트워크는 스레드에서, 결과 확인은 tkinter after 로 메인 스레드에서.
    완료(결과, 에러메시지) 형태로 호출된다."""
    상자 = queue.Queue()

    def 일():
        try:
            상자.put((함수(*인자), None))
        except urllib.error.HTTPError as e:
            상자.put((None, f"서버가 거절함 ({e.code}) - 이름/점수 범위 또는 테이블 설정을 확인하세요"))
        except RuntimeError as e:
            상자.put((None, str(e)))
        except Exception:
            상자.put((None, "오프라인 - 인터넷 연결을 확인하세요 (게임은 계속할 수 있어요)"))

    def 확인():
        try:
            결과 = 상자.get_nowait()
        except queue.Empty:
            try:
                위젯.after(100, 확인)
            except Exception:
                pass  # 그 사이 창이 닫힘
            return
        완료(*결과)

    threading.Thread(target=일, daemon=True).start()
    위젯.after(100, 확인)
