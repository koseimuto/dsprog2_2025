import flet as ft
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import traceback 

import db_manager

urllib3.disable_warnings(InsecureRequestWarning)

def main(page: ft.Page):
    try:
        db_manager.init_db()
    except Exception as e:
        page.add(ft.Text(f"DB初期化エラー: {e}", color="red"))
        return

    page.title = "天気予報アプリ (改良版)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1000
    page.window_height = 800

    # 1. 地域リスト取得
    area_url = "http://www.jma.go.jp/bosai/common/const/area.json"
    try:
        res = requests.get(area_url, verify=False)
        area_data = res.json()
        centers = area_data['centers']
        offices = area_data['offices']
    except Exception as e:
        page.add(ft.Text(f"地域リスト取得エラー: {e}", color="red"))
        return

    # 2. 画面UI
    weather_grid = ft.GridView(
        expand=True,
        runs_count=5,
        max_extent=200,
        child_aspect_ratio=1.0, 
        spacing=10,
        run_spacing=10,
    )
    
    header_text = ft.Text("地域を選択してください", size=24, weight="bold")
    
    content_area = ft.Column(
        controls=[
            ft.Container(content=header_text, padding=20),
            weather_grid
        ],
        expand=True,
    )

    # 3. ロジック
    def get_weather(e):
        code = e.control.data['code']
        name = e.control.data['name']
        
        header_text.value = f"{name}の天気予報"
        weather_grid.controls.clear()
        page.update()

        url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
        
        try:
            # (1) 古いデータを消す
            if hasattr(db_manager, 'clear_data'):
                db_manager.clear_data(code)
            
            # (2) APIデータ取得
            res = requests.get(url, verify=False)
            data = res.json()
            
            if not data or 'timeSeries' not in data[0]:
                raise Exception("データが見つかりません")

            forecast_data = data[0]['timeSeries'][0]
            dates = forecast_data['timeDefines']
            weathers = forecast_data['areas'][0]['weathers']
            
            # (3) DB保存
            for i in range(len(weathers)):
                date_str = dates[i][0:10]
                weather_str = weathers[i]
                db_manager.save_forecast(code, date_str, weather_str)

            # (4) DBから表示
            stored_data = db_manager.get_forecasts_by_area(code)

            for row in stored_data:
                db_date = row[0]
                db_weather = row[1]

                emoji = "☀️"
                text_color = "orange"
                
                if "雨" in db_weather:
                    emoji = "☔️"
                    text_color = "blue"
                elif "曇" in db_weather:
                    emoji = "☁️"
                    text_color = "grey"
                elif "雪" in db_weather:
                    emoji = "☃️"
                    text_color = "white"
                
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(db_date, size=16),
                                ft.Text(emoji, size=40, color=text_color),
                                ft.Text(db_weather, size=14, text_align="center"),
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                        padding=20,
                    )
                )
                weather_grid.controls.append(card)
                
        except Exception as err:
            print(f"エラー: {err}")
            weather_grid.controls.append(ft.Text(f"エラー: {err}", color="red"))

        page.update()

    # 4. サイドバー
    sidebar_controls = []
    for center_code, center_info in centers.items():
        region_name = center_info['name']
        children_codes = center_info['children']
        
        pref_tiles = []
        for child_code in children_codes:
            if child_code in offices:
                office_name = offices[child_code]['name']
                tile = ft.ListTile(
                    title=ft.Text(office_name),
                    on_click=get_weather,
                    data={'code': child_code, 'name': office_name}
                )
                pref_tiles.append(tile)
        
        expansion = ft.ExpansionTile(
            title=ft.Text(region_name),
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

    page.add(
        ft.Row(
            controls=[sidebar, ft.VerticalDivider(width=1), content_area],
            expand=True,
        )
    )

ft.app(target=main)