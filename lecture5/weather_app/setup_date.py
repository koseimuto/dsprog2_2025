import requests
import json

# 気象庁の地域リスト（住所録）を取得
url = "http://www.jma.go.jp/bosai/common/const/area.json"
print("地域リストをダウンロード中...")

try:
    response = requests.get(url)
    data = response.json()

    # 必要なデータ（地方と都道府県）だけを整理
    regions = {}
    for code, info in data['centers'].items():
        regions[code] = {
            "name": info['name'],
            "children": info['children']
        }

    prefectures = {}
    for code, info in data['offices'].items():
        prefectures[code] = {
            "name": info['name']
        }

    saved_data = {"regions": regions, "prefectures": prefectures}

    # ファイルとして保存
    with open('area.json', 'w', encoding='utf-8') as f:
        json.dump(saved_data, f, ensure_ascii=False, indent=2)

    print("成功！ 'area.json' を保存しました。")

except Exception as e:
    print(f"エラー: {e}")
    