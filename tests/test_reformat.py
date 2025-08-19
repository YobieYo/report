import pandas as pd
from typing import Dict, List, Any
import pytest
from unittest.mock import Mock
from app.utils import DataFrameUtils


class TestDataFrameUtils:
    """
    Тесты для метода `reformat_dataframe` класса `DataFrameUtils`.
    """

    @pytest.fixture
    def sample_df(self):
        """Фикстура, создающая тестовый DataFrame."""
        return pd.DataFrame({
            "old_col1": [1, 2, 3],
            "old_col2": ["a", "b", "c"],
            "old_col3": [10.5, 20.5, 30.5]
        })

    def test_reformat_dataframe_with_valid_mapping(self, sample_df):
        """
        Проверяет, что метод корректно переименовывает и сортирует колонки согласно `column_map`.
        """
        column_map = {
            "new_col1": (0, "old_col2"),
            "new_col2": (1, "old_col1"),
            "new_col3": (2, "old_col3")
        }

        result = DataFrameUtils.reformat_dataframe(sample_df, column_map)

        expected_columns = ["new_col1", "new_col2", "new_col3"]
        assert list(result.columns) == expected_columns
        assert (result["new_col1"] == ["a", "b", "c"]).all()
        assert (result["new_col2"] == [1, 2, 3]).all()
        assert (result["new_col3"] == [10.5, 20.5, 30.5]).all()

    def test_reformat_dataframe_with_empty_column_map(self, sample_df):
        """
        Проверяет, что метод возвращает пустой DataFrame при пустом `column_map`.
        """
        column_map = {}

        result = DataFrameUtils.reformat_dataframe(sample_df, column_map)

        assert result.empty
        assert result.shape == (3, 0)

    def test_reformat_dataframe_sorts_columns_by_index(self, sample_df):
        """
        Проверяет, что колонки возвращаются в порядке, заданном индексами в `column_map`.
        """
        column_map = {
            "col3": (2, "old_col3"),
            "col1": (0, "old_col1"),
            "col2": (1, "old_col2")
        }

        result = DataFrameUtils.reformat_dataframe(sample_df, column_map)

        assert list(result.columns) == ["col1", "col2", "col3"]
        assert (result["col1"] == [1, 2, 3]).all()
        assert (result["col2"] == ["a", "b", "c"]).all()
        assert (result["col3"] == [10.5, 20.5, 30.5]).all()

