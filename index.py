from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile, Depends
from typing import List
import json
from redis_server.redis_client import redis
from models.model import updateEmployer, updateEmployee, loginCreds, inputSignupEmployer, inputSignupEmployee, jobCreation, updateJob
import ast

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_PRIVATE_KEY")
service_key = os.getenv("SUPBASE_SERVICE_KEY")


@app.get("/")
async def root ():
    return {"message":"working"}


@app.get("/preload")
async def preload(request: Request):
    try:
        # Get the auth user ID from the request
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
        
        # Check both employee and employer tables
        employee_check = supabase.table("employee").select("*").eq("user_id", auth_userID).execute()
        employer_check = supabase.table("employers").select("*").eq("user_id", auth_userID).execute()
        
        if employee_check.data:
            return {
                "Status": "Success",
                "isAuthenticated": True,
                "role": "employee",
                "userData": employee_check.data
            }
        elif employer_check.data:
            return {
                "Status": "Success",
                "isAuthenticated": True,
                "role": "employer",
                "userData": employer_check.data
            }
        else:
            return {
                "Status": "Error",
                "isAuthenticated": False,
                "Message": "User not found in either employee or employer tables"
            }  
    except Exception as e:
        # if "Session not found in Redis" in str(e):
        #     return {
        #         "Status": "Error",
        #         "isAuthenticated": False,
        #         "Message": "Not authenticated"
        #     }
        return {
            "Status": "Error",
            "isAuthenticated": False,
            "Message": f"Internal Server Error: {employee_check.data}",
            "Details": str(e)
        }


# functions for retriving session or to be speficifc the user ID
async def getAuthUserIdByToken(redis, access_token):
    value = await redis.get(access_token)
    if value:
        session_data = json.loads(value)
        return session_data.get("auth_userID")
    return None

