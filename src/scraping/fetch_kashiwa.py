import urllib.robotparser
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from pathlib import Path

# 1. 取得対象のURLリスト（3駅）
TARGET_URLS = [
    {
        "station": "柏",
        "url": "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=12&sc=12217&cb=0.0&ct=9999999&et=20&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
    },
    {
        "station": "流山おおたかの森",
        "url": "https://suumo.jp/chintai/chiba/ek_76125/?rn=0760"
    },
    {
        "station": "柏の葉キャンパス",
        "url": "https://suumo.jp/chintai/chiba/ek_76130/?rn=0760"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "Final assignment" / "db" / "rent.db"

def check_robots_txt(url, user_agent="*"):
    """robots.txtを確認する関数"""
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True 

def fetch_data():
    # DB初期化（フォルダがない場合のみ作成）
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # テーブル作成
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rent_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT, rent INTEGER, walk_min INTEGER, 
            age INTEGER, area REAL, layout TEXT, url TEXT UNIQUE
        )
    """)
    
    total_inserted = 0

    print("🚀 スクレイピングプログラムを開始します...")

    # 3駅分ループして実行
    for target in TARGET_URLS:
        station_name = target["station"]
        target_url = target["url"]
        
        print(f"\n--------------------------------------------------")
        print(f"📡 {station_name}駅 のデータ取得を開始")
        print(f"--------------------------------------------------")

        # 1. robots.txt チェック
        if not check_robots_txt(target_url):
            print(f"❌ {station_name}駅: robots.txt により禁止されています。スキップします。")
            continue

        # 2. 負荷対策 (3秒待機)
        print("💤 サーバー負荷低減のため、3秒待機します...")
        time.sleep(3)

        # 3. データ取得
        try:
            res = requests.get(target_url, headers=HEADERS)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
        except Exception as e:
            print(f"❌ 通信エラー: {e}")
            continue

        items = soup.find_all("div", class_="cassetteitem")
        print(f"📦 ページから取得した物件数: {len(items)} 件")

        data_list = []
        
        # 4. 解析処理
        for i, item in enumerate(items):
            try:
                # 建物情報
                age_text = item.find("li", class_="cassetteitem_detail-col3").find("div").text
                age = 0 if "新築" in age_text else int(age_text.replace("築", "").replace("年", ""))
                
                # 部屋情報
                tbody = item.find("table", class_="cassetteitem_other").find("tbody")
                rooms = tbody.find_all("tr")
                
                for tr in rooms:
                    try:
                        # 家賃
                        rent_text = tr.find("span", class_="cassetteitem_price--rent").text
                        if "万円" in rent_text:
                            rent = int(float(rent_text.replace("万円", "")) * 10000)
                        else:
                            rent = int(rent_text.replace("円", ""))

                        # 管理費
                        admin_text = tr.find("span", class_="cassetteitem_price--administration").text
                        if admin_text == "-":
                            admin = 0
                        elif "万円" in admin_text:
                            admin = int(float(admin_text.replace("万円", "")) * 10000)
                        elif "円" in admin_text:
                            admin = int(admin_text.replace("円", ""))
                        else:
                            admin = 0
                        
                        total_rent = rent + admin

                        # 徒歩
                        walk_text = item.find("li", class_="cassetteitem_detail-col2").text
                        import re
                        walk_match = re.search(r'歩(\d+)分', walk_text)
                        walk_min = int(walk_match.group(1)) if walk_match else 99
                        
                        # 面積
                        menseki_text = tr.find("span", class_="cassetteitem_menseki").text
                        area = float(menseki_text.replace("m2", ""))
                        
                        # 間取り
                        layout_text = tr.find("span", class_="cassetteitem_madori").text
                        layout = layout_text.strip()

                        # URL
                        link_rel = tr.find("td", class_="ui-text--midium").find("a")['href']
                        url = "https://suumo.jp" + link_rel

                        data_list.append({
                            "station": station_name,
                            "rent": total_rent, "walk_min": walk_min,
                            "age": age, "area": area, "layout": layout, "url": url
                        })
                        
                    except Exception:
                        continue
            except Exception:
                continue

        # 5. DB保存
        station_inserted = 0
        for d in data_list:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO rent_properties 
                    (station, rent, walk_min, age, area, layout, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (d['station'], d['rent'], d['walk_min'], d['age'], d['area'], d['layout'], d['url']))
                if cur.rowcount > 0:
                    station_inserted += 1
                    total_inserted += 1
            except: pass
            
        print(f"✨ {station_name}駅: {len(data_list)} 部屋分のデータを解析し、{station_inserted} 件を新規保存しました。")

    conn.commit()
    conn.close()
    print(f"\n✅ 全工程完了！ 新しく合計 {total_inserted} 件のデータを保存しました。")
    print("これでStep 2は完了です。分析（Jupyter Notebook）に進んでください！")

if __name__ == "__main__":
    fetch_data()