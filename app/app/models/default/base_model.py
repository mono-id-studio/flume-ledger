from typing import Any
from django.db.models import Model, DateTimeField
from django.forms import model_to_dict


class BaseModel(Model):
    """
    Base model class that all models should inherit from.
    """

    created_at: DateTimeField = DateTimeField(auto_now_add=True)
    updated_at: DateTimeField = DateTimeField(auto_now=True)

    def relation(self: "BaseModel", name: str) -> Any:
        """
        Return the name of the foreign key field.
        """
        return getattr(self, name)

    def dict(self: "BaseModel") -> dict[str, Any]:
        """
        Return the model as a dictionary.
        """
        return model_to_dict(self)

    class Meta:
        abstract = True
