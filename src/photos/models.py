from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, TIMESTAMP, func, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from config.db import Base



class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url_link: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    qr_core_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


    owner: Mapped["User"] = relationship("User", back_populates="photos", lazy="selectin")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="photo", lazy="selectin")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="photo_tags",
        back_populates="photos",
        lazy="selectin"
    )

