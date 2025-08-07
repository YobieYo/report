from typing import Type, TypeVar, Generic, Dict, Any
from ..models import db
from sqlalchemy import and_

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get_all(self):
        return self.model.query.all() 

    def get_by_id(self, id: int) -> T:
        return self.model.query.get(id)

    def exists_by_fields(self, **kwargs) -> bool:
        """Проверяет, существует ли запись с указанными значениями полей."""
        filters = [getattr(self.model, key) == value for key, value in kwargs.items()]
        return db.session.query(db.exists().where(and_(*filters))).scalar()

    def get_by_fields(self, **kwargs) -> T:
        """Возвращает запись с указанными значениями полей, если она существует."""
        filters = [getattr(self.model, key) == value for key, value in kwargs.items()]
        return db.session.query(self.model).filter(and_(*filters)).first()

    def create(self, **kwargs) -> T:
        """Создает новую запись, предварительно проверяя на дубликат."""
        existing = self.get_by_fields(**kwargs)
        if existing:
            return existing
        
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, id: int, **kwargs) -> T:
        instance = self.model.query.get(id)
        if instance:
            # Проверяем, не приведет ли обновление к дублированию
            check_fields = {k: v for k, v in kwargs.items() if k in self.model.__table__.columns}
            if check_fields and self.exists_by_fields(**check_fields):
                existing = self.model.query.filter_by(**check_fields).first()
                if existing.id != id:  # Разрешаем обновление, если это та же запись
                    raise ValueError(f"Обновление приведет к дублированию записи: {check_fields}")
            
            for key, value in kwargs.items():
                setattr(instance, key, value)
            db.session.commit()
        return instance

    def delete(self, id: int) -> bool:
        instance = self.model.query.get(id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
            return True
        return False