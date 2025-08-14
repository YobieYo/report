import os
import json
import pandas as pd
from pathlib import Path
from app.drawer import MergeDrawer, Utils

class DummySchema:
    def __init__(self, message, download_link):
        self.message = message
        self.download_link = download_link

def test_draw_report_integration(tmp_path, monkeypatch):
    # Подменим схемы и Utils
    monkeypatch.setenv('UPLOAD_FOLDER', str(tmp_path))

    def fake_create_save_file(upl_folder):
        out = Path(upl_folder) / "out.xlsx"
        link = "http://test/download/out.xlsx"
        # файл создастся внутри _format_excel_report, здесь только возвращаем пути
        return str(out), link

    monkeypatch.setattr('app.drawer.Utils.create_save_file', fake_create_save_file)

    # Подменим SuccesSchema на простой класс, чтобы не тянуть зависимости
    monkeypatch.setattr('app.drawer.SuccesSchema', DummySchema)

    # Мокаем конфиг, чтобы не читать файл
    config = {
        'bitrix_columns': ['Название', 'Бюро'],
        'web_columns': ['Опытный узел', '№ трактора', 'Бюро'],
        'report_column_map': {
            'Опытный узел': (0, 'Опытный узел'),
            '№ трактора': (1, '№ трактора'),
            'Бюро': (2, 'Бюро'),
        }
    }

    bitrix_df = pd.DataFrame({'Название': ['XXXXU1'], 'Бюро': ['A']})
    web_df = pd.DataFrame({'Опытный узел': ['U1'], '№ трактора': [123], 'Бюро': ['A']})

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=config)
    res = md.draw_report()

    assert isinstance(res, DummySchema)
    assert res.message == 'Отчет создан'
    assert 'download' in res.download_link
    # Убедимся, что файл создан
    out_path = tmp_path / "out.xlsx"
    assert out_path.exists()