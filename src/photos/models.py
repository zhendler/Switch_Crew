# from datetime import datetime
#
# from config.db import Base
# from src.tags.models import photo_tags, Tag
#
# from sqlalchemy import String, Integer, ForeignKey, TIMESTAMP, func, Text
# from sqlalchemy.orm import relationship, Mapped, mapped_column
#
#
#
#
#
class Photo(Base):
# #     __tablename__ = "photos"
# #
# #     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
# #     url_link: Mapped[str] = mapped_column(String(255), nullable=False)
# #     description: Mapped[str | None] = mapped_column(Text, nullable=True)
# #     qr_core_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
# #     owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
# #     created_at: Mapped["datetime"] = mapped_column(
# #         TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
# #     )
# #
# #     # Відношення з User
# #     owner: Mapped["User"] = relationship("User", back_populates="photos", lazy="selectin")
# #     # Відношення з Comment
# #     comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="photo", lazy="selectin")
# #     # Відношення з Tag через проміжну таблицю
# #     tags: Mapped[list["Tag"]] = relationship(
# #         "Tag",
# #         secondary=photo_tags,
# #         back_populates="photos",
# #         lazy="selectin"
# #     )
#
