from sqlalchemy import Column, String, ForeignKey, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db import Base


photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Відношення з Photo через проміжну таблицю
    photos: Mapped[list["Photo"]] = relationship(
        "Photo",
        secondary=photo_tags,
        back_populates="tags",
        lazy="selectin"
    )

