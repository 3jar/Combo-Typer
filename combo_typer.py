"""콤보 타자기 (tkinter) — 3주차 CodeCombo 기획을 GUI로 옮기고 온라인 리더보드를 붙인 버전.
실행: uv run python combo_typer.py   (리더보드 서버: uv run uvicorn server:app)"""
import os
import random
import sys
import time
import tkinter as tk

# uv 가상환경에서 Tcl/Tk 라이브러리를 못 찾는 문제(init.tcl 오류) 우회
for 이름, 폴더 in (("TCL_LIBRARY", "tcl9.0"), ("TK_LIBRARY", "tk9.0")):
    경로 = os.path.join(sys.base_prefix, "lib", 폴더)
    if 이름 not in os.environ and os.path.isdir(경로):
        os.environ[이름] = 경로

import leaderboard

게임시간 = 60       # 한 판 길이(초)
리셋시간 = 1.5      # 이 시간 안에 다음 정타가 없으면 콤보 리셋
임계값 = 30         # 이 콤보 이상이면 화면 흔들림 + 색 변화

스니펫목록 = [
    "def add(a, b): return a + b", "for i in range(10): print(i * i)",
    "names = ['kim', 'lee', 'park']", "total = sum([3, 1, 4, 1, 5])",
    "sign = 'plus' if x > 0 else 'minus'", "squares = [x ** 2 for x in range(5)]",
    "with open('memo.txt') as f: text = f.read()", "while count < 3: count += 1",
    "number = random.randint(1, 6)", "class Dog: pass",
]


