from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user_model import User, Base
from app.utils.email_util import email_verification, reset_password_email
import uvicorn
from passlib.context import CryptContext
from datetime import datetime


engine = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Event Startup
    engine = create_engine("sqlite:///users.db")
    Base.metadata.create_all(engine)

    yield
    # On Event Shutdown
    engine.dispose()


app = FastAPI(lifespan=lifespan)

# Database setup
engine = create_engine("sqlite:///users.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request, "form_fields":{},})

@app.post("/register", response_class=HTMLResponse)
async def post_register(    
    request: Request, 
    email: EmailStr = Form(...), 
    last_name: str = Form(...), 
    first_name: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db) # type: ignore
):
    
    errors = {}
    form_fields = {"email":email, "last_name":last_name, "first_name":first_name, "password":password}
    
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters long. Include multiple words and phrases to make it more secure."
        
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        errors["email"] = "An account already exists with this email."
    if errors:
        #print(f"form password {request.form['password']}")
        return templates.TemplateResponse(
            "sign_up.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
    
    try:
        token = uuid.uuid4().hex
        db_user = User(first_name=first_name, last_name=last_name, password=password, email=email, verification_token=token)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        email_verification(email, token, first_name)
    except Exception as e:
        errors["database"] = "Sorry we are unable to create Accounts at this time. Please try agian later."
        return templates.TemplateResponse(
            "sign_up.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
    return templates.TemplateResponse("confirm_email_sent.html", {"request": request, "form_fields":form_fields})

# Verification endpoint
@app.get("/verify/{token}", response_class=HTMLResponse)
async def get_verify(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if user:
        user.verified = True
        db.commit()
        db.refresh(user)
        errors = {"verified":"Your email has been verified."}
        return templates.TemplateResponse("sign_in.html", {"request": request, "form_fields":{}, "errors": errors})
    # ignore any tokens that do not match

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("sign_in.html", {"request": request, "form_fields":{}})

@app.post("/login", response_class=HTMLResponse)
async def post_login(    
    request: Request, 
    email: EmailStr = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db) # type: ignore
):
    errors = {}
    db_user = db.query(User).filter(User.email == email).first()
    valid_login=False
    if db_user:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        valid_login = pwd_context.verify(password, db_user.password)
        
    if not valid_login:
        errors["login"] = "Email or Password are incorrect."
        form_fields = {"email":email, "password":password}
        return templates.TemplateResponse(
            "sign_in.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
        
    if not db_user.verified:
        errors["login"] = "Email has not been verified.\nCheck your email or reset password with Forgot Passowrd."
        form_fields = {"email":email, "password":password}
        return templates.TemplateResponse(
            "sign_in.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
        
    return templates.TemplateResponse("index.html", {"request": request})
        
@app.get("/reset-password-request", response_class=HTMLResponse)
async def get_reset_password_request(request: Request):
    return templates.TemplateResponse("reset_password_request.html", {"request": request, "form_fields":{}})

@app.post("/reset-password-request", response_class=HTMLResponse)
async def post_reset_password_request(    
    request: Request, 
    email: EmailStr = Form(...), 
    db: Session = Depends(get_db) # type: ignore
):
    errors = {}
    form_fields={"email":email}
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        token = uuid.uuid4().hex
        client_ip = request.client.host
        try:
            db_user.verification_token=token
            db.commit()
            db.refresh(db_user)
            reset_password_email(email, token, db_user.first_name, client_ip)
        except Exception as e:
            errors["database"] = "Sorry we are unable to reset your password at this time. Please try agian later."
            return templates.TemplateResponse(
                "reset_password_request.html", {"request": request, "form_fields":form_fields, "errors":errors}
            )
    else:
        errors["email"] = "Error: Email not found."
        return templates.TemplateResponse(
            "reset_password_request.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
        
    return templates.TemplateResponse("reset_password_email_sent.html", {"request": request, "form_fields":form_fields})

@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def get_reset_password(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if user:
        return templates.TemplateResponse("reset_password.html", {"request": request, "form_fields":{"email":user.email}})
    
    return templates.TemplateResponse("reset_password_error.html", {"request": request})
    # ignore any tokens that do not match
        
@app.post("/reset-password", response_class=HTMLResponse)
async def post_reset_password(    
    request: Request, 
    email: EmailStr = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db) # type: ignore
):
    errors = {}
    form_fields = {"email":email, "password":password}
    db_user = db.query(User).filter(User.email == email).first()
    
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters long. Include multiple words and phrases to make it more secure."
        
    if not db_user:
        errors["database"] = "Unable to reset password"
        
    if errors:
        return templates.TemplateResponse(
            "reset_password.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
    
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db_user.password = pwd_context.hash(password)
        db_user.verification_token = uuid.uuid4().hex
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        errors["database"] = "Sorry we are unable to reset password at this time. Please try agian later."
        return templates.TemplateResponse(
            "reset_password.html", {"request": request, "form_fields":form_fields, "errors": errors}
        )
    return templates.TemplateResponse("index.html", {"request": request})
    

        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
        