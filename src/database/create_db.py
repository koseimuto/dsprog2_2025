import sqlite3
import os
from pathlib import Path

def create_database():
    print("🚀 プログラムが動き出しました！")
    
    # Final assignment/db フォルダを狙い撃ち
    base_path = Path("Final assignment/db")
    db_path = base_path / "rent.db"
    
    print(f"📂 保存先ターゲット: {db_path.absolute()}")

    # フォルダを作る
    if not base_path.exists():
        print("⚡ フォルダを作成中...")
        base_path.mkdir(parents=True, exist_ok=True)

    # DBを作る
    print("🔨 データベースを作成中...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rent_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT NOT NULL,
            rent INTEGER NOT NULL,
            walk_min INTEGER NOT NULL,
            age INTEGER,
            area REAL,
            layout TEXT,
            url TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()
    print("✅ 大成功！ rent.db が作成されました！")

if __name__ == "__main__":
    create_database()
