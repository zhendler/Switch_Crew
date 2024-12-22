#there will be comments

from sqlalchemy import String, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db import Base


class Comment(Base):
    __tablename__ = "comments"

    id:Mapped[int] = mapped_column(Integer,primary_key=True, index=True)
    content:Mapped[str] = mapped_column(String, index=True)
    owner_id:Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    photo_id:Mapped[int] = mapped_column(Integer, ForeignKey("photo.id"), nullable=True)
    created_at:Mapped[str] = mapped_column(Date, index=True)
    owner: Mapped["User"] = relationship("User", back_populates="comments", lazy="selectin")