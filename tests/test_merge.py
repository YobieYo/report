import pandas as pd
from app.drawer import MergeDrawer


def _config():
    return {
        'bitrix_columns': ['ID', 'Название', 'Описание', 'Примечание', 'Теги'],
        'web_columns': ['Опытный узел', '№ трактора', 'ПЭ: Комментарий', '№ задачи в Битрикс'],
    }


def test_merge_matches_by_number_and_validates_name(monkeypatch):
    bitrix_df = pd.DataFrame({
        'ID': [101, 102],
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
        '№ задачи в Битрикс': [101],
        'Лишнее': [1],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=_config())
    result = md._merge_content()

    assert set(result.columns) >= {'Название', 'Опытный узел', '№ трактора', 'Теги'}
    assert len(result) == 1
    matched_row = result.iloc[0]
    assert matched_row['Название'] == 'A'
    assert matched_row['Опытный узел'] == 'A'
    assert matched_row['№ трактора'] == 101

    # Задача B (номер 102) нигде не упомянута в отчете -> конфликт "не найдено"
    conflicts = md.conflicts_df
    bitrix_conflicts = conflicts[conflicts['Источник'] == 'БИТРИКС']
    assert (bitrix_conflicts['№ задачи'] == '102').any()
    assert (bitrix_conflicts['_reason_code'] == 'not_found').all()


def test_merge_flags_description_mismatch_as_conflict():
    bitrix_df = pd.DataFrame({
        'ID': [101],
        'Название': ['A'],
        'Описание': ['описание A'],
        'Примечание': ['100 м/ч'],
        'Теги': ['Бюро А'],
    })

    web_df = pd.DataFrame({
        'Опытный узел': ['ДРУГОЙ УЗЕЛ'],
        '№ трактора': [101],
        'ПЭ: Комментарий': ['-'],
        '№ задачи в Битрикс': [101],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=_config())
    result = md._merge_content()

    # Номер найден, но название не совпало -> в основной отчет строка не идет
    assert result.empty

    conflicts = md.conflicts_df
    web_conflicts = conflicts[conflicts['Источник'] == 'СЛУЖЕБНЫЙ']
    assert len(web_conflicts) == 1
    row = web_conflicts.iloc[0]
    assert row['_reason_code'] == 'mismatch'
    assert row['№ задачи'] == '101'
    assert row['Опытный узел'] == 'ДРУГОЙ УЗЕЛ'
    assert row['Название в Битрикс'] == 'A'


def test_merge_flags_missing_number_as_not_found():
    bitrix_df = pd.DataFrame({
        'ID': [101],
        'Название': ['A'],
        'Описание': ['описание A'],
        'Примечание': ['100 м/ч'],
        'Теги': ['Бюро А'],
    })

    web_df = pd.DataFrame({
        'Опытный узел': ['A'],
        '№ трактора': [101],
        'ПЭ: Комментарий': ['-'],
        '№ задачи в Битрикс': [None],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=_config())
    result = md._merge_content()

    assert result.empty

    conflicts = md.conflicts_df
    web_conflicts = conflicts[conflicts['Источник'] == 'СЛУЖЕБНЫЙ']
    assert len(web_conflicts) == 1
    assert web_conflicts.iloc[0]['_reason_code'] == 'not_found'


def test_merge_joins_multiple_tasks_in_one_row_for_conflicts():
    # Номер 201 не существует в Битриксе вовсе - должен уйти в конфликты
    # вместе с номером 202 (тоже не найден), т.к. оба относятся к одной строке отчета.
    bitrix_df = pd.DataFrame({
        'ID': [999],
        'Название': ['Не относится к делу'],
        'Описание': ['-'],
        'Примечание': ['100 м/ч'],
        'Теги': ['Бюро А'],
    })

    web_df = pd.DataFrame({
        'Опытный узел': ['Узел 1; Узел 2'],
        '№ трактора': [101],
        'ПЭ: Комментарий': ['-'],
        '№ задачи в Битрикс': ['201, 202'],
    })

    md = MergeDrawer(web_df=web_df, bitrix_df=bitrix_df, config=_config())
    result = md._merge_content()

    assert result.empty

    conflicts = md.conflicts_df
    web_conflicts = conflicts[conflicts['Источник'] == 'СЛУЖЕБНЫЙ']
    assert len(web_conflicts) == 1
    row = web_conflicts.iloc[0]
    assert row['№ задачи'] == '201 202'
    assert row['Опытный узел'] == 'Узел 1, Узел 2'