def 배율(콤보):
    """콤보 10마다 배율 +1 (최대 x5)."""
    return min(1 + 콤보 // 10, 5)


class 게임:
    def __init__(self, 창):
        self.창 = 창
        창.title("콤보 타자기")
        창.geometry("720x460")
        창.configure(bg="#111")
        self.위 = tk.Label(창, font=("Menlo", 14), fg="#aaa", bg="#111")
        self.위.pack(pady=8)
        self.글 = tk.Text(창, font=("Menlo", 20), height=2, width=44, bg="#111", fg="#666",
                         bd=0, highlightthickness=0, cursor="arrow")
        self.글.tag_config("정", foreground="#4f4")
        self.글.tag_config("현", background="#555", foreground="#fff")
        self.글.tag_config("오", background="#a22", foreground="#fff")
        self.글.pack(pady=20)
        self.콤보표시 = tk.Label(창, font=("Menlo", 36, "bold"), fg="#fff", bg="#111")
        self.콤보표시.pack()
        self.메시지 = tk.Label(창, font=("Menlo", 13), fg="#f55", bg="#111")
        self.메시지.pack(pady=6)
        self.아래 = tk.Frame(창, bg="#111")
        self.아래.pack(fill="both", expand=True)
        창.bind("<Key>", self.키)
        self.시작화면()

    def 아래비우기(self):
        for w in self.아래.winfo_children():
            w.destroy()

    def 시작화면(self):
        self.진행중, self.끝화면 = False, False
        self.위.config(text=f"{게임시간}초 동안 코드를 따라 치세요.  Enter: 시작")
        self.글.config(state="normal"); self.글.delete("1.0", "end"); self.글.config(state="disabled")
        self.콤보표시.config(text="COMBO TYPER")
        self.메시지.config(text="")
        self.아래비우기()
        self.순위표시()

    def 시작(self):
        self.아래비우기()
        self.진행중, self.점수, self.콤보, self.최대콤보 = True, 0, 0, 0
        self.마지막정타 = 0.0
        self.끝시각 = time.time() + 게임시간
        self.오타 = False
        self.새스니펫()
        self.틱()

    def 새스니펫(self):
        self.스니펫 = random.choice([s for s in 스니펫목록 if s != getattr(self, "스니펫", "")])
        self.위치 = 0
        self.그리기()

    def 그리기(self):
        t = self.글
        t.config(state="normal"); t.delete("1.0", "end"); t.insert("1.0", self.스니펫)
        t.tag_add("정", "1.0", f"1.{self.위치}")
        t.tag_add("오" if self.오타 else "현", f"1.{self.위치}", f"1.{self.위치 + 1}")
        t.config(state="disabled")
        남은 = max(0, int(self.끝시각 - time.time()))
        self.위.config(text=f"점수 {self.점수}   최대콤보 {self.최대콤보}   남은시간 {남은}s")
        색 = "#ff0" if self.콤보 >= 임계값 else "#fff"
        self.콤보표시.config(text=f"{self.콤보} COMBO  x{배율(self.콤보)}", fg=색)

    def 틱(self):
        if not self.진행중:
            return
        지금 = time.time()
        if self.콤보 and 지금 - self.마지막정타 > 리셋시간:
            self.브레이크("시간 초과")
        if 지금 >= self.끝시각:
            return self.종료()
        self.그리기()
        self.창.after(100, self.틱)

    def 키(self, e):
        if not self.진행중:
            if e.keysym == "Return" and not self.끝화면:
                self.시작()
            return
        c = e.char
        if not c or not c.isprintable():
            return
        if c == self.스니펫[self.위치]:
            self.콤보 += 1
            self.최대콤보 = max(self.최대콤보, self.콤보)
            self.점수 += 10 * 배율(self.콤보)
            self.마지막정타 = time.time()
            self.오타 = False
            self.위치 += 1
            if self.콤보 >= 임계값:
                self.흔들기()
            if self.위치 == len(self.스니펫):
                self.점수 += 50
                self.새스니펫()
        else:
            self.오타 = True
            self.브레이크("오타")
        self.그리기()

    def 브레이크(self, 이유):
        if self.콤보:
            self.메시지.config(text=f"COMBO BREAK! ({self.콤보} → 0, {이유})")
        self.콤보 = 0

    def 흔들기(self):
        dx, dy = random.randint(-4, 4), random.randint(-3, 3)
        self.글.pack_configure(padx=(20 + dx, 20 - dx), pady=(20 + dy, 20 - dy))

    def 종료(self):
        self.진행중, self.끝화면 = False, True
        self.콤보표시.config(text=f"GAME OVER  {self.점수}점", fg="#ff0")
        self.메시지.config(text=f"최대 콤보 {self.최대콤보}", fg="#aaa")
        self.위.config(text="닉네임을 입력하고 등록하세요 (최대 12자)")
        self.아래비우기()
        줄 = tk.Frame(self.아래, bg="#111"); 줄.pack()
        self.이름 = tk.Entry(줄, font=("Menlo", 14), width=14); self.이름.pack(side="left", padx=4)
        self.이름.focus_set()
        self.이름.bind("<Return>", lambda e: self.등록())
        self.등록버튼 = tk.Button(줄, text="등록", command=self.등록); self.등록버튼.pack(side="left")
        tk.Button(줄, text="다시 하기", command=self.다시).pack(side="left", padx=4)
        self.상태 = tk.Label(self.아래, font=("Menlo", 12), fg="#aaa", bg="#111"); self.상태.pack()
        self.표 = tk.Label(self.아래, font=("Menlo", 12), fg="#ddd", bg="#111", justify="left")
        self.표.pack()
        self.순위표시()

    def 다시(self):
        self.끝화면 = False
        self.창.focus_set()
        self.아래비우기()
        self.시작()

    def 등록(self):
        이름 = self.이름.get().strip()
        if not 1 <= len(이름) <= 12:
            return self.상태.config(text="닉네임은 1~12자로 입력하세요")
        self.등록버튼.config(state="disabled")
        self.상태.config(text="등록 중...")
        leaderboard.백그라운드(leaderboard.점수보내기, self.등록완료, self.창, 이름, self.점수, self.최대콤보)

    def 등록완료(self, 결과, 에러):
        if 에러:
            self.등록버튼.config(state="normal")
            self.상태.config(text=에러)
        else:
            self.상태.config(text=f"등록 완료! 현재 {결과['rank']}위")
            self.순위표시()

    def 순위표시(self):
        if not self.아래.winfo_children():
            self.표 = tk.Label(self.아래, font=("Menlo", 12), fg="#ddd", bg="#111", justify="left")
            self.표.pack()
        self.표.config(text="TOP 10 불러오는 중...")
        leaderboard.백그라운드(leaderboard.순위가져오기, self.순위받음, self.창, 10)

    def 순위받음(self, 목록, 에러):
        if not self.표.winfo_exists():
            return
        if 에러:
            return self.표.config(text=f"(리더보드 오프라인: {에러})")
        줄들 = [f"{r['rank']:>2}. {r['name']:<12} {r['score']:>7}점  콤보 {r['combo']}" for r in 목록]
        self.표.config(text="🏆 TOP 10\n" + ("\n".join(줄들) or "아직 기록이 없어요"))


if __name__ == "__main__":
    창 = tk.Tk()
    게임(창)
    창.mainloop()
