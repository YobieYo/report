import os
import json
import pandas as pd
from pathlib import Path
from app.drawer import MergeDrawer, Utils
from unittest.mock import patch

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
        'bitrix_columns': ['Название', 'Описание', 'Примечание', 'Теги'],
        'web_columns': ['Опытный узел', '№ трактора', 'ПЭ: Комментарий'],
        'report_column_map': {
            'Опытный узел': (0, 'Опытный узел'),
            '№ трактора': (1, '№ трактора'),
            'Бюро': (2, 'Теги'),
        }
    }

    bitrix_df = pd.DataFrame({
        'Название': ['U1'],
        'Описание': ['Описание U1'],
        'Примечание': ['100 м/ч'],
        'Теги': ['A'],
    })
    web_df = pd.DataFrame({
        'Опытный узел': ['U1'],
        '№ трактора': [123],
        'ПЭ: Комментарий': ['-'],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=config)
    with patch.object(MergeDrawer, '_format_excel_report', autospec=True) as format_report:
        def fake_format_report(self, group_col_name, output_file):
            Path(output_file).touch()

        format_report.side_effect = fake_format_report
        res = md.draw_report()

    assert isinstance(res, DummySchema)
    assert res.message == 'Отчет создан'
    assert 'download' in res.download_link
    # Убедимся, что файл создан
    out_path = tmp_path / "out.xlsx"
    assert out_path.exists()