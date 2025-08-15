import pytest
from unittest.mock import Mock, patch
from app import PrefixMiddleware


class TestPrefixMiddleware:
    """
    Тесты для middleware `PrefixMiddleware`, добавляющего префикс к пути запроса.
    """

    @pytest.fixture
    def mock_app(self):
        """Фикстура, имитирующая WSGI-приложение."""
        app = Mock()
        app.return_value = [b"Mocked response"]
        return app

    @pytest.fixture
    def environ(self):
        """Базовое WSGI-окружение для тестирования."""
        return {
            'SCRIPT_NAME': '',
            'PATH_INFO': '/test/path',
            'REQUEST_METHOD': 'GET'
        }

    def test_prefix_middleware_applies_prefix_correctly(self, mock_app, environ):
        """
        Проверяет, что middleware корректно добавляет префикс к `SCRIPT_NAME`
        и удаляет его из `PATH_INFO`.
        """
        prefix = '/new_reports'
        middleware = PrefixMiddleware(mock_app, prefix)
        middleware(environ, lambda *args: None)

        assert environ['SCRIPT_NAME'] == prefix
        assert environ['PATH_INFO'] == '/test/path'

    def test_prefix_middleware_removes_prefix_from_path_info(self, mock_app, environ):
        """
        Проверяет, что middleware удаляет префикс из `PATH_INFO`, если путь начинается с него.
        """
        prefix = '/new_reports'
        environ['PATH_INFO'] = f'{prefix}/test/path'
        middleware = PrefixMiddleware(mock_app, prefix)
        middleware(environ, lambda *args: None)

        assert environ['SCRIPT_NAME'] == prefix
        assert environ['PATH_INFO'] == '/test/path'

    def test_prefix_middleware_does_nothing_if_prefix_is_empty(self, mock_app, environ):
        """
        Проверяет, что middleware не изменяет окружение, если префикс пустой.
        """
        middleware = PrefixMiddleware(mock_app, '')
        middleware(environ, lambda *args: None)

        assert environ['SCRIPT_NAME'] == ''
        assert environ['PATH_INFO'] == '/test/path'

    def test_prefix_middleware_does_not_remove_prefix_if_path_does_not_match(self, mock_app, environ):
        """
        Проверяет, что middleware не удаляет префикс из `PATH_INFO`, если путь не начинается с него.
        """
        prefix = '/new_reports'
        environ['PATH_INFO'] = '/other/path'
        middleware = PrefixMiddleware(mock_app, prefix)
        middleware(environ, lambda *args: None)

        assert environ['SCRIPT_NAME'] == prefix
        assert environ['PATH_INFO'] == '/other/path'

    def test_prefix_middleware_calls_underlying_app(self, mock_app, environ):
        """
        Проверяет, что middleware вызывает оборачиваемое приложение после изменения окружения.
        """
        prefix = '/new_reports'
        middleware = PrefixMiddleware(mock_app, prefix)
        
        mock_start_response = Mock()
        middleware(environ, mock_start_response)

        mock_app.assert_called_once_with(environ, mock_start_response)

    def test_prefix_middleware_case_insensitive_prefix_not_applied(self, mock_app, environ):
        """
        Проверяет, что префикс применяется строго как указано — без учёта регистра.
        """
        prefix = '/new_reports'
        environ['PATH_INFO'] = '/NEW_REPORTS/test/path'
        middleware = PrefixMiddleware(mock_app, prefix)
        middleware(environ, lambda *args: None)

        assert environ['SCRIPT_NAME'] == prefix
        assert environ['PATH_INFO'] == '/NEW_REPORTS/test/path'
