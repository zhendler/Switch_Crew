from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    func,
    ForeignKey,
    TIMESTAMP,
    text,
    Table,
    Column,
    Text,
    Date,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db import Base
from src.reports.schemas import ReportStatus


class Role(Base):
    """
    Role Model.

    Represents a user role in the system (e.g., Admin, Moderator).

    Attributes:
        id (int): The unique identifier of the role.
        name (str): The unique name of the role.
        users (list[User]): A one-to-many relationship linking users
        to this role.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


"""
photo_tags Table.

Represents a many-to-many relationship between Photos and Tags.

Columns:
    photo_id (int): Foreign key referencing the ID of the Photo.
    tag_id (int): Foreign key referencing the ID of the Tag.
"""
photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

photo_reactions = Table(
    "photo_reactions",
    Base.metadata,
    Column("photo_id", ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "reaction_id", ForeignKey("reactions.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.now()),
)


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    photos: Mapped[list["Photo"]] = relationship(
        "Photo", secondary=photo_reactions, back_populates="reactions", lazy="selectin"
    )
    user: Mapped["User"] = relationship(
        "User", secondary=photo_reactions, back_populates="reactions", lazy="selectin"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    photo_id: Mapped[int | None] = mapped_column(ForeignKey("photos.id", ondelete="CASCADE"), nullable=True)
    comment_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=ReportStatus.PENDING.value)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Користувач, що подав скаргу
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Користувач, на якого подано скаргу
    reported_user: Mapped["User"] = relationship("User", foreign_keys=[reported_user_id], lazy="selectin")

    # Фото, на яке подано скаргу (якщо скарга на фото)
    photo: Mapped["Photo"] = relationship("Photo", back_populates="reports", lazy="selectin")

    # Коментар, на який подано скаргу (якщо скарга на коментар)
    comment: Mapped["Comment"] = relationship("Comment", back_populates="reports", lazy="selectin")



class User(Base):
    """
    User Model.

    Represents a system user.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): A unique username for the user.
        first_name (str | None): The first name of the user (optional).
        last_name (str | None): The last name of the user (optional).
        birth_date (date | None): The user's birth date (optional).
        country (str | None): The country of the user (optional).
        is_banned (bool): Indicates whether the user is banned.
        email (str): A unique email address for the user.
        hashed_password (str): The hashed password of the user.
        is_active (bool): Indicates whether the user is active.
        role_id (int): The role ID associated with the user.
        avatar_url (str | None): The URL of the user's avatar (optional).
        created_at (datetime): The creation timestamp of the user.
        updated_at (datetime): The last update timestamp of the user.
        role (Role): A many-to-one relationship with the Role model.
        photos (list[Photo]): A one-to-many relationship with the Photo model.
        comments (list[Comment]): A one-to-many relationship with the Comment model.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
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
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    photos: Mapped[list["Photo"]] = relationship(
        "Photo", back_populates="owner", lazy="selectin", cascade="all, delete"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="user", lazy="selectin", cascade="all, delete"
    )
    reactions: Mapped[list["Reaction"]] = relationship(
        "Reaction", secondary=photo_reactions, back_populates="user", lazy="selectin", cascade="all, delete"
    )
    # Зв'язок з підписками, де користувач є підписником
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="[Subscription.subscriber_id]",
        back_populates="subscriber",
        lazy="selectin",
    )
    # Зв'язок з підписками, де користувач є тим, на кого підписуються
    subscribed_by: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="[Subscription.subscribed_to_id]",
        back_populates="subscribed_to",
        lazy="selectin",
    )
    # Скарги, які подав користувач
    submitted_reports: Mapped[list["Report"]] = relationship("Report", foreign_keys=[Report.user_id], lazy="selectin")

    # Скарги, подані на цього користувача
    received_reports: Mapped[list["Report"]] = relationship("Report", foreign_keys=[Report.reported_user_id],
                                                            lazy="selectin")



