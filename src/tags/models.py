from sqlalchemy import Column, Integer, String
from config.db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

#     photos = relationship('Photo', secondary='photo_tags', back_populates='tags')
#
#
# class PhotoTag(Base):
#     __tablename__ = 'photo_tags'
#
#     photo_id = Column(Integer, ForeignKey('photos.id', ondelete="CASCADE"), primary_key=True)
#     tags_id = Column(Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)