from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile, Depends
from typing import List
import json
from redis_server.redis_client import redis
from models.model import updateEmployer, updateEmployee, loginCreds, inputSignupEmployer, inputSignupEmployee, jobCreation, updateJob
import ast
from datetime import datetime
import httpx
import asyncio

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
service_key = os.getenv("SUPABASE_SERVICE_KEY")


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


#Send basic notification
async def sendNotification(user_id: str, receiver_id: str, content: str, category: str):
    supabase = create_client(url, service_key)
    
    # Validate inputs
    if not user_id or not receiver_id or not content or not category:
        raise Exception(f"Missing required notification data: user_id={user_id}, receiver_id={receiver_id}, content={content}, category={category}")
    
    # Ensure all inputs are strings
    user_id = str(user_id)
    receiver_id = str(receiver_id)
    content = str(content)
    category = str(category)

    #employer notifs categories
    if category == "new_applicant":
        title = "You have a new applicant"
    elif category == "message":
        title = "You have a new message"
    
    #employee notifs categories
    if category == "message":
        title = "You have a new message"
    elif category == "job_application_accepted":
        title = "Your job application has been accepted"
    elif category == "job_application_rejected":
        title = "Your job application has been rejected"
    elif category == "job_application_sent":
        title = "Your job application is sent"
    else:
        title = "Notification"  # Default title
        
    try:
        notification_data = {
            "title": title,
            "user_id": user_id,
            "receiver_id": receiver_id,
            "content": content,
            "category": category
        }
        #
        # print(f"DEBUG - sendNotification data:")
        # print(f"  title: {title}")
        # print(f"  user_id: {user_id}")
        # print(f"  receiver_id: {receiver_id}")
        # print(f"  content: {content}")
        # print(f"  category: {category}")
        # #
        
        result = supabase.table("notifications").insert(notification_data).execute()
        
        print(f"DEBUG - insert result: {result}")
        
        if not result.data:
            raise Exception("Failed to insert notification - no data returned")
            
    except Exception as e:
        print(f"Error in sendNotification: {e}")#
        print(f"Error type: {type(e)}")#
        raise e 

#Authentication Process

# Signup and login for employee and employer
@app.post("/employee/signup") # signup for employee
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
            supabase_insert: Client = create_client(url, service_key)
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
                
                # Upload resume with correct content-type to allow inline PDF viewing
                resume_path = f"resumes/{response.user.id}/{resume.filename}"
                supabase_insert.storage.from_("resumes").upload(
                    resume_path,
                    resume_content,
                    {
                        "content-type": "application/pdf",
                        "upsert": "true",
                    },
                )
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
                supabase_insert.storage.from_("profilepic").upload(profile_pic_path, profile_pic_content)
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
                supabase_insert.storage.from_("pwdidfront").upload(pwd_id_front_path, pwd_id_front_content)
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
                supabase_insert.storage.from_("pwdidback").upload(pwd_id_back_path, pwd_id_back_content)
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

@app.post("/employee/login") # login employee
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


@app.post("/employer/signup") # signup for employer
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
         
@app.post("/employer/login") # login employer
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

#profile management
@app.get("/profile/view-profile") # view profile
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

@app.post("/profile/employer/update-profile")
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

@app.post("/profile/employee/update-profile")
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
                    supabase.storage.from_("resumes").upload(
                        resume_path,
                        resume_content,
                        {
                            "content-type": "application/pdf",
                            "upsert": "true",
                        },
                    )
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

@app.post("/jobs/create-jobs")
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

@app.get("/jobs/view-all-jobs")
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

@app.get("/jobs/view-job/{id}")
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

@app.post("/jobs/delete-job/{id}")
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
        
