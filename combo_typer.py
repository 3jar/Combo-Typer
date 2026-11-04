"""콤보 타자기 v2 — 메인 메뉴 + Supabase 온라인 리더보드.
실행: uv run python combo_typer.py   (Supabase 설정은 README.md 참고)"""
import os
import sys
import tkinter as tk

# uv 가상환경에서 Tcl/Tk 라이브러리를 못 찾는 문제(init.tcl 오류) 우회
for 이름, 폴더 in (("TCL_LIBRARY", "tcl9.0"), ("TK_LIBRARY", "tk9.0")):
    경로 = os.path.join(sys.base_prefix, "lib", 폴더)
    if 이름 not in os.environ and os.path.isdir(경로):
        os.environ[이름] = 경로

import leaderboard
from game import 게임화면, 난이도

배경, 글꼴 = "#111", "Menlo"


class 앱:
    def __init__(self, 창):
        self.창, self.설정 = 창, leaderboard.설정읽기()
        창.title("콤보 타자기")
        창.geometry("800x540")
        창.configure(bg=배경)
        self.화면 = None
        self.메뉴()

    # ---------- 공통 도우미 ----------
    def 새화면(self):
        if self.화면:
            self.화면.destroy()
        self.화면 = tk.Frame(self.창, bg=배경)
        self.화면.pack(fill="both", expand=True)
        return self.화면

    def 라벨(self, 부모, 글, 크기=14, 색="#ddd", pady=4, **옵션):
        l = tk.Label(부모, text=글, font=(글꼴, 크기), fg=색, bg=배경, **옵션)
        l.pack(pady=pady)
        return l

    def 버튼(self, 부모, 글, 명령, 옆으로=False):
        b = tk.Button(부모, text=글, command=명령, width=14, font=(글꼴, 14))
        b.pack(side="left" if 옆으로 else "top", padx=4, pady=4)
        return b

    def 최고기록글(self):
        return "내 최고 기록  " + "   ".join(
            f"{난이도[m]['이름']} {self.설정['best'].get(m, 0)}" for m in 난이도)

    # ---------- 메인 메뉴 / 난이도 ----------
    def 메뉴(self):
        f = self.새화면()
        self.라벨(f, "COMBO TYPER", 40, "#ff0", pady=0).pack_configure(pady=(50, 10))
        self.라벨(f, self.최고기록글(), 13, "#aaa").pack_configure(pady=(0, 30))
        self.버튼(f, "게임 시작", self.난이도선택)
        self.버튼(f, "리더보드", lambda: self.리더보드("normal"))
        self.버튼(f, "설정", self.설정화면)
        self.버튼(f, "종료", self.창.destroy)

    def 난이도선택(self):
        f = self.새화면()
        self.라벨(f, "난이도를 고르세요", 24).pack_configure(pady=(60, 20))
        설명 = {"easy": "짧은 단어", "normal": "한 줄 코드", "hard": "긴 코드"}
        for 모드, 값 in 난이도.items():
            self.버튼(f, f"{값['이름']} ({설명[모드]})", lambda m=모드: self.게임시작(m)).config(width=24)
        self.버튼(f, "메뉴로", self.메뉴)
        self.라벨(f, "게임 중 ESC: 일시정지", 12, "#888")

    def 게임시작(self, 모드):
        if self.화면:
            self.화면.destroy()
        self.화면 = 게임화면(self.창, 모드, self.설정, self.결과, self.메뉴)
        self.화면.pack(fill="both", expand=True)
        self.화면.focus_set()

    # ---------- 결과 / 등록 ----------
    def 결과(self, r):
        f = self.새화면()
        최고 = self.설정["best"].get(r["mode"], 0)
        갱신 = r["score"] > 최고
        if 갱신:
            self.설정["best"][r["mode"]] = r["score"]
            leaderboard.설정저장(self.설정)
        self.라벨(f, f"GAME OVER  {r['score']}점", 32, "#ff0").pack_configure(pady=(30, 6))
        self.라벨(f, f"{난이도[r['mode']]['이름']} · 최대 콤보 {r['combo']} · 정확도 {r['accuracy']}% · {r['cpm']} CPM", 14)
        self.라벨(f, "🎉 내 최고 기록 갱신!" if 갱신 else f"내 최고 기록 {최고}", 14, "#4f4" if 갱신 else "#aaa")
        self.라벨(f, "닉네임 (1~12자)", 12, "#aaa")
        줄 = tk.Frame(f, bg=배경); 줄.pack()
        self.이름칸 = tk.Entry(줄, font=(글꼴, 14), width=14)
        self.이름칸.insert(0, self.설정["name"])
        self.이름칸.pack(side="left", padx=4)
        self.이름칸.focus_set()
        self.이름칸.bind("<Return>", lambda e: self.등록(r))
        self.등록버튼 = tk.Button(줄, text="등록", font=(글꼴, 13), command=lambda: self.등록(r))
        self.등록버튼.pack(side="left")
        self.상태 = self.라벨(f, "", 13, "#aaa")
        아래 = tk.Frame(f, bg=배경); 아래.pack(pady=14)
        self.버튼(아래, "다시 하기", lambda: self.게임시작(r["mode"]), True)
        self.버튼(아래, "리더보드", lambda: self.리더보드(r["mode"]), True)
        self.버튼(아래, "메뉴로", self.메뉴, True)

    def 등록(self, r):
        이름 = self.이름칸.get().strip()
        if not 1 <= len(이름) <= 12:
            return self.상태.config(text="닉네임은 1~12자로 입력하세요", fg="#f55")
        self.설정["name"] = 이름
        leaderboard.설정저장(self.설정)
        self.등록버튼.config(state="disabled")
        self.상태.config(text="등록 중...", fg="#aaa")
        상태 = self.상태
        leaderboard.백그라운드(leaderboard.점수보내기, lambda 결과, 에러: self.등록완료(상태, 결과, 에러),
                           self.창, 이름, r["score"], r["combo"], r["mode"])

    def 등록완료(self, 상태, 결과, 에러):
        if not 상태.winfo_exists():
            return  # 그 사이 다른 화면으로 이동함
        if 에러:
            self.등록버튼.config(state="normal")
            상태.config(text=에러, fg="#f55")
        else:
            상태.config(text=f"등록 완료! 현재 {결과['rank']}위", fg="#4f4")

    # ---------- 리더보드 ----------
    def 리더보드(self, 모드):
        f = self.새화면()
        self.라벨(f, "🏆 리더보드 TOP 10", 24, "#ff0").pack_configure(pady=(24, 8))
        탭 = tk.Frame(f, bg=배경); 탭.pack()
        for m, 값 in 난이도.items():
            b = self.버튼(탭, 값["이름"], lambda m=m: self.리더보드(m), True)
            b.config(width=8, state="disabled" if m == 모드 else "normal")
        표 = self.라벨(f, "불러오는 중...", 13, justify="left")
        표.pack_configure(pady=12)
        아래 = tk.Frame(f, bg=배경); 아래.pack(side="bottom", pady=14)
        self.버튼(아래, "새로고침", lambda: self.리더보드(모드), True)
        self.버튼(아래, "메뉴로", self.메뉴, True)
        leaderboard.백그라운드(leaderboard.순위가져오기, lambda 목록, 에러: self.순위받음(표, 목록, 에러),
                           self.창, 모드)

    def 순위받음(self, 표, 목록, 에러):
        if not 표.winfo_exists():
            return
        if 에러:
            return 표.config(text=f"({에러})", fg="#f55")
        줄들 = [f"{i:>2}. {r['name']:<12} {r['score']:>7}점  콤보 {r['combo']}" for i, r in enumerate(목록, 1)]
        표.config(text="\n".join(줄들) or "아직 기록이 없어요", fg="#ddd")

    # ---------- 설정 ----------
    def 설정화면(self):
        f = self.새화면()
        self.라벨(f, "설정", 28).pack_configure(pady=(30, 10))
        시간 = tk.IntVar(value=self.설정["time"])
        흔들림 = tk.BooleanVar(value=self.설정["shake"])
        self.라벨(f, "게임 시간(초)", 13, "#aaa")
        줄 = tk.Frame(f, bg=배경); 줄.pack()
        for t in (30, 60, 90):
            tk.Radiobutton(줄, text=f"{t}초", variable=시간, value=t, font=(글꼴, 13), fg="#ddd",
                           bg=배경, selectcolor="#333", activebackground=배경).pack(side="left", padx=8)
        tk.Checkbutton(f, text="화면 흔들림", variable=흔들림, font=(글꼴, 13), fg="#ddd", bg=배경,
                       selectcolor="#333", activebackground=배경).pack(pady=12)
        self.라벨(f, "닉네임 (1~12자)", 13, "#aaa")
        이름칸 = tk.Entry(f, font=(글꼴, 14), width=14)
        이름칸.insert(0, self.설정["name"])
        이름칸.pack()

        def 저장():
            self.설정.update(time=시간.get(), shake=흔들림.get(), name=이름칸.get().strip()[:12])
            leaderboard.설정저장(self.설정)
            self.메뉴()
        self.버튼(f, "저장", 저장).pack_configure(pady=(20, 4))
        self.버튼(f, "취소", self.메뉴)


if __name__ == "__main__":
    창 = tk.Tk()
    앱(창)
    창.mainloop()
