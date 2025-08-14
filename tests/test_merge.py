import pandas as pd
from drawer import MergeDrawer

def test_merge_content_basic_ffill_and_trim(monkeypatch):
    # Конфиг с нужными колонками
    config = {
        'bitrix_columns': ['Название', 'Бюро'],
        'web_columns': ['Опытный узел', '№ трактора', 'Бюро'],
    }

    bitrix_df = pd.DataFrame({
        'Название': ['XXXXA', 'XXXXB', 'XXXXC'],  # первые 4 символа отрежутся
        'Бюро': ['Б1', 'Б2', 'Б3'],
        'Игнор': [0, 0, 0]
    })

    web_df = pd.DataFrame({
        'Опытный узел': ['A', None, 'C'],
        '№ трактора': [None, 101, 102],
        'Бюро': ['Б1', 'Б1', 'Б3'],
        'Лишнее': [1, 2, 3]
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=config)
    result = md._merge_content()

    # Проверки колонок после выбора
    assert set(result.columns) >= {'Название', 'Опытный узел', '№ трактора', 'Бюро'}

    # Название должно было подрезаться: 'XXXXA' -> 'A', и сматчиться по merge
    # после ffill в web_df: 'Опытный узел' и '№ трактора' заполнены вниз
    # result после merge и ffill не должен содержать NaN в этих полях
    assert result['Опытный узел'].isna().sum() == 0
    assert result['№ трактора'].isna().sum() == 0

    # Проверим, что запись для 'A' подтянула 'Бюро'='Б1'
    row_a = result[result['Опытный узел'] == 'A'].iloc[0]
    assert row_a['Бюро'] == 'Б1'