class Photo(Base):
    """
    Photo Model.

    Represents a photo uploaded by a user.

    Attributes:
        id (int): The unique identifier of the photo.
        url_link (str): The URL of the photo.
        description (str | None): The description of the photo (optional).
        rating (int | None): The rating of the photo (optional).
        qr_core_url (str | None): The QR code URL for the photo (optional).
        owner_id (int): The user ID of the photo's owner.
        created_at (datetime): The timestamp when the photo was created.
        owner (User): A many-to-one relationship with the User model.
        comments (list[Comment]): A one-to-many relationship with the Comment model.
        tags (list[Tag]): A many-to-many relationship with the Tag model via a helper table.
        ratings (list[PhotoRating]): A one-to-many relationship with the PhotoRating model.
    """

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url_link: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    qr_core_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Відношення з User
    owner: Mapped["User"] = relationship(
        "User", back_populates="photos", lazy="selectin"
    )
    # Відношення з Comment
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="photo", lazy="selectin", cascade="all, delete"
    )
    # Відношення з Tag через проміжну таблицю
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=photo_tags, back_populates="photos", lazy="selectin"
    )
    ratings: Mapped[list["PhotoRating"]] = relationship(
        "PhotoRating", back_populates="photo", lazy="selectin"
    )
    reactions: Mapped[list["Reaction"]] = relationship(
        "Reaction", secondary=photo_reactions, back_populates="photos", lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="photo", lazy="selectin"
    )


class Comment(Base):
    """
    Comment Model.

    Represents a comment made by a user under a specific photo.

    Attributes:
        id (int): The unique identifier of the comment.
        content (str): The content of the comment.
        user_id (int): The ID of the user who made the comment.
        photo_id (int): The ID of the photo under which the comment is made.
        created_at (datetime): The timestamp when the comment was created.
        updated_at (datetime): The timestamp when the comment was last updated.
        user (User): A many-to-one relationship with the User model.
        photo (Photo): A many-to-one relationship with the Photo model.
    """

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    photo_id: Mapped[int | None] = mapped_column(ForeignKey("photos.id", ondelete="CASCADE"),
                                                 nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"),
                                                  nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    photo: Mapped["Photo"] = relationship("Photo", lazy="selectin")

    parent: Mapped["Comment"] = relationship(
        "Comment", remote_side=[id], back_populates="replies", lazy="selectin"
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="parent", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="comment", lazy="selectin"
    )


class Tag(Base):
    """
    Tag Model.

    Represents a tag that can be associated with one or more photos.

    Attributes:
        id (int): The unique identifier of the tag.
        name (str): The unique name of the tag.
        photos (list[Photo]): A many-to-many relationship with the Photo model via the photo_tags table.
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    photos: Mapped[list["Photo"]] = relationship(
        "Photo", secondary=photo_tags, back_populates="tags", lazy="selectin"
    )


class PhotoRating(Base):
    """
    PhotoRating Model.

    Represents a user's rating for a specific photo.

    Attributes:
        id (int): The unique identifier of the photo rating.
        photo_id (int): The ID of the rated photo.
        user_id (int): The ID of the user who gave the rating.
        rating (int): The numerical rating given by the user.
        photo (Photo): A many-to-one relationship with the Photo model.
        user (User): A many-to-one relationship with the User model.
    """

    __tablename__ = "photo_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    # Відношення з Photo
    photo: Mapped["Photo"] = relationship(
        "Photo", back_populates="ratings", lazy="selectin"
    )
    # Відношення з User
    user: Mapped["User"] = relationship("User", lazy="selectin")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    #особа котра підписується 
    subscriber_id: Mapped[int] = mapped_column( 
        Integer, ForeignKey("users.id"), nullable=False
    )

    #користувач на кого підписалися
    subscribed_to_id: Mapped[int] = mapped_column( 
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    subscriber: Mapped["User"] = relationship(
        "User",
        foreign_keys=[subscriber_id],
        back_populates="subscriptions",
        lazy="selectin",
    )
    subscribed_to: Mapped["User"] = relationship(
        "User",
        foreign_keys=[subscribed_to_id],
        back_populates="subscribed_by",
        lazy="selectin",
    )
