from datetime import datetime

from sqlalchemy import Integer, String, Boolean, func, ForeignKey, TIMESTAMP, text, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )


    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    photos: Mapped[list["Photo"]] = relationship("Photo", back_populates="owner", lazy="selectin")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", lazy="selectin")


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

    # Відношення з User
    owner: Mapped["User"] = relationship("User", back_populates="photos", lazy="selectin")
    # Відношення з Comment
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="photo", lazy="selectin")
    # Відношення з Tag через проміжну таблицю
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=photo_tags,
        back_populates="photos",
        lazy="selectin"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    photo: Mapped["Photo"] = relationship("Photo", lazy="selectin")




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
