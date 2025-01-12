from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CategoryModel(BaseModel):
    id: int
    keyword: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "keyword": "tecnología"
        }
    })

class AddCategoryModel(BaseModel):
    keyword: str

    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "keyword": "data science"
        }
    })

class AddCategoriesResponseModel(BaseModel):
    message: str
    categories: List[CategoryModel]
    skipped_categories: Optional[List[str]] = None  # Nuevas categorías ignoradas

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Categories added successfully with some duplicates skipped",
            "categories": [
                {"id": 4, "keyword": "data science"},
                {"id": 5, "keyword": "machine learning"}
            ],
            "skipped_categories": ["blockchain", "tecnología"]  # Duplicados ignorados
        }
    })

class CategoriesResponseModel(BaseModel):
    user_id: int
    email: str
    categories: List[CategoryModel]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": 42,
            "email": "example@example.com",
            "categories": [
                {"id": 1, "keyword": "tecnología"},
                {"id": 2, "keyword": "innovación"},
                {"id": 3, "keyword": "blockchain"}
            ]
        }
    })

class ErrorResponseModel(BaseModel):
    detail: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "detail": "Usuario no encontrado."
        }
    })

class DeleteCategoriesResponseModel(BaseModel):
    message: str
    deleted_categories: List[CategoryModel]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Categories deleted successfully",
            "deleted_categories": [
                {"id": 1, "keyword": "tecnología"},
                {"id": 3, "keyword": "blockchain"}
            ]
        }
    })
