# main.py
# To run this backend server:
# 1. Make sure you have Python and PostgreSQL installed and your 'shovik07' database is set up.
# 2. Create a .env file in this directory with your DATABASE_URL.
# 3. Install all necessary libraries with this single command:
#    pip install fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary pydantic[email] python-dotenv
# 4. In your terminal, run the command to start the server:
#    uvicorn main:app --reload
# 5. Once running, go to http://127.0.0.1:8000/docs to add and manage your portfolio data.

import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ARRAY
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables. Please create a .env file.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- SQLAlchemy Models (Database Tables) ---

class ProfileDB(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String, unique=True)
    linkedin_url = Column(String)
    github_url = Column(String)
    portfolio_url = Column(String, nullable=True)

class EducationDB(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String, index=True)
    degree = Column(String)
    cgpa = Column(Float)
    duration = Column(String)
    location = Column(String)

class ExperienceDB(Base):
    __tablename__ = "experience"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True)
    role = Column(String)
    duration = Column(String)
    description = Column(ARRAY(String))

class ProjectDB(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    technologies = Column(ARRAY(String))
    description = Column(ARRAY(String))

class SkillCategoryDB(Base):
    __tablename__ = "skill_categories"
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True, index=True)
    skills = Column(ARRAY(String))

class CertificationDB(Base):
    __tablename__ = "certifications"
    id = Column(Integer, primary_key=True, index=True)
    issuer = Column(String)
    title = Column(String)


# --- Pydantic Schemas for API ---

# Base schemas for creation (don't include 'id')
class ProfileCreate(BaseModel):
    name: str
    phone: str
    email: str
    linkedin_url: HttpUrl
    github_url: HttpUrl
    portfolio_url: Optional[HttpUrl] = None

class EducationCreate(BaseModel):
    institution: str
    degree: str
    cgpa: float
    duration: str
    location: str

class ExperienceCreate(BaseModel):
    company: str
    role: str
    duration: str
    description: List[str]

class ProjectCreate(BaseModel):
    title: str
    technologies: List[str]
    description: List[str]

class SkillCategoryCreate(BaseModel):
    category_name: str
    skills: List[str]

class CertificationCreate(BaseModel):
    issuer: str
    title: str

# Schemas for reading data (include 'id' and ORM mode)
class Profile(ProfileCreate):
    id: int
    class Config:
        from_attributes = True

class Education(EducationCreate):
    id: int
    class Config:
        from_attributes = True

class Experience(ExperienceCreate):
    id: int
    class Config:
        from_attributes = True

class Project(ProjectCreate):
    id: int
    class Config:
        from_attributes = True

class SkillCategory(SkillCategoryCreate):
    id: int
    class Config:
        from_attributes = True

class Certification(CertificationCreate):
    id: int
    class Config:
        from_attributes = True

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Shovik Banerjee's Portfolio API",
    description="A fully manageable API for a personal portfolio website.",
    version="3.0.0",
)

# CORS Middleware
origins = ["http://localhost", "http://localhost:3000", "http://localhost:8080"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Create Database Tables on Startup ---
@app.on_event("startup")
def on_startup():
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"An error occurred during startup table creation: {e}")
        print("Please ensure your DATABASE_URL is correct and the PostgreSQL server is running.")

# --- API Endpoints ---

@app.get("/", summary="Root endpoint")
def read_root():
    return {"message": "Welcome to the Portfolio API. Go to /docs to manage data."}

