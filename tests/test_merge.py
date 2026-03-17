import pandas as pd
from app.drawer import MergeDrawer

def test_merge_content_does_not_fill_from_neighbor_tasks(monkeypatch):
    config = {
        'bitrix_columns': ['Название', 'Описание', 'Примечание', 'Теги'],
        'web_columns': ['Опытный узел', '№ трактора', 'ПЭ: Комментарий'],
    }

    bitrix_df = pd.DataFrame({
        'Название': ['A', 'B'],
        'Описание': ['описание A', 'описание B'],
        'Примечание': ['100 м/ч', '200 м/ч'],
        'Теги': [None, 'Бюро Б'],
        'Игнор': [0, 0],
    })

    web_df = pd.DataFrame({
        'Опытный узел': ['A'],
        '№ трактора': [101],
        'ПЭ: Комментарий': ['-'],
        'Лишнее': [1],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=config)
    result = md._merge_content()

    assert set(result.columns) >= {'Название', 'Опытный узел', '№ трактора', 'Теги'}

    matched_row = result[result['Название'] == 'A'].iloc[0]
    assert matched_row['Опытный узел'] == 'A'
    assert matched_row['№ трактора'] == 101

    unmatched_row = result[result['Название'] == 'B'].iloc[0]
    assert pd.isna(unmatched_row['Опытный узел'])
    assert pd.isna(unmatched_row['№ трактора'])
    assert unmatched_row['Теги'] == 'Бюро Б'
