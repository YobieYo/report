import pandas as pd
from drawer import MergeDrawer

def test_reformat_dataframe_keeps_renames_and_orders_columns():
    df = pd.DataFrame({
        'old_a': [1, 2],
        'old_b': [3, 4],
        'extra': [9, 9],
    })
    column_map = {
        'NewB': (1, 'old_b'),
        'NewA': (0, 'old_a'),
    }
    md = MergeDrawer(web_df=pd.DataFrame(), bitrix_df=pd.DataFrame(), config={})
    out = md._reformat_dataframe(df, column_map)

    assert list(out.columns) == ['NewA', 'NewB']
    assert out['NewA'].tolist() == [1, 2]
    assert out['NewB'].tolist() == [3, 4]
