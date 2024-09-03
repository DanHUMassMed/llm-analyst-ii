from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)
    email = Column(String, unique=True)
    verified = Column( Boolean, default=False)
    verification_token = Column(String)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password = pwd_context.hash(kwargs["password"])

class UserIn(BaseModel):
    first_name: str
    last_name: str
    password: str
    email: EmailStr

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    verified: bool