import os
import json
import pandas as pd
from unittest.mock import Mock, patch
import pytest
from app.utils import Utils
from app.drawer import FormatDrawer
from app.schemas import SuccesSchema


class TestFormatDrawer:
    """
    Тесты для класса `FormatDrawer`, отвечающего за форматирование и сохранение Excel-отчётов.
    """

    @pytest.fixture
    def mock_format_df(self):
        """Фикстура, создающая тестовый DataFrame."""
        return pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        })

    @pytest.fixture
    def mock_config(self):
        """Фикстура, имитирующая конфигурацию форматирования."""
        return {
            "format_column_map": {
                "new_col1": (0, "col1"),
                "new_col2": (1, "col2")
            }
        }
    

    @pytest.fixture
    def drawer_instance(self, mock_format_df, mock_config):
        """Фикстура, создающая экземпляр `FormatDrawer`."""
        return FormatDrawer(format_df=mock_format_df, config=mock_config)

    def test_initialization_with_config(self, mock_format_df, mock_config):
        """
        Проверяет, что при инициализации с явно переданным `config`
        он используется вместо загрузки из файла.
        """
        drawer = FormatDrawer(format_df=mock_format_df, config=mock_config)
        assert drawer.config == mock_config






    def test_draw_report_returns_succes_schema_with_message_and_link(self, drawer_instance):
        """
        Проверяет, что метод `draw_report` возвращает объект `SuccesSchema`
        с сообщением об успехе и ссылкой на файл.
        """
        with patch('app.utils.Utils.create_save_file', return_value=('file_path', 'link')):
            result = drawer_instance.draw_report()
            assert isinstance(result, SuccesSchema)
            assert result.message == 'Отчет создан'
            assert result.download_link == 'link'