# --- Profile Endpoints (Singleton) ---
@app.post("/profile", response_model=Profile, summary="Create Profile")
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    # This endpoint should ideally be called only once.
    if db.query(ProfileDB).first():
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")
    db_profile = ProfileDB(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.get("/profile", response_model=Optional[Profile], summary="Get Profile")
def get_profile(db: Session = Depends(get_db)):
    return db.query(ProfileDB).first()

@app.put("/profile", response_model=Profile, summary="Update Profile")
def update_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(ProfileDB).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found. Use POST to create one.")
    for key, value in profile.model_dump().items():
        setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile

# --- Education Endpoints (Singleton) ---
@app.post("/education", response_model=Education, summary="Create Education")
def create_education(education: EducationCreate, db: Session = Depends(get_db)):
    if db.query(EducationDB).first():
        raise HTTPException(status_code=400, detail="Education entry already exists. Use PUT to update.")
    db_education = EducationDB(**education.model_dump())
    db.add(db_education)
    db.commit()
    db.refresh(db_education)
    return db_education

@app.get("/education", response_model=Optional[Education], summary="Get Education")
def get_education(db: Session = Depends(get_db)):
    return db.query(EducationDB).first()
    
@app.put("/education", response_model=Education, summary="Update Education")
def update_education(education: EducationCreate, db: Session = Depends(get_db)):
    db_education = db.query(EducationDB).first()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education not found. Use POST to create one.")
    for key, value in education.model_dump().items():
        setattr(db_education, key, value)
    db.commit()
    db.refresh(db_education)
    return db_education

# --- Generic CRUD Functions for List-based Items ---
def create_item(db: Session, model_db, schema_create):
    db_item = model_db(**schema_create.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, model_db):
    return db.query(model_db).all()

def delete_item(db: Session, model_db, item_id: int):
    db_item = db.query(model_db).filter(model_db.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}

# --- Experience Endpoints ---
@app.post("/experience", response_model=Experience, summary="Add Experience")
def add_experience(experience: ExperienceCreate, db: Session = Depends(get_db)):
    return create_item(db, ExperienceDB, experience)

@app.get("/experience", response_model=List[Experience], summary="Get All Experiences")
def get_all_experiences(db: Session = Depends(get_db)):
    return get_items(db, ExperienceDB)

@app.delete("/experience/{exp_id}", summary="Delete Experience")
def delete_experience(exp_id: int, db: Session = Depends(get_db)):
    return delete_item(db, ExperienceDB, exp_id)

# --- Project Endpoints ---
@app.post("/projects", response_model=Project, summary="Add Project")
def add_project(project: ProjectCreate, db: Session = Depends(get_db)):
    return create_item(db, ProjectDB, project)

@app.get("/projects", response_model=List[Project], summary="Get All Projects")
def get_all_projects(db: Session = Depends(get_db)):
    return get_items(db, ProjectDB)

@app.delete("/projects/{proj_id}", summary="Delete Project")
def delete_project(proj_id: int, db: Session = Depends(get_db)):
    return delete_item(db, ProjectDB, proj_id)

# --- Skills Endpoints ---
@app.post("/skills", response_model=SkillCategory, summary="Add Skill Category")
def add_skill_category(skill: SkillCategoryCreate, db: Session = Depends(get_db)):
    return create_item(db, SkillCategoryDB, skill)

@app.get("/skills", response_model=List[SkillCategory], summary="Get All Skill Categories")
def get_all_skill_categories(db: Session = Depends(get_db)):
    return get_items(db, SkillCategoryDB)

@app.delete("/skills/{skill_id}", summary="Delete Skill Category")
def delete_skill_category(skill_id: int, db: Session = Depends(get_db)):
    return delete_item(db, SkillCategoryDB, skill_id)

# --- Certifications Endpoints ---
@app.post("/certifications", response_model=Certification, summary="Add Certification")
def add_certification(cert: CertificationCreate, db: Session = Depends(get_db)):
    return create_item(db, CertificationDB, cert)

@app.get("/certifications", response_model=List[Certification], summary="Get All Certifications")
def get_all_certifications(db: Session = Depends(get_db)):
    return get_items(db, CertificationDB)

@app.delete("/certifications/{cert_id}", summary="Delete Certification")
def delete_certification(cert_id: int, db: Session = Depends(get_db)):
    return delete_item(db, CertificationDB, cert_id)
