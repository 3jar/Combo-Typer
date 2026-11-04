"""콤보 타자기 리더보드 API (FastAPI + SQLite)
실행: uv run uvicorn server:app            (내 컴퓨터만)
      uv run uvicorn server:app --host 0.0.0.0   (같은 와이파이의 다른 컴퓨터도)"""
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, field_validator

DB경로 = Path(__file__).parent / "scores.db"  # 상대 경로 (프로젝트 폴더 안)
app = FastAPI(title="Combo Typer Leaderboard")


def 연결():
    db = sqlite3.connect(DB경로)
    db.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY, name TEXT, score INTEGER,"
               " combo INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP)")
    return db


class 점수(BaseModel):
    name: str = Field(min_length=1, max_length=12)
    score: int = Field(ge=0, le=1_000_000)
    combo: int = Field(ge=0, le=100_000)

    @field_validator("name")
    @classmethod
    def 이름정리(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("이름이 비어 있음")
        return v


@app.get("/scores")
def 점수목록(limit: int = Query(10, ge=1, le=100)):
    with 연결() as db:
        행들 = db.execute("SELECT name, score, combo, created FROM scores"
                          " ORDER BY score DESC, id ASC LIMIT ?", (limit,)).fetchall()
    return [{"rank": i + 1, "name": n, "score": s, "combo": c, "created": t}
            for i, (n, s, c, t) in enumerate(행들)]


@app.post("/scores", status_code=201)
def 점수등록(p: 점수):
    with 연결() as db:
        db.execute("INSERT INTO scores (name, score, combo) VALUES (?, ?, ?)", (p.name, p.score, p.combo))
        순위 = db.execute("SELECT COUNT(*) FROM scores WHERE score > ?", (p.score,)).fetchone()[0] + 1
    return {"ok": True, "rank": 순위}
