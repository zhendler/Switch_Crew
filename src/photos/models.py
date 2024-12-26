# from sqlalchemy import Column, Integer, String, ForeignKey, Table
# from sqlalchemy.orm import relationship
# from config.db import Base

# photo_tags = Table(
#     "photo_tags",
#     Base.metadata,
#     Column("photo_id", Integer, ForeignKey("photos.id")),
#     Column("tag_id", Integer, ForeignKey("tags.id")),
# )


# class Photo(Base):
#     __tablename__ = "photos"

#     id = Column(Integer, primary_key=True, index=True)
#     public_id = Column(String, unique=True, index=True)
#     description = Column(String)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     user = relationship("User", back_populates="photos")
#     tags = relationship("Tag", secondary="photo_tags", back_populates="photos")
#     transformed_url = Column(String, nullable=True)
#     qr_code = Column(String, nullable=True)


# class Tag(Base):
#     __tablename__ = "tags"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, nullable=False)

#     photos = relationship("Photo", secondary=photo_tags, back_populates="tags")
