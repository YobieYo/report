from pydantic import BaseModel, field_validator
from enum import Enum

class MergeSchema(BaseModel):
    """
    Схема данных для модели объединения файлов.

    Используется для валидации входных данных, полученных от клиента при отправке запроса на объединение.
    Обязательные поля:
        - web_file: имя файла из веб-системы (должно иметь расширение .xlsx)
        - bitrix_file: имя файла из Битрикс (должно иметь расширение .xlsx)

    """

    web_file: str
    bitrix_file: str

    @field_validator('web_file')
    def validate_web_extension(cls, value: str) -> str:
        """
        Проверяет, что имя файла из веб-системы имеет расширение `.xlsx`.

        :param value: Имя файла для проверки.
        :type value: str
        :raises ValueError: Если расширение файла не `.xlsx`.
        :return: Возвращается оригинальное значение, если валидация успешна.
        :rtype: str
        """
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл веб системы должен иметь расширение .xlsx")
        return value

    @field_validator('bitrix_file')
    def validate_bitrix_extension(cls, value: str) -> str:
        """
        Проверяет, что имя файла из Битрикс имеет расширение `.xlsx`.

        :param value: Имя файла для проверки.
        :type value: str
        :raises ValueError: Если расширение файла не `.xlsx`.
        :return: Возвращается оригинальное значение, если валидация успешна.
        :rtype: str
        """
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл битрикс должен иметь расширение .xlsx")
        return value

class FormatSchema(BaseModel):
    """
    Схема данных для модели форматирования файла.

    Используется для валидации входных данных, полученных от клиента при отправке запроса на форматирование.
    Обязательные поля:
        - format_file: имя файла, который будет обработан (должно иметь расширение .xlsx)
    """

    format_file: str

    @field_validator('format_file')
    def validate_excel_extension(cls, value: str) -> str:
        """
        Проверяет, что имя файла имеет расширение `.xlsx`.

        :param value: Имя файла для проверки.
        :type value: str
        :raises ValueError: Если расширение файла не `.xlsx`.
        :return: Возвращается оригинальное значение, если валидация успешна.
        :rtype: str
        """
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл должен иметь расширение .xlsx")
        return value

class SuccesSchema(BaseModel):
    """
    Схема данных для успешного ответа.

    Используется для формирования структурированного JSON-ответа при успешной обработке запроса.
    Обязательные поля:
        - message: текстовое сообщение, предназначенное для вывода пользователю
        - download_link: ссылка на скачивание результата обработки
    """

    message: str  # Сообщение для вывода на экран
    download_link: str  # Ссылка для скачивания файла

class ErrorSchema(BaseModel):
    """
    Схема данных для ответа с ошибкой.

    Используется для формирования структурированного JSON-ответа при возникновении ошибок.
    Обязательные поля:
        - message: текстовое описание ошибки
        - code: HTTP-код ошибки (например, 400, 500)
    """

    message: str  # Сообщение об ошибке
    code: int     # Код ошибки

