from pydantic import BaseModel, constr, EmailStr
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

from db import db_engine

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    posts = relationship("Post", back_populates="user")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    text = Column(String, index=True)
    user = relationship("User", back_populates="posts")


Base.metadata.create_all(bind=db_engine)


class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AddPostRequest(BaseModel):
    text: constr(max_length=1048576)
