from pydantic import BaseModel, field_validator
from enum import Enum


class MergeSchema(BaseModel):
    web_file: str
    bitrix_file: str

    @field_validator('web_file')
    def validate_web_extension(cls, value):
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл веб системы должен иметь расширение .xlsx")
        return value
    
    @field_validator('bitrix_file')
    def validate_bitrix_extension(cls, value):
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл битрикс должен иметь расширение .xlsx")
        return value

class FormatSchema(BaseModel):
    format_file: str

    @field_validator('format_file')
    def validate_excel_extension(cls, value):
        if not value.lower().endswith('.xlsx'):
            raise ValueError("Файл должен иметь расширение .xlsx")
        return value

class FileType(str, Enum):
    formated = "formated"
    merged = "merged"

class DownloadSchema(BaseModel):
    file_path: str
    file_type: FileType


class SuccesSchema(BaseModel):
    message: str # Сообщение для вывода на экран
    download_link: str # Ссылка для скачивания файла

class ErrorSchema(BaseModel):
    message: str
    code: int
