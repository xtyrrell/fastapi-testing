from pydantic import BaseModel
import uuid


class Item(BaseModel):
    id: uuid.UUID
    name: str