@app.post("/jobs/update-job/{id}")
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
        
        supabase = create_client(url, service_key)
        
        # check the user id in auth)userID is an employer
        
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            apply_job = supabase.table("employee_history").update({"applied": True}).eq("job_id", job_id).eq("user_id", auth_userID).execute()
            
            if apply_job.data:
                supabase_job_data_insertion = create_client(url, service_key)
                #get the user details
                user_details = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()
                job_data = {
                    "user_id": auth_userID,
                    "job_id": job_id,
                    "status": "under_review",
                    "applicant_details": user_details.data
                }

                # add arkha matching scoring here soon POGGGGGGGGG
                
                insert_job_appliead = supabase_job_data_insertion.table("job_applications").insert(job_data).execute()

                #send notification to the employer
                user_id = auth_userID
                category = "new_applicant"
                try:
                    job_title = supabase.table("jobs").select("title").eq("id", job_id).single().execute()
                    content = f"You have a new applicant for your job {job_title.data['title']}"
                except Exception as e:
                    return {
                        "Status": "Error",
                        "Message": "Error getting job title",
                        "Details": f"{e}"
                    }
                try:
                    receiver_id = supabase.table("jobs").select("user_id").eq("id", job_id).single().execute()
                    await sendNotification(user_id, receiver_id.data["user_id"], content, category)
                except Exception as e:
                    return {
                        "Status": "Error",
                        "Message": "Error storing notification",
                        "Details": f"{e}"
                    }
                    
                return{
                    "Status": "Successfull",
                    "Message": f"You applied to job {job_id}",
                    "Details": insert_job_appliead.data,
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
@app.get("/view-applicants/{job_id}")
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
                # Upload the resume to the supabase storage with proper metadata
                resume_path = f"resumes/{auth_userID}/{file.filename}"
                supabase.storage.from_("resumes").upload(
                    resume_path,
                    file_content,
                    {
                        "content-type": "application/pdf",
                        "upsert": "true",
                    },
                )

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
            
            #send notification to the applicant
            user_id = auth_userID
            try:
                receiver_id = supabase.table("job_applications").select("user_id").eq("id", application_id).single().execute()
                job_id = supabase.table("job_applications").select("job_id").eq("id", application_id).single().execute()
                job_title = supabase.table("jobs").select("title").eq("id", job_id.data["job_id"]).single().execute()
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Error getting details",
                    "Details": f"{e}"
                }
            
            if new_status == "accepted":
                category = "job_application_accepted"
                content = f"Your application at {job_title.data['title']} has been accepted"
            elif new_status == "rejected":
                category = "job_application_rejected"
                content = f"Your application at {job_title.data['title']} has been rejected"
            elif new_status == "under_review":
                category = "job_application_sent"
                content = f"Your application at {job_title.data['title']} is under review"
            else:
                category = "job_application_sent"
                content = f"Your application at {job_title.data['title']} is sent"
            try:
                # #
                # print(f"DEBUG - About to send notification:")
                # print(f"  user_id: {user_id}")
                # print(f"  receiver_id: {receiver_id.data['user_id'] if receiver_id.data else 'None'}")
                # print(f"  content: {content}")
                # print(f"  category: {category}")
                # #
                await sendNotification(user_id, receiver_id.data["user_id"], content, category)
            except Exception as e:
                # print(f"DEBUG - sendNotification error: {e}") #
                return {
                    "Status": "Error",
                    "Message": "Error sending notification",
                    "Details": f"{e}"
                }
            
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
            # Get all applications for this user (newest first)
            view_all_applciations = (
                supabase
                .table("job_applications")
                .select("*")
                .eq("user_id", auth_userID)
                .order("created_at", desc=True)
                .execute()
            )

            if view_all_applciations.data:
                applications = view_all_applciations.data

                # Collect distinct job_ids
                raw_ids = list({app.get("job_id") for app in applications if app.get("job_id") is not None})

                # Split numeric vs. string ids to support both integer and uuid/text schemas
                numeric_ids: list[int] = []
                string_ids: list[str] = []
                for rid in raw_ids:
                    s = str(rid)
                    if s.isdigit():
                        try:
                            numeric_ids.append(int(s))
                        except Exception:
                            string_ids.append(s)
                    else:
                        string_ids.append(s)

                # Build jobs map by id (as string)
                job_details_map: dict[str, dict] = {}
                if numeric_ids:
                    jobs_resp = supabase.table("jobs").select("*").in_("id", numeric_ids).execute()
                    for job in jobs_resp.data or []:
                        job_details_map[str(job["id"])] = job
                if string_ids:
                    jobs_resp2 = supabase.table("jobs").select("*").in_("id", string_ids).execute()
                    for job in jobs_resp2.data or []:
                        job_details_map[str(job["id"])] = job

                # Attach jobDetails, with direct-fetch fallback
                enriched = []
                for app in applications:
                    app_copy = dict(app)
                    raw_job_id = app_copy.get("job_id")
                    job_id_key = str(raw_job_id) if raw_job_id is not None else None
                    if job_id_key and job_id_key in job_details_map:
                        app_copy["jobDetails"] = job_details_map[job_id_key]
                    elif raw_job_id is not None:
                        try:
                            jid_numeric = int(str(raw_job_id))
                            single_job = supabase.table("jobs").select("*").eq("id", jid_numeric).single().execute()
                        except Exception:
                            single_job = supabase.table("jobs").select("*").eq("id", str(raw_job_id)).single().execute()
                        if getattr(single_job, 'data', None):
                            app_copy["jobDetails"] = single_job.data
                    enriched.append(app_copy)

                return{
                    "Status": "Successfull",
                    "Message": enriched
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

@app.get("/get-declined-applications")
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
    





# ======== Websocket for real time chat ========

# websocket manager
#track active  connections on redis (Upstash)
from typing import Dict
from models.model import ChatMessage


active_connections: Dict[str, WebSocket] = {}


# async def connect_user(websocket: WebSocket, user_id: str):
#     try:
#         await websocket.accept()
#         active_connections[user_id] = websocket
#         # fetch any offline messages amd send them
#         await send_offline_messages(user_id)
#     except Exception as e:
#         return {
#             "Status": "Error",
#             "Message": f"Failed to connect to user {user_id}",
#             "Details": f"{e}"
#         }

# async def disconnect_user(websocket: WebSocket, user_id: str):
#     try:
#         if user_id in active_connections:
#             await active_connections[user_id].close()
#             del active_connections[user_id]
#     except Exception as e:
#         return {
#             "Status": "Error",
#             "Message": f"Failed to disconnect user {user_id}",
#             "Details": f"{e}"
#         }

# async def get_active_connections(user_id: str) -> WebSocket | None:
#     return active_connections.get(user_id)

# async def send_message(message: ChatMessage):
#     try:
#         # store message in supabase
#         supabase = create_client(url, service_key)
#         response = supabase.table("messages").insert({
#             "sender_id": message.sender_id,
#             "receiver_id": message.receiver_id,
#             "type": message.type,
#             "message": message.message,
#             "job_id": message.job_id,
#             "created_at": datetime.utcnow().isoformat()
#         }).execute()

#         if not response.data:
#             return {
#                 "Status": "Error",
#                 "Message": "Failed to send message"
#             }
        
#         #prepare payload for websocket
#         message_paylaod = {
#             "type": "chat_message",
#             "data": {
#                 **message.model_dump(),
#                 "id": response.data[0]["id"]
#             }
#         }

#         # if the reciver is online, send message DIRECTLY
#         reciever_websocket = await get_active_connections(message.receiver_id)
#         if reciever_websocket:
#             try:
#                 await reciever_websocket.send_text(json.dumps(message_paylaod))
#             except Exception as e:
#                 return {
#                     # if the sending fails, message is already in supabase db for offline retrieval
#                     "Status": "Error",
#                     "Message": "User is Offline, However Message is stored in the database"
#                 }
        
#         return{
#             "Status": "Success",
#             "Message": "Message is sent and Stored in the database",
#             "data": response.data[0]
#         }
#     except Exception as e:
#         return {
#             "Status": "Error",
#             "Message": f"Failed to send message: {str(e)}"
#         }
# async def send_offline_messages(user_id: str):
#     # fetch and send messages that were recived while the user was offline
#     try:
#         supabase = create_client(url, service_key)
#         response = supabase.table("messages").select("*").eq("receiver_id", user_id).eq("is_read", False).order("created_at").execute()

#         if response.data:
#             websocket = await get_active_connections(user_id)
#             if websocket:
#                 for message in response.data:
#                     message_payload = {
#                         "type": "chat_message",
#                         "data": message
#                     }
#                     await websocket.send_text(json.dumps(message_payload))

#                     #mark messages read
#                     message_ids = [message["id"] for message in response.data]
#                     supabase.table("messages").update({
#                         "is_read": True
#                     }).in_("id", message_ids).execute()

#             return {
#                 "Status": "Success",
#                 "Message": "Offline messages sent"
#             }
#     except Exception as e:
#         return {
#             "Status": "Error",
#             "Message": "Failed to send offline messages",
#             "Details": f"{e}"
#         }

# # websocket endpoint
# async def get_user_id_from_token(token: str) -> str:
#     """Validate token and get user_id from Upstash Redis"""
#     try:
#         if not token:
#             raise WebSocketDisconnect(reason="Missing token")
        
#         # Get session data from Upstash Redis
#         value = await redis.get(token)
#         if not value:
#             raise WebSocketDisconnect(reason="Invalid or expired token")
        
#         try:
#             session_data = json.loads(value)
#             auth_user_id = session_data.get("auth_userID")
#             if not auth_user_id:
#                 raise WebSocketDisconnect(reason="Invalid session data")
#             return auth_user_id
#         except json.JSONDecodeError:
#             raise WebSocketDisconnect(reason="Corrupted session data")
            
#     except Exception as e:
#         if isinstance(e, WebSocketDisconnect):
#             raise e
#         raise WebSocketDisconnect(reason=f"Authentication error: {str(e)}")

# @app.websocket("/ws/chat/{user_id}")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     user_id: str,
#     token: str = None
# ):
#     print(f"WebSocket connection attempt for user_id: {user_id}")  # Debug log
#     try:
#         # Validate token and get authenticated user ID
#         if not token:
#             print("No token provided")  # Debug log
#             await websocket.close(code=4001, reason="Missing authentication token")
#             return
            
#         print("Validating token...")  # Debug log
#         try:
#             auth_user_id = await get_user_id_from_token(token)
#             print(f"Token validated for user: {auth_user_id}")  # Debug log
#         except WebSocketDisconnect as e:
#             print(f"WebSocket disconnect during auth: {str(e)}")  # Debug log
#             await websocket.close(code=4002, reason=str(e))
#             return
#         except Exception as e:
#             print(f"Authentication error: {str(e)}")  # Debug log
#             await websocket.close(code=4500, reason="Internal authentication error")
#             return
        
#         # Verify the user_id matches the token
#         if auth_user_id != user_id:
#             print(f"User ID mismatch: {auth_user_id} != {user_id}")  # Debug log
#             await websocket.close(code=4003, reason="User ID mismatch")
#             return
        
#         print("Accepting connection...")  # Debug log
#         # Store WebSocket connection
#         await connect_user(websocket, user_id)
#         print("Connection accepted and stored")  # Debug log
        
#         while True:
#             try:
#                 data = await websocket.receive_text()
#                 print(f"Received message from {user_id}: {data[:100]}...")  # Debug log (first 100 chars)
#                 message_data = json.loads(data)
                
#                 # Create ChatMessage instance with validation
#                 chat_message = ChatMessage(**message_data)
                
#                 # Verify sender_id matches authenticated user
#                 if chat_message.sender_id != auth_user_id:
#                     # print(f"Sender ID mismatch: {chat_message.sender_id} != {auth_user_id}")  # Debug log
#                     await websocket.send_json({
#                         "Status": "Error",
#                         "Message": "Unauthorized: sender_id does not match authenticated user"
#                     })
#                     continue
                
#                 # Handle incoming messages
#                 result = await send_message(chat_message)
#                 # print(f"Message processed with result: {result}")  # Debug log
                
#                 # Send acknowledgment back to client
#                 await websocket.send_json(result)
                
#             except json.JSONDecodeError:
#                 # print("Invalid JSON received")  # Debug log
#                 await websocket.send_json({
#                     "Status": "Error",
#                     "Message": "Invalid message format"
#                 })
#             except Exception as e:
#                 # print(f"Error processing message: {str(e)}")  # Debug log
#                 await websocket.send_json({
#                     "Status": "Error",
#                     "Message": f"Message processing error: {str(e)}"
#                 })
                
#     except WebSocketDisconnect:
#         # print(f"WebSocket disconnected for user: {user_id}")  # Debug log
#         await disconnect_user(websocket, user_id)
#     except Exception as e:
#         print(f"WebSocket error: {str(e)}")
#         await disconnect_user(websocket, user_id)
#     finally:
#         # Ensure connection is removed from active_connections
#         if user_id in active_connections:
#             del active_connections[user_id]
#         # print(f"Cleaned up connection for user: {user_id}")  # Debug log

#get the chat history
@app.get("/messages/{sender_id}/{receiver_id}")
async def get_chat_history(sender_id: str, reciever_id: str, job_id: str = None):
    try:
        supabase = create_client(url, service_key)
        query = supabase.table("messages").select("*").eq("sender_id", sender_id).eq("receiver_id", reciever_id)
        
        # Filter by job_id if provided
        if job_id:
            query = query.eq("job_id", job_id)
            
        response = query.order("created_at").execute()

        if response.data:
            return {
                "Status": "Success",
                "Message": "Chat history fetched successfully",
                "data": response.data
            }
        else:
            return {
                "Status": "Error",
                "Message": "No chat history found",
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to fetch chat history",
            "Details": f"{e}"
        }

# ======== Push Notification Functions ========

async def get_user_push_token(user_id: str) -> str:
    """Get the active push token for a user from the database"""
    try:
        supabase = create_client(url, service_key)
        response = supabase.table("push_tokens").select("expo_token").eq("user_id", user_id).eq("active", True).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["expo_token"]
        return None
    except Exception as e:
        print(f"❌ Error getting push token for user {user_id}: {str(e)}")
        return None

async def send_push_notification(expo_token: str, title: str, body: str, data: dict = None):
    """Send push notification via Expo Push API"""
    try:
        notification_payload = {
            "to": expo_token,
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high"
        }
        
        if data:
            notification_payload["data"] = data
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=notification_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Push notification sent successfully: {result}")
                return result
            else:
                print(f"❌ Failed to send push notification: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error sending push notification: {str(e)}")
        return None

def get_notification_content(message_type: str):
    """Get appropriate notification title and body based on message type"""
    if message_type == "google_meet_link":
        return {
            "title": "🎥 Interview Scheduled!",
            "body": "You have a new interview scheduled. Tap to join the meeting."
        }
    elif message_type == "form_link":
        return {
            "title": "📝 Test Assigned!",
            "body": "A new technical test has been assigned to you."
        }
    elif message_type == "status_update":
        return {
            "title": "📋 Status Update",
            "body": "There's an update on your application status."
        }
    else:  # text or default
        return {
            "title": "💬 New Message",
            "body": "You have received a new message from an employer."
        }

@app.post("/message/send-message") # send message to a user
async def send_message(payload: ChatMessage, request: Request):
    # check if the user is authenticated
    auth_userID = await getAuthUserIdFromRequest(redis, request)
    if auth_userID != payload.sender_id:
        return {
            "Status": "Error",
            "Message": "Unauthorized: sender_id does not match authenticated user"
        }
    
    supabase = create_client(url, service_key)
    
    # Insert message into database
    response = supabase.table("messages").insert({
        "sender_id": payload.sender_id,
        "receiver_id": payload.receiver_id,
        "message": payload.message,
        "job_id": payload.job_id,
        "type": payload.type
    }).execute()
    

    #store notification
    user_id = auth_userID
    category = "message"
    # Initialize variables
    sender_name_in_employee = None
    sender_name_in_employer = None
    
    # Try to find sender in employee table first
    try:
        sender_name_in_employee = supabase.table("employee").select("full_name").eq("user_id", payload.sender_id).single().execute()
    except Exception as e:
        # If no rows found or other error, continue to check employer table
        print(f"DEBUG - Employee table check failed: {e}")
        sender_name_in_employee = None
    
    # If not found in employee table, try employer table
    if not sender_name_in_employee or not sender_name_in_employee.data:
        try:
            sender_name_in_employer = supabase.table("employers").select("company_name").eq("user_id", payload.sender_id).single().execute()
        except Exception as e:
            # If no rows found or other error in employer table too
            print(f"DEBUG - Employer table check failed: {e}")
            sender_name_in_employer = None
    
    # Determine sender name based on results
    if sender_name_in_employee and sender_name_in_employee.data:
        sender_name = sender_name_in_employee.data["full_name"]
    elif sender_name_in_employer and sender_name_in_employer.data:
        sender_name = sender_name_in_employer.data["company_name"]
    else:
        # Only raise error if BOTH tables failed to find the user
        return{
            "Status": "Error",
            "Message": "Error getting sender name",
            "Details": f"Sender with user_id {payload.sender_id} not found in either employee or employer tables"
        }

    try:
        content = f"You have a new message from {sender_name}"
        await sendNotification(user_id, payload.receiver_id, content, category)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Error storing notification",
            "Details": f"{e}"
        }
            
    
    if response.data:
        inserted_message = response.data[0]
        
        # Send push notification to receiver (async, don't wait for it)
        async def send_notification():
            try:
                # Get receiver's push token
                push_token = await get_user_push_token(payload.receiver_id)
                
                if push_token:
                    # Get appropriate notification content based on message type
                    notification_content = get_notification_content(payload.type)
                    
                    # Send push notification
                    await send_push_notification(
                        expo_token=push_token,
                        title=notification_content["title"],
                        body=notification_content["body"],
                        data={
                            "type": "message",
                            "messageId": inserted_message["id"],
                            "senderId": payload.sender_id,
                            "messageType": payload.type,
                            "jobId": payload.job_id
                        }
                    )
                    print(f"🔔 Push notification sent to user {payload.receiver_id}")
                else:
                    print(f"⚠️ No push token found for user {payload.receiver_id}")
                    
            except Exception as e:
                print(f"❌ Error sending push notification: {str(e)}")
        
        # Start notification task in background (don't block the response)
        asyncio.create_task(send_notification())
        
        return {
            "Status": "Success",
            "Message": "Message sent successfully",
            "data": inserted_message
        }
    else:
        return {
            "Status": "Error",
            "Message": "Failed to send message"
        }