async def getAuthUserIdFromRequest(redis, request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    access_token = token.split("Bearer ")[1]
    
    auth_userID = await getAuthUserIdByToken(redis, access_token)
    if not auth_userID:
        raise HTTPException(status_code=401, detail="Session not found in Redis")
    
    return auth_userID


#Authentication Process

# Signup for employee and employer
@app.post("/signupEmployee") # signup for employee
async def signUp(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    address: str = Form(None),
    phone_number: str = Form(None),
    short_bio: str = Form(None),
    disability: str = Form(None),
    skills: str = Form(None),
    resume: UploadFile = File(None),
    profile_pic: UploadFile = File(None),
    pwd_id_front: UploadFile = File(None),
    pwd_id_back: UploadFile = File(None)
):
    role = "employee"
    try:
        # First step: Sign up the user
        supabase: Client = create_client(url, key)
        response = supabase.auth.sign_up(
            {
                "email": email, 
                "password": password,
            }
        )
    except Exception as e:
        return{
            "Status":"ERROR",
            "Message":"Signing Up Failed",
            "Details": f"{e}"
        }
    
    if response:
        try:
            # Second step: Insert initial user data
            supabase_insert: Client = create_client(url, key)
            user_data = {
                "user_id": response.user.id,
                "full_name": full_name,
                "email": email,
                "role": role
            }
            
            # If additional info is provided, add it to user_data
            if address:
                user_data["address"] = address
            if phone_number:
                user_data["phone_number"] = phone_number
            if short_bio:
                user_data["short_bio"] = short_bio
            if disability:
                user_data["disability"] = disability
            if skills:
                user_data["skills"] = skills

            # Handle file uploads if provided
            if resume:
                # Validate file type (PDF only)
                if not resume.filename.lower().endswith('.pdf'):
                    return {
                        "Status": "Error",
                        "Message": "Resume must be a PDF file"
                    }
                
                # Validate file size (5MB limit)
                resume_content = await resume.read()
                if len(resume_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "Resume file size must be less than 5MB"
                    }
                
                # Upload resume
                resume_path = f"resumes/{response.user.id}/{resume.filename}"
                supabase.storage.from_("resumes").upload(resume_path, resume_content)
                resume_url = supabase.storage.from_("resumes").get_public_url(resume_path)
                user_data["resume_url"] = resume_url

            if profile_pic:
                # Validate file type (images only)
                allowed_image_types = ['.jpg', '.jpeg', '.png', '.gif']
                file_ext = os.path.splitext(profile_pic.filename)[1].lower()
                if file_ext not in allowed_image_types:
                    return {
                        "Status": "Error",
                        "Message": "Profile picture must be an image file (JPG, JPEG, PNG, or GIF)"
                    }
                
                # Validate file size (5MB limit)
                profile_pic_content = await profile_pic.read()
                if len(profile_pic_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "Profile picture file size must be less than 5MB"
                    }
                
                # Upload profile picture
                profile_pic_path = f"profilepic/{response.user.id}/{profile_pic.filename}"
                supabase.storage.from_("profilepic").upload(profile_pic_path, profile_pic_content)
                profile_pic_url = supabase.storage.from_("profilepic").get_public_url(profile_pic_path)
                user_data["profile_pic_url"] = profile_pic_url

            if pwd_id_front:
                # Validate file type (images only)
                file_ext = os.path.splitext(pwd_id_front.filename)[1].lower()
                if file_ext not in allowed_image_types:
                    return {
                        "Status": "Error",
                        "Message": "PWD ID front must be an image file (JPG, JPEG, PNG, or GIF)"
                    }
                
                # Validate file size (5MB limit)
                pwd_id_front_content = await pwd_id_front.read()
                if len(pwd_id_front_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "PWD ID front file size must be less than 5MB"
                    }
                
                # Upload PWD ID front
                pwd_id_front_path = f"pwdidfront/{response.user.id}/{pwd_id_front.filename}"
                supabase.storage.from_("pwdidfront").upload(pwd_id_front_path, pwd_id_front_content)
                pwd_id_front_url = supabase.storage.from_("pwdidfront").get_public_url(pwd_id_front_path)
                user_data["pwd_id_front_url"] = pwd_id_front_url

            if pwd_id_back:
                # Validate file type (images only)
                file_ext = os.path.splitext(pwd_id_back.filename)[1].lower()
                if file_ext not in allowed_image_types:
                    return {
                        "Status": "Error",
                        "Message": "PWD ID back must be an image file (JPG, JPEG, PNG, or GIF)"
                    }
                
                # Validate file size (5MB limit)
                pwd_id_back_content = await pwd_id_back.read()
                if len(pwd_id_back_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "PWD ID back file size must be less than 5MB"
                    }
                
                # Upload PWD ID back
                pwd_id_back_path = f"pwdidback/{response.user.id}/{pwd_id_back.filename}"
                supabase.storage.from_("pwdidback").upload(pwd_id_back_path, pwd_id_back_content)
                pwd_id_back_url = supabase.storage.from_("pwdidback").get_public_url(pwd_id_back_path)
                user_data["pwd_id_back_url"] = pwd_id_back_url

            # Insert all data into the database
            insert_data = supabase_insert.table("employee").insert(user_data).execute()
            
            return{
                "Status": "Successfull",
                "Message": f"{full_name} has been successfully signed up",
                "Details": insert_data.data
            }
        except Exception as e:
            return{
                "Status":"ERROR",
                "Message:":"Internal error. Data insertion failed",
                "Details": f"{e}"
            }


@app.post("/signupEmployer") # signup for employer
async def signUp(
    email: str = Form(...),
    password: str = Form(...),
    company_name: str = Form(...),
    company_level: str = Form(...),
    website_url: str = Form(...),
    company_type: str = Form(...),
    industry: str = Form(...),
    admin_name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    tags: str = Form(...),
    file: UploadFile = File(...)
):
    role = "employer"
    #signing up the user
    try:
        supabase = create_client(url, key)
        response = supabase.auth.sign_up(
            {
                "email": email, 
                "password": password,
            }
        )
        # print(supabase.auth.get_session())
    except Exception as e:
        return{
            "Status":"ERROR",
            "Message":"Signing Up Failed",
            "Details": f"{e}"
        }
    
    if response:
        try:
            # Handle logo upload
            file_content = await file.read()
            
            # Validate file type (allow common image formats)
            allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_types:
                return {
                    "Status": "ERROR",
                    "Message": "Invalid file type. Allowed types: JPG, JPEG, PNG, GIF"
                }
            
            # Validate file size (5MB limit)
            if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
                return {
                    "Status": "ERROR",
                    "Message": "File size exceeds 5MB limit"
                }
            
            # Upload logo to Supabase storage
            logo_path = f"logos/{response.user.id}/{file.filename}"
            supabase.storage.from_("companylogo").upload(logo_path, file_content)
            
            # Get the public URL for the uploaded logo
            logo_url = supabase.storage.from_("companylogo").get_public_url(logo_path)
            
            supabase_insert = create_client(url, key) #re created a suapsbe client for insertion (Current band aid fix)
            user_data = { # Structure the data to be inserted
                "user_id": response.user.id,
                "email": email,
                "company_name": company_name,
                "company_level": company_level,
                "website_url": website_url,
                "company_type": company_type,
                "industry": industry,
                "admin_name": admin_name,
                "logo_url": logo_url,  # Store the logo URL
                "description": description,
                "location": location,
                "tags": tags,
                "role": role,
            }
            
            # print(user_data)
            
            #Insert data "suer_data" to the table
            insert_data = supabase_insert.table("employers").insert(user_data).execute()
            
            if insert_data.data:
                return{
                    "Status": "Successfull",
                        "Message": f"{company_name} has been successfully signed up",
                        "Details": f"{insert_data}"
                    }
            else:
                return {
                    "Status": "Error",
                    "Message": "Updating not Succesfull",
                    "Details": f"{insert_data}"
                }
        except Exception as e:
            return{
                "Status":"ERROR",
                "Message:":"Internal error. Data insertion failed",
                "Details": f"{e}"
            }





#On this login, auth_userID needs to be retrieve on the client side emaning frontend so it can be use on the other endpoints
        
@app.post("/login-employee")
async def login(user: loginCreds):
    supabase: Client = create_client(url, key)
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password
            }
        )

        # Get the session
        session_key = response.session

        if session_key:
            access_token = session_key.access_token
            refresh_token = session_key.refresh_token
            auth_userID = response.user.id

            session_data = {
                "auth_userID": auth_userID,
                "refresh_token": refresh_token
            }

            # Check if the user is in the employee table
            employee_check = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()

            if employee_check.data:  # check for presence of data
                # Store session in Redis with a key prefix
                await redis.set(access_token, json.dumps(session_data), ex=None)

                return {
                    "Status": "Success",
                    "Message": "Login successful. Session stored in Redis.",
                    "Token": access_token,
                    "Stored User ID": auth_userID
                }
            else:
                return {
                    "Status": "ERROR",
                    "Message": "User is not an employee"
                }
        else:
            return {
                "Status": "ERROR",
                "Message": "No session returned"
            }

    except Exception as e:
        return {
            "Status": "ERROR",
            "Message": "Internal Server Error",
            "Details": str(e)
        }

         
@app.post("/login-employer")
async def login(user: loginCreds):
    supabase: Client = create_client(url, key)
    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password
            }
        )

        # Get the session
        session_key = response.session

        if session_key:
            access_token = session_key.access_token
            refresh_token = session_key.refresh_token
            auth_userID = response.user.id

            session_data = {
                "auth_userID": auth_userID,
                "refresh_token": refresh_token
            }

            # Check if the user is in the employee table
            employee_check = supabase.table("employers").select("*").eq("user_id", auth_userID).single().execute()

            if employee_check.data:  # check for presence of data
                # Store session in Redis with a key prefix
                await redis.set(access_token, json.dumps(session_data), ex=None)

                return {
                    "Status": "Success",
                    "Message": "Login successful. Session stored in Redis.",
                    "Token": access_token,
                    "Stored User ID": auth_userID
                }
            else:
                return {
                    "Status": "ERROR",
                    "Message": "User is not an employee"
                }
        else:
            return {
                "Status": "ERROR",
                "Message": "No session returned"
            }

    except Exception as e:
        return {
            "Status": "ERROR",
            "Message": "Internal Server Error",
            "Details": str(e)
        }

        
#Password reset to be followded after this week

# To send an authenticated request to the backend (e.g., /view-profile):
# Retrieve the access token (from localStorage, sessionStorage, or cookies).
# Add it to the request header as: Authorization: Bearer <access_token>.

# Example (using Fetch API):
#   
#    const accessToken = localStorage.getItem('access_token'); // or from a cookie
#   
#    fetch('http://localhost:8000/view-profile', {
#      method: 'GET',
#      headers: {
#        'Authorization': `Bearer ${accessToken}`
# }
# })

#profile management
@app.get("/view-profile")
async def viewProfile(request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, key)
        
        # print(f"Fetching profile for user_id: {auth_userID}")
        
        #Checking both tables if the user is an employee or employer
        
        response_employer = supabase.table("employers").select("*").eq("user_id", auth_userID).single().execute()
        
        if response_employer.data:
            return {"Profile": response_employer.data}
        
        response_employee = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()
        
        if response_employee.data:
            return {"Profile": response_employee.data}
        
        # Not found in either table
        return {
            "Status": "ERROR",
            "Message": "User profile not found in employers or employees tables"
        }
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return {
            "Status": "ERROR",
            "Message": "Internal Server Error",
            "Details": str(e)
        }

# Profile Update
#this will update only name, skills, and disability 

@app.post("/update-profile/employer")
async def updateProfile(
    request: Request,
    company_name: str = Form(None),
    company_level: str = Form(None),
    website_url: str = Form(None),
    company_type: str = Form(None),
    industry: str = Form(None),
    admin_name: str = Form(None),
    description: str = Form(None),
    location: str = Form(None),
    tags: str = Form(None),
    logo: UploadFile = File(None)
):
    def not_empty(val):
        return val not in [None, ""]
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
        
        # Check if the user is an employer
        search_employer = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if search_employer.data and search_employer.data["user_id"] == auth_userID:
            updated_details = {}

            if not_empty(company_name):
                updated_details["company_name"] = company_name
            if not_empty(company_level):
                updated_details["company_level"] = company_level
            if not_empty(website_url):
                updated_details["website_url"] = website_url
            if not_empty(company_type):
                updated_details["company_type"] = company_type
            if not_empty(industry):
                updated_details["industry"] = industry
            if not_empty(admin_name):
                updated_details["admin_name"] = admin_name
            if not_empty(description):
                updated_details["description"] = description
            if not_empty(location):
                updated_details["location"] = location
            if not_empty(tags):
                updated_details["tags"] = tags

            # Handle logo upload if provided and not empty
            if logo and logo.filename:
                allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
                file_ext = os.path.splitext(logo.filename)[1].lower()
                if file_ext not in allowed_types:
                    # If the file is empty (no filename), just skip updating logo
                    return {
                        "Status": "Error",
                        "Message": "Invalid logo file type. Allowed: JPG, JPEG, PNG, GIF"
                    }
                logo_content = await logo.read()
                if len(logo_content) == 0:
                    # If the file is empty, skip updating logo
                    pass
                elif len(logo_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "Logo file size must be less than 5MB"
                    }
                else:
                    logo_path = f"logos/{auth_userID}/{logo.filename}"
                    supabase.storage.from_("companylogo").upload(logo_path, logo_content)
                    logo_url = supabase.storage.from_("companylogo").get_public_url(logo_path)
                    updated_details["logo_url"] = logo_url

            if not updated_details:
                return {
                    "Status": "Error",
                    "Message": "No valid fields provided for update."
                }

            try:
                update_employer_res = supabase.table("employers").update(updated_details).eq("user_id", auth_userID).execute()
                if update_employer_res.data:
                        return {
                        "Status": "Successfull",
                        "Message": "Update successfull"
                    }
                else:
                    return {
                        "Status": "Error",
                        "Message": "Updating not Succesfull",
                        "Details": f"{update_employer_res}" 
                        }
            except Exception as e:
                if "Duplicate" in str(e) or "already exists" in str(e):
                    return {
                        "Status": "Error",
                        "Message": "A unique field value you are trying to update already exists for another employer.",
                        "Details": str(e)
                    }
                return {
                    "Status": "Error",
                    "Message": "Internal Server Error",
                    "Details": str(e)
                 }
        else:
            return {
                "Status": "Error",
                "Message": "Cant find user",
                "Details": f"{search_employer}" 
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }



@app.post("/update-profile/employee")
async def updateProfile(
    request: Request,
    full_name: str = Form(None),
    address: str = Form(None),
    phone_number: str = Form(None),
    short_bio: str = Form(None),
    disability: str = Form(None),
    skills: str = Form(None),
    resume: UploadFile = File(None),
    profile_pic: UploadFile = File(None)
):
    def not_empty(val):
        return val not in [None, ""]
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
        
        # Check if the user is an employee
        search_employee = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if search_employee.data and search_employee.data["user_id"] == auth_userID:
            updated_details = {}

            if not_empty(full_name):
                updated_details["full_name"] = full_name
            if not_empty(address):
                updated_details["address"] = address
            if not_empty(phone_number):
                updated_details["phone_number"] = phone_number
            if not_empty(short_bio):
                updated_details["short_bio"] = short_bio
            if not_empty(disability):
                updated_details["disability"] = disability
            if not_empty(skills):
                updated_details["skills"] = skills

            # Handle resume upload if provided and not empty
            if resume and resume.filename:
                if not resume.filename.lower().endswith('.pdf'):
                    return {
                        "Status": "Error",
                        "Message": "Resume must be a PDF file"
                    }
                resume_content = await resume.read()
                if len(resume_content) == 0:
                    pass
                elif len(resume_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "Resume file size must be less than 5MB"
                    }
                else:
                    resume_path = f"resumes/{auth_userID}/{resume.filename}"
                    supabase.storage.from_("resumes").upload(resume_path, resume_content)
                    resume_url = supabase.storage.from_("resumes").get_public_url(resume_path)
                    updated_details["resume_url"] = resume_url

            # Handle profile picture upload if provided and not empty
            if profile_pic and profile_pic.filename:
                allowed_image_types = ['.jpg', '.jpeg', '.png', '.gif']
                file_ext = os.path.splitext(profile_pic.filename)[1].lower()
                if file_ext not in allowed_image_types:
                    return {
                        "Status": "Error",
                        "Message": "Profile picture must be an image file (JPG, JPEG, PNG, or GIF)"
                    }
                profile_pic_content = await profile_pic.read()
                if len(profile_pic_content) == 0:
                    pass
                elif len(profile_pic_content) > 5 * 1024 * 1024:
                    return {
                        "Status": "Error",
                        "Message": "Profile picture file size must be less than 5MB"
                    }
                else:
                    profile_pic_path = f"profilepic/{auth_userID}/{profile_pic.filename}"
                    supabase.storage.from_("profilepic").upload(profile_pic_path, profile_pic_content)
                    profile_pic_url = supabase.storage.from_("profilepic").get_public_url(profile_pic_path)
                    updated_details["profile_pic_url"] = profile_pic_url

            if not updated_details:
                return {
                    "Status": "Error",
                    "Message": "No valid fields provided for update."
                }

            try:
                update_employee_res = supabase.table("employee").update(updated_details).eq("user_id", auth_userID).execute()
                if update_employee_res.data:
                        return {
                        "Status": "Successfull",
                        "Message": "Update successfull"
                    }
                else:
                    return {
                        "Status": "Error",
                        "Message": "Updating not Succesfull",
                        "Details": f"{update_employee_res}" 
                        }
            except Exception as e:
                if "Duplicate" in str(e) or "already exists" in str(e):
                    return {
                        "Status": "Error",
                        "Message": "A unique field value you are trying to update already exists for another employee.",
                        "Details": str(e)
                    }
                return {
                    "Status": "Error",
                    "Message": "Internal Server Error",
                    "Details": str(e)
                 }
        else:
            return {
                "Status": "Error",
                "Message": "Cant find user",
                "Details": f"{search_employee}" 
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }

#job shii

#create jobs
# This endpoint is for empployers to be able create jobs, view al jobs listings they created, view a specific job listinsg details, delete, and update

@app.post("/create-jobs")
async def createJob(job: jobCreation, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        #check first if the user exist as an employer
        supabase: Client = create_client(url, service_key)
        search_id = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if search_id:
            # structure teh data to be created
            jobs_data = {
                "user_id": auth_userID,
                "title": job.title,
                "job_description": job.description,
                "skill_1": job.skill_1,
                "skill_2": job.skill_2,
                "skill_3": job.skill_3,
                "skill_4": job.skill_4,
                "skill_5": job.skill_5,
                "pwd_friendly": job.pwd_friendly,
                "company_name": job.company_name,
                "location": job.location,
                "job_type": job.job_type,
                "industry": job.industry,
                "experience": job.experience,
                "min_salary": job.min_salary,
                "max_salary": job.max_salary
            }
            
            insert_response = supabase.table("jobs").insert(jobs_data).execute()
            
            return{
                "Status": "Sucessfull",
                "Message": "Job has been created",
                "Details": f"{insert_response}"
            }
        else:
            return {
                "Status": "Error",
                "Message": "Maybe the employer dosen't exist"
            }
    except Exception as e:
        return{
            "Status": "Internal Server Error",
            "Message": "Some sort of error",
            "Details": f"{e}"
        }

@app.get("/view-all-jobs")
async def viewAllJobs(request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, key)
        
        all_jobs = supabase.table("jobs").select("*").eq("user_id", auth_userID).execute()
        
        if all_jobs:
            return {"jobs": all_jobs.data}
        
        return {
            "Status": "ERROR",
            "Message": "No Jobs Found"
        }
    except Exception as e:
        return{
            "Status": "ERROR",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }

@app.get("/view-job/{id}")
async def viewSpecificJob(id: str):
    try:
        # auth_userID = await getAuthUserIdFromRequest(redis, request) .eq("user_id", auth_userID)
        
        supabase = create_client(url, key)
        
        job = supabase.table("jobs").select("*").eq("id", id).execute()
        
        if job:
            return {
                "Status": "Successfull",
                "Message": f"Job Number {id} Found",
                "Details": job.data
            }
        return {
            "Status": "Error",
            "Message": "Job Not Found"
        }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Error",
            "Details": f"{e}"
        }
@app.post("/delete-job/{id}")
async def deleteJob(request: Request, id: str):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)

        # Check if the user is an employer
        search_id = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()

        if search_id.data and search_id.data["user_id"] == auth_userID:
            #delete the job
            delete_job = supabase.table("jobs").delete().eq("id", id).execute()
            # print(delete_job)
            
            if delete_job.data:  # check if any row was actually deleted
                return {
                    "Status": "Success",
                    "Message": f"Job {id} deleted successfully"
                }
            else:
                return {
                    "Status": "Error",
                    "Message": f"No job found with id {id} to delete.",
                    "Details": f"{delete_job}"
                }
        else:
            return {
                "Status": "Error",
                "Message": "Employer not found or not authorized."
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
        
@app.post("/update-job/{id}")
async def updateSpecificJob(request: Request, id: str, job: updateJob):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)

        # Check if the user is an employer
        search_id = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()

        if search_id.data and search_id.data["user_id"] == auth_userID:
             #build the structure of the update json 
             new_data = {
                "user_id": auth_userID,
                "title": job.title,
                "job_description": job.description,
                "skill_1": job.skill_1,
                "skill_2": job.skill_2,
                "skill_3": job.skill_3,
                "skill_4": job.skill_4,
                "skill_5": job.skill_5,
                "pwd_friendly": job.pwd_friendly,
                "company_name": job.company_name,
                "location": job.location,
                "job_type": job.job_type,
                "industry": job.industry,
                "experience": job.experience,
                "min_salary": job.min_salary,
                "max_salary": job.max_salary
             }
             update_response = supabase.table("jobs").update(new_data).eq("id", id).execute()
            
             if update_response.data:
                 return{
                     "Status": "Successfull",
                     "Message": "Update successfull"
                 }
             else:
                 return {
                     "Status": "Error",
                     "Message": "Updating not Succesfull",
                     "Details": f"{update_response}" 
                 }
        else:
            return{
                "Status": "Error",
                "Message": "Cant find user",
                "Details": f"{search_id}" 
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details":f"{e}"
        }
          
#MAIN ALGO WORKS (Content absed filtering + collaborative filtering)

@app.get("/reco-jobs")
async def reccomendJobs(request: Request):
    try:
        # Get the user details
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, key)

        # Fetch the user details
        search_user = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()

        if not search_user or not search_user.data:
            return {
                "Status": "Error",
                "Message": "Can't find user"
            }

        # user_id = search_user.data.get("user_id")
        disability = search_user.data.get("disability")

        # Parse the skills
        skills_raw = search_user.data.get("skills", "[]")
        if isinstance(skills_raw, list):
            skills_list = skills_raw
        elif isinstance(skills_raw, str):
            try:
                skills_list = ast.literal_eval(skills_raw)
                if not isinstance(skills_list, list):
                    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
            except Exception:
                skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
        else:
            skills_list = []

        user_skills_set = set()
        for skill in skills_list:
            if isinstance(skill, str):
                user_skills_set.add(skill.strip().lower())

        # Fetch jobs based on disability
        if disability == "None":
            jobs_response = supabase.table("jobs").select("*").execute()
            jobs_data = jobs_response.data or []
        else:
            jobs_response = supabase.table("jobs").select("*").eq("pwd_friendly", True).execute()
            jobs_data = jobs_response.data or []

        # Recommendations
        recommendations = []

        for job in jobs_data:
            # Extract job skills
            job_skills = []
            for i in range(1, 6):
                skill = job.get(f"skill_{i}", "")
                if isinstance(skill, str) and skill.strip():
                    job_skills.append(skill.strip().lower())

            job_skills_set = set(job_skills)

            # Calculate skill match score
            matched_skills_set = user_skills_set & job_skills_set
            matched_skills_count = len(matched_skills_set)

            if job_skills_set:
                skill_match_score = matched_skills_count / len(job_skills_set)
            else:
                skill_match_score = 0

            # Create a copy of the job details and add match data
            # Exclude jobs with zero match score
            if skill_match_score > 0:
                job_copy = job.copy()
                job_copy["skill_match_score"] = skill_match_score
                job_copy["matched_skills"] = list(matched_skills_set)
                recommendations.append(job_copy)
                
        # Sort and return top 5 recommendations
        recommendations.sort(key=lambda x: x["skill_match_score"], reverse=True)
        
        for job in recommendations:
            job_id = job["id"]

            # Check if this record already exists
            existing_record = supabase.table("employee_history").select("id").eq("user_id", auth_userID).eq("job_id", job_id).execute()

            if not existing_record.data:
                # Insert the new history record
                supabase.table("employee_history").insert({
                    "user_id": auth_userID,
                    "job_id": job_id
                }).execute()

        return {
            "recommendations": recommendations
        }

    except Exception as e:
        return {
            "error": str(e)
        }

# apply to a job
@app.post("/apply-job/{job_id}")
async def applyingForJob(job_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, key)
        
        # check the user id in auth)userID is an employer
        
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            apply_job = supabase.table("employee_history").update({"applied": True}).eq("job_id", job_id).eq("user_id", auth_userID).execute()
            
            if apply_job.data:
                supabase_job_data_insertion = create_client(url, service_key)
                
                job_data = {
                    "user_id": auth_userID,
                    "job_id": job_id,
                    "status": "under_review"
                }
                
                insert_job_appliead = supabase_job_data_insertion.table("job_applications").insert(job_data).execute()
                return{
                    "Status": "Successfull",
                    "Message": f"You applied to job {job_id}",
                    "Details": insert_job_appliead.data
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "Error/Failed in applying"
                }
        else:
            return {
                "Status": "Error",
                "Message": "Can't find the user"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }

# view all apllicants of a job listing
@app.get("/job/{job_id}/applicants")
async def viewAllApplicantsInJobListing(request: Request, job_id: str):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, key)
        
        check_user = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            get_all_applicants = supabase.table("job_applications").select("*").eq("job_id", job_id).execute()
            
            if get_all_applicants.data:
                return {
                    "Status": "Successfull",
                    "Applicants": get_all_applicants.data
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "No Applicants"
                }
        else:
            return {
                "Status": "Error",
                "Message": "User not Found"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }

