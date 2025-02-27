from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pymongo import MongoClient

from mapping_suite_sdk.models.core import CoreModel

T = TypeVar('T', bound=CoreModel)


class RepositoryError(Exception):
    pass


class ModelNotFoundError(RepositoryError):
    pass


class RepositoryABC(Generic[T], ABC):
    @abstractmethod
    def create(self, model: T) -> str:
        pass

    @abstractmethod
    def read(self, model_id: str) -> T:
        pass

    @abstractmethod
    def read_many(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        pass

    @abstractmethod
    def update(self, model: T) -> T:
        pass

    @abstractmethod
    def delete(self, model_id: str) -> None:
        pass


class MongoDBRepository(RepositoryABC[T]):
    def __init__(
            self,
            model_class: Type[T],
            mongo_client: MongoClient,
            database_name: str,
            collection_name: Optional[str] = None
    ):
        self.model_class = model_class
        self.client = mongo_client
        self.database = self.client[database_name]
        self.collection_name = collection_name or model_class.__name__
        self.collection = self.database[self.collection_name]

    def create(self, model: T) -> T:
        model_dict = model.model_dump(by_alias=True, mode="json")
        self.collection.insert_one(model_dict)

        return model

    def read(self, model_id: str) -> T:
        result = self.collection.find_one({"_id": model_id})
        if result is None:
            raise ModelNotFoundError(f"Model with ID {model_id} not found")

        return self.model_class.model_validate(result)

    def read_many(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        query = filters or {}
        results = self.collection.find(query)
        models = []
        for doc in results:
            models.append(self.model_class.model_validate(doc))

        return models

    def update(self, model: T) -> T:
        model_dict = model.model_dump(by_alias=True, mode="json")
        query = {'_id': model.id}
        existing = self.collection.find_one(query)
        if existing is None:
            raise ModelNotFoundError(f"Model with ID {model.id} not found")
        self.collection.replace_one(query, model_dict)

        return model

    def delete(self, model_id: str) -> None:
        result = self.collection.delete_one({'_id': model_id})

        if result.deleted_count < 1:
            raise ModelNotFoundError(f"Model with ID {model_id} not found")

    def __del__(self):
        self.client.close()
