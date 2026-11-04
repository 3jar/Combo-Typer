"""게임 화면: 스니펫 따라 치기, 콤보/배율/브레이크, 화면 흔들림, 난이도 데이터."""
import random
import time
import tkinter as tk

임계값 = 30  # 이 콤보 이상이면 화면 흔들림 + 색 변화

# 난이도: 스니펫 묶음 + 리셋시간(이 시간 안에 다음 정타가 없으면 콤보 리셋)
난이도 = {
    "easy": {"이름": "쉬움", "리셋": 2.5, "스니펫": [
        "print", "len", "range", "input", "import", "return", "class", "while",
        "lambda", "append", "split", "True", "None", "break", "def", "else"]},
    "normal": {"이름": "보통", "리셋": 1.5, "스니펫": [
        "def add(a, b): return a + b", "for i in range(10): print(i * i)",
        "names = ['kim', 'lee', 'park']", "total = sum([3, 1, 4, 1, 5])",
        "sign = 'plus' if x > 0 else 'minus'", "squares = [x ** 2 for x in range(5)]",
        "while count < 3: count += 1", "number = random.randint(1, 6)", "class Dog: pass"]},
    "hard": {"이름": "어려움", "리셋": 1.0, "스니펫": [
        "with open('memo.txt') as f: text = f.read().strip().split(',')",
        "result = {k: v for k, v in zip(keys, values) if v is not None}",
        "def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)",
        "data = sorted(items, key=lambda p: (-p['score'], p['name']))[:10]",
        "value = int(text) if text.strip().isdigit() else 0",
        "print(f'{name:<12} {score:>7}점 콤보 {combo}')"]},
}


def 배율(콤보):
    """콤보 10마다 배율 +1 (최대 x5)."""
    return min(1 + 콤보 // 10, 5)


class 게임화면(tk.Frame):
    def __init__(self, 부모, 모드, 설정, 끝났을때, 메뉴로):
        super().__init__(부모, bg="#111")
        self.모드, self.설정, self.끝났을때 = 모드, 설정, 끝났을때
        self.리셋시간 = 난이도[모드]["리셋"]
        self.위 = tk.Label(self, font=("Menlo", 14), fg="#aaa", bg="#111")
        self.위.pack(pady=8)
        self.글 = tk.Text(self, font=("Menlo", 20), height=2, width=48, bg="#111", fg="#666",
                         bd=0, highlightthickness=0, cursor="arrow", wrap="word")
        self.글.tag_config("정", foreground="#4f4")
        self.글.tag_config("현", background="#555", foreground="#fff")
        self.글.tag_config("오", background="#a22", foreground="#fff")
        self.글.pack(pady=20)
        self.콤보표시 = tk.Label(self, font=("Menlo", 36, "bold"), fg="#fff", bg="#111")
        self.콤보표시.pack()
        self.메시지 = tk.Label(self, font=("Menlo", 13), fg="#f55", bg="#111")
        self.메시지.pack(pady=6)
        tk.Button(self, text="메뉴로 (포기)", command=메뉴로).pack(side="bottom", pady=10)
        self.bind("<Key>", self.키)
        self.focus_set()
        self.진행중, self.멈춤 = True, False
        self.점수 = self.콤보 = self.최대콤보 = self.정타 = self.입력 = 0
        self.마지막정타 = 0.0
        self.남은시간 = float(설정["time"])
        self.마지막틱 = time.time()
        self.오타 = False
        self.스니펫 = ""
        self.새스니펫()
        self.틱()

    def destroy(self):
        self.진행중 = False  # 예약된 틱이 있어도 아무것도 안 하게
        super().destroy()

    def 새스니펫(self):
        목록 = [s for s in 난이도[self.모드]["스니펫"] if s != self.스니펫]
        self.스니펫, self.위치 = random.choice(목록), 0
        self.그리기()

    def 그리기(self):
        t = self.글
        t.config(state="normal"); t.delete("1.0", "end"); t.insert("1.0", self.스니펫)
        t.tag_add("정", "1.0", f"1.{self.위치}")
        t.tag_add("오" if self.오타 else "현", f"1.{self.위치}", f"1.{self.위치 + 1}")
        t.config(state="disabled")
        상태 = "  [일시정지 - ESC로 계속]" if self.멈춤 else ""
        self.위.config(text=f"점수 {self.점수}   최대콤보 {self.최대콤보}   남은시간 {int(self.남은시간 + 0.99)}s{상태}")
        색 = "#ff0" if self.콤보 >= 임계값 else "#fff"
        self.콤보표시.config(text=f"{self.콤보} COMBO  x{배율(self.콤보)}", fg=색)

    def 틱(self):
        if not self.진행중:
            return
        지금 = time.time()
        if not self.멈춤:
            self.남은시간 -= 지금 - self.마지막틱
            if self.콤보 and 지금 - self.마지막정타 > self.리셋시간:
                self.브레이크("시간 초과")
            if self.남은시간 <= 0:
                return self.종료()
            self.그리기()
        self.마지막틱 = 지금
        self.after(100, self.틱)

    def 키(self, e):
        if not self.진행중:
            return
        if e.keysym == "Escape":
            self.멈춤 = not self.멈춤
            self.마지막정타 = time.time()  # 재개 직후 시간초과 방지
            return self.그리기()
        c = e.char
        if self.멈춤 or not c or not c.isprintable():
            return
        self.입력 += 1
        if c == self.스니펫[self.위치]:
            self.정타 += 1
            self.콤보 += 1
            self.최대콤보 = max(self.최대콤보, self.콤보)
            self.점수 += 10 * 배율(self.콤보)
            self.마지막정타 = time.time()
            self.오타 = False
            self.위치 += 1
            if self.설정["shake"] and self.콤보 >= 임계값:
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
            self.bell()
        self.콤보 = 0

    def 흔들기(self):
        dx, dy = random.randint(-4, 4), random.randint(-3, 3)
        self.글.pack_configure(padx=(20 + dx, 20 - dx), pady=(20 + dy, 20 - dy))

    def 종료(self):
        self.진행중 = False
        정확도 = round(100 * self.정타 / self.입력) if self.입력 else 0
        cpm = round(self.정타 * 60 / self.설정["time"])
        self.끝났을때({"mode": self.모드, "score": self.점수, "combo": self.최대콤보,
                    "accuracy": 정확도, "cpm": cpm})
