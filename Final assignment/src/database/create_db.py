import sqlite3
from pathlib import Path
import os

def create_database():
    print("🚀 DB作成プログラムを起動します...")
    
    # 1. このプログラムファイルがある場所を特定
    current_file_path = Path(__file__).resolve()
    
    # 2. プロジェクトのルートディレクトリ
    project_root = current_file_path.parent.parent.parent
    
    # 3. ターゲットとなるDBファイルの絶対パスを作成
    target_db_dir = project_root / "Final assignment" / "db"
    target_db_path = target_db_dir / "rent.db"
    
    print(f"📂 目標フォルダ: {target_db_dir}")
    print(f"📄 目標ファイル: {target_db_path}")

    # 4. フォルダがなければ強制作成
    if not target_db_dir.exists():
        print("⚡ フォルダが存在しないため作成します...")
        target_db_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. DB作成とテーブル定義
    try:
        conn = sqlite3.connect(target_db_path)
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
        print("\n✅ 成功！データベースが正常に作成されました！")
        print(f"確認コマンド: ls -l \"{target_db_path}\"")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    create_database()