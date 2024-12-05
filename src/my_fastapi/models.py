from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, text
import uuid
from typing import Annotated


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str]
