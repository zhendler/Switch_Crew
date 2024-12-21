from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from . import Base


photo_tag = Table('photo_tag', Base.metadata,
    Column('photo_id', Integer, ForeignKey('photo.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

class Photo(Base):
    __tablename__ = 'photo'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    qr_code_url = Column(String, nullable=True)
    tags = relationship('Tag', secondary=photo_tag, back_populates='photos')

class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    photos = relationship('Photo', secondary=photo_tag, back_populates='tags')