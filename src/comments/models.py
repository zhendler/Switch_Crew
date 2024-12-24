from datetime import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from config.db import Base



# class Comment(Base):
#     __tablename__ = "comments"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     content: Mapped[str] = mapped_column(String, nullable=False)
#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
#     photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"), nullable=False)
#     created_at: Mapped[datetime] = mapped_column(
#         TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
#     )
#
#     user: Mapped["User"] = relationship("User", lazy="selectin")
#     photo: Mapped["Photo"] = relationship("Photo", lazy="selectin")