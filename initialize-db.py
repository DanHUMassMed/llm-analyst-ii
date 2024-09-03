from sqlalchemy import create_engine, Column, String, Boolean, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from passlib.context import CryptContext

# Define the SQLite database URL
DATABASE_URL = "sqlite:///researcher-web.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a base class for the SQLAlchemy models
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify a password against a hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Define the SQLAlchemy User model
class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    verified = Column(Boolean, default=False)

# Define the Pydantic model for user data validation
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: constr(min_length=8) # type: ignore
    verified: Optional[bool] = False
    

# Create the database and tables
def initialize_database():
    Base.metadata.create_all(engine)
    print("Database initialized and tables created.")

# Example usage of Pydantic for data validation
def create_user(user_data: UserCreate):
    # Create a new SQLAlchemy session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    hashed_password = get_password_hash(user_data.password)

    # Create a new User instance
    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password=hashed_password,
        verified=user_data.verified
    )

    # Add the new user to the session and commit
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"User created: {user.id}, {user.first_name} {user.last_name}")
    
    # Close the session
    session.close()

if __name__ == "__main__":
    initialize_database()
    
    # Example of creating a user with Pydantic validation
    user_data = UserCreate(
        first_name="John",
        last_name="Doe",
        password="123456789",
        email="john.doe@example.com"
    )
    create_user(user_data)