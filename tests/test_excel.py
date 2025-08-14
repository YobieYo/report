import pandas as pd
from pathlib import Path
from app.drawer import MergeDrawer

def test_format_excel_report_smoke(tmp_path):
    df = pd.DataFrame({
        'Бюро': ['A', 'A', 'B'],
        'Опытный узел': ['U1', 'U2', 'U3'],
        '№ трактора': [10, 10, 11],
        'КолонкаX': [1, 2, 3],
    })

    config = {
        'report_column_map': {
            'Опытный узел': (0, 'Опытный узел'),
            '№ трактора': (1, '№ трактора'),
            'Бюро': (2, 'Бюро'),
            'КолонкаX': (3, 'КолонкаX'),
        }
    }

    md = MergeDrawer(web_df=pd.DataFrame(), bitrix_df=pd.DataFrame(), config=config)
    md.result_df = df  # уже «готовый» результат

    out = tmp_path / "report.xlsx"
    md._format_excel_report(group_col_name='Бюро', output_file=str(out))
    assert out.exists() and out.stat().st_size > 0