@app.post("/logout")
async def logout(request: Request):
    # Debug: Print all headers
    # print("All headers:", dict(request.headers))
    
    token = request.headers.get("Authorization")
    # print("Raw Authorization header:", token)
    
    if not token or not token.startswith("Bearer "):
        # print("Token validation failed - token missing or invalid format")
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    access_token = token.split("Bearer ")[1]
    # print("Extracted access token:", access_token)
    
    try:
        # Delete the session from Redis
        await redis.delete(access_token)
        # print("Successfully deleted token from Redis")
        
        return {
            "Status": "Success",
            "Message": "Successfully logged out"
        }
    except Exception as e:
        # print("Error during logout:", str(e))
        return {
            "Status": "ERROR",
            "Message": "Logout failed",
            "Details": str(e)
        }

@app.post("/upload-resume")
async def uploadResume(request: Request, file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return {
                "Status": "Error",
                "Message": "Only PDF files are allowed"
            }

        # Read file content
        file_content = await file.read()
        
        # Validate file size (e.g., 5MB limit)
        if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
            return {
                "Status": "Error",
                "Message": "File size exceeds 5MB limit"
            }

        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, key)

        # Check if the user is an employee
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()

        if check_user.data and check_user.data["user_id"] == auth_userID:
            try:
                # Upload the resume to the supabase storage
                resume_path = f"resumes/{auth_userID}/{file.filename}"
                supabase.storage.from_("resumes").upload(resume_path, file_content)

                # Update the employee's profile with the resume URL
                resume_url = supabase.storage.from_("resumes").get_public_url(resume_path)
                supabase.table("employee").update({"resume_url": resume_url}).eq("user_id", auth_userID).execute()

                return {
                    "Status": "Success",
                    "Message": "Resume uploaded successfully",
                    "ResumeURL": resume_url
                }
            except Exception as storage_error:
                return {
                    "Status": "Error",
                    "Message": "Failed to upload resume to storage",
                    "Details": str(storage_error)
                }
        else:
            return {
                "Status": "Error",
                "Message": "User not found or not authorized"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": str(e)
        }

# 15/06/2025 - Michael the great
# Currently working on the three endpoinst
# for the applciation ststus, see hsitory of application, and
# view applciants
#
#
#
#
#

@app.patch("/application/{id}/status")
async def updateApplicationStatus(request : Request, application_id: str, new_status: str):
    # check first if the user authticated is an employer or not
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, service_key)
        
        check_user = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            status_to_be_changed = supabase.table("job_applications").update({
                "status": new_status
            }).eq("id", application_id).execute()
                        
            if status_to_be_changed.data:
                return {
                    "Status": "Successfull",
                    "Applicants": status_to_be_changed.data
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "Failed updating"
                }
        else:
            return {
                "Status": "Error",
                "Message": "User not Found"
            }
        
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Inetrnal Error",
            "Details": f"{e}"
        }

@app.get("/my-applications")
async def viewApplicationHistory(request: Request):
    # check first if the user authticated is an employer or not
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, key)
        
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            view_all_applciations = supabase.table("job_applications").select("*").eq("user_id", auth_userID).execute()
            
            if view_all_applciations.data:
                return{
                    "Status": "Successfull",
                    "Message": view_all_applciations.data
                }
            else:
                return{
                    "Status": "Error",
                    "Message": "No Data Found"
                }
        else:
            return {
                    "Status": "Error",
                    "Message": "User Can't be found"
                }    
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Error",
            "Details": f"{e}"
        }


@app.post("/decline-application/{application_id}")
async def declineApplication(request: Request, application_id: str):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, service_key)
        
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()

        if check_user.data and check_user.data["user_id"] == auth_userID:
            decline_application = supabase.table("declined_jobs").insert({
                "user_id": auth_userID,
                "job_id": application_id
            }).execute()
            
            if decline_application.data:
                return {
                    "Status": "Successfull",
                    "Message": "Application declined successfully"
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "Failed to decline application"
                }
        else:
            return {
                "Status": "Error",
                "Message": "User not found"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Error",
            "Details": f"{e}"
        }

@app.get("/declined-applications")
async def viewDeclinedApplications(request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        
        supabase = create_client(url, service_key)
        
        get_all_declined_applications = supabase.table("declined_jobs").select("*").eq("user_id", auth_userID).execute()
        
        if get_all_declined_applications.data:
            return {
                "Status": "Successfull",
                "Message": get_all_declined_applications.data
            }
        else:
            return {
                "Status": "Error",
                "Message": "No Data Found"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Error",
            "Details": f"{e}"
        }