# from datetime import datetime
#
# from sqlalchemy import Integer, String, Boolean, func, ForeignKey, TIMESTAMP
# from sqlalchemy.orm import Mapped, mapped_column, relationship
#
# from config.db import Base
#
#
# class Role(Base):
#     __tablename__ = "roles"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
#     users: Mapped[list["User"]] = relationship("User", back_populates="role")
#
#
# class User(Base):
#     __tablename__ = "users"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
#     email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
#     hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=True)
#     avatar_url: Mapped[str] = mapped_column(String, nullable=True)
#     created_at: Mapped["datetime"] = mapped_column(
#         TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
#     )
#
#
#     role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
#     photos: Mapped[list["Photo"]] = relationship("Photo", back_populates="owner", lazy="selectin")
#     comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", lazy="selectin")
#
#