@app.post("/test-push-notification/{user_id}")
async def test_push_notification(user_id: str):
    """Test endpoint to send a push notification to a specific user"""
    try:
        # Get user's push token
        push_token = await get_user_push_token(user_id)
        
        if not push_token:
            return {
                "Status": "Error",
                "Message": f"No active push token found for user {user_id}"
            }
        
        # Send test notification
        result = await send_push_notification(
            expo_token=push_token,
            title="🧪 Test Notification",
            body="This is a test push notification from your backend server!",
            data={
                "type": "test",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if result:
            return {
                "Status": "Success",
                "Message": "Test push notification sent successfully",
                "data": result
            }
        else:
            return {
                "Status": "Error",
                "Message": "Failed to send test push notification"
            }
            
    except Exception as e:
        return {
            "Status": "Error",
            "Message": f"Error sending test notification: {str(e)}"
        }

# marking messages as read
@app.patch("/message/mark-as-read/{message_id}")
async def mark_message_as_read(message_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    # Verify the message exists and belongs to the authenticated user
    check_message = supabase.table("messages").select("*").eq("id", message_id).eq("receiver_id", auth_userID).execute()

    if not check_message.data:
        return {
            "Status": "Error",
            "Message": "Message not found"
        }
    
    # Update the message to mark it as read
    response = supabase.table("messages").update({"is_read": True}).eq("id", message_id).execute()

    if response.data:
        return {
            "Status": "Success",
            "Message": "Message marked as read"
        }
    else:
        return {
            "Status": "Error",
            "Message": "Failed to mark message as read"
        }

#marking all mesages who is not read READ!
@app.patch("/message/mark-all-as-read/{user_id}")
async def mark_all_messages_as_read(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    # Verify the user exists
    check_user = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not check_user.data:
        return {
            "Status": "Error",
            "Message": "User not found"
        }
    
    # Update all messages for the user to mark them as read
    response = supabase.table("messages").update({"is_read": True}).eq("receiver_id", user_id).execute()
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "All messages marked as read"
        }
    else:
        return {
            "Status": "Error",
            "Message": "Failed to mark all messages as read"
        }

#get all unread messages
@app.get("/message/get-unread-messages/{user_id}")
async def get_unread_messages(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    # Verify the user exists
    check_user = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not check_user.data:
        return {
            "Status": "Error",
            "Message": "User not found"
        }
    
    # Get all unread messages for the user
    response = supabase.table("messages").select("*").eq("receiver_id", user_id).eq("is_read", False).execute()
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "Unread messages fetched successfully",
            "data": response.data
        }
    else:
        return {
            "Status": "Error",
            "Message": "No unread messages found"
        }

#get all messages
@app.get("/message/get-all-messages/{user_id}")
async def get_all_messages(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    # Verify the user exists
    check_user = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not check_user.data:
        return {
            "Status": "Error",
            "Message": "User not found"
        }
    
    # Get all messages for the user
    response = supabase.table("messages").select("*").eq("receiver_id", user_id).execute()
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "All messages fetched successfully",
            "data": response.data
        }
    else:
        return {
            "Status": "Error",
            "Message": "No messages found"
        }