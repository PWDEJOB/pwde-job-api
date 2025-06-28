from pydantic import BaseModel
from typing import List

class inputSignupEmployee(BaseModel):
    full_name: str
    email: str
    password: str

class moreInfoEmployee(BaseModel):
    address: str
    phone_number: str
    short_bio: str
    disability: str
    skills: List[str]

class inputSignupEmployer(BaseModel):
    email: str
    password: str
    company_name: str
    company_level: str
    website_url: str
    company_type: str
    industry: str
    admin_name: str
    description: str
    location: str
    tags: List[str]

class loginCreds(BaseModel):
    email: str
    password: str

class updateEmployer(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    
class updateEmployee(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    disability: str
    skills: List[str]

class jobCreation(BaseModel):
    title: str
    company_name: str
    location: str
    job_type: str
    industry: str
    experience: str
    description: str
    skill_1: str
    skill_2: str
    skill_3: str
    skill_4: str
    skill_5: str
    pwd_friendly: bool
    min_salary: float
    max_salary: float

class updateJob(BaseModel):
    title: str
    company_name: str
    location: str
    job_type: str
    industry: str
    experience: str
    description: str
    skill_1: str
    skill_2: str
    skill_3: str
    skill_4: str
    skill_5: str
    pwd_friendly: bool
    min_salary: float
    max_salary: float