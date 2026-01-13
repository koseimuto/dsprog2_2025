import flet as ft
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# SSL証明書の警告を無視する設定（Macでの問題回避のため）
urllib3.disable_warnings(InsecureRequestWarning)

# メインアプリケーション
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1000
    page.window_height = 800

    # 1. データの読み込み (保存したJSONを使う)
    try:
        with open('area.json', 'r', encoding='utf-8') as f:
            area_data = json.load(f)
        regions = area_data['regions']      # 地方データ
        prefectures = area_data['prefectures'] # 都道府県データ
    except FileNotFoundError:
        page.add(ft.Text("エラー: area.jsonが見つかりません。setup_date.pyを先に実行してください。", color="red"))
        return

    # 2. 画面右側：天気表示エリアの作成
    # 天気カードを並べるグリッド
    weather_grid = ft.GridView(
        expand=True,
        runs_count=5,          # 横に並べる数
        max_extent=200,        # カードの最大幅
        child_aspect_ratio=1.0, 
        spacing=10,
        run_spacing=10,
    )
    
    header_text = ft.Text("地域を選択してください", size=24, weight="bold")
    
    # 右側全体のレイアウト
    content_area = ft.Column(
        controls=[
            ft.Container(content=header_text, padding=20),
            weather_grid
        ],
        expand=True,
    )

    # 3. ロジック：天気を取得して表示する関数
    def get_weather(e):
        # ボタンのデータから地域コードを取得
        code = e.control.data['code']
        name = e.control.data['name']
        
        header_text.value = f"{name}の天気予報"
        weather_grid.controls.clear() # 前の表示をクリア
        page.update()

        # 気象庁APIのエンドポイント
        url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
        
        try:
            # verify=False でMac特有のSSLエラーを回避
            res = requests.get(url, verify=False)
            data = res.json()
            
            # データ構造: data[0] -> timeSeries[0] -> areas[0] -> weathers
            forecast_data = data[0]['timeSeries'][0]
            dates = forecast_data['timeDefines']
            weathers = forecast_data['areas'][0]['weathers']
            
            # 予報の数だけカードを作成
            for i in range(len(weathers)):
                date_str = dates[i][0:10] # 日付部分のみ抽出
                weather_str = weathers[i]
                
                # アイコンと色を文字列で指定 
                icon_name = "sunny"
                icon_color = "orange"
                
                if "雨" in weather_str:
                    icon_name = "water_drop"
                    icon_color = "blue"
                elif "曇" in weather_str:
                    icon_name = "cloud"
                    icon_color = "grey"
                elif "雪" in weather_str:
                    icon_name = "snowing"
                    icon_color = "white"
                
                # 天気カード
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(date_str, size=16),
                                # アイコンの name プロパティに文字列を渡す
                                ft.Icon(name=icon_name, size=40, color=icon_color),
                                ft.Text(weather_str, size=14, text_align="center"),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                        padding=20,
                    )
                )
                weather_grid.controls.append(card)
                
        except Exception as err:
            print(f"エラー発生: {err}")
            weather_grid.controls.append(ft.Text(f"エラー: {err}", color="red"))

        page.update()

    # 4. 画面左側：サイドバーの作成 (ExpansionTile & ListTile)
    sidebar_controls = []

    # 地方ごとに折りたたみメニューを作成
    for region_code, region_info in regions.items():
        pref_tiles = []
        for child_code in region_info['children']:
            if child_code in prefectures:
                pref_name = prefectures[child_code]['name']
                
                # 都道府県ボタン
                tile = ft.ListTile(
                    title=ft.Text(pref_name),
                    on_click=get_weather,  # クリック時の動作
                    data={'code': child_code, 'name': pref_name} # コードを紐付け
                )
                pref_tiles.append(tile)
        
        # 地方メニュー
        expansion = ft.ExpansionTile(
            title=ft.Text(region_info['name']),
            controls=pref_tiles,
            collapsed_text_color=ft.Colors.WHITE,
            text_color=ft.Colors.BLUE_200,
        )
        sidebar_controls.append(expansion)

    sidebar = ft.Container(
        content=ft.ListView(controls=sidebar_controls, expand=True),
        width=250,
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=10,
    )

    # 5. アプリ全体の構成
    page.add(
        ft.Row(
            controls=[sidebar, ft.VerticalDivider(width=1), content_area],
            expand=True,
        )
    )

ft.app(target=main)