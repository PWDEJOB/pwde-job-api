from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile, Depends
from typing import List
import json
from redis_server.redis_client import redis
from models.model import updateEmployer, updateEmployee, loginCreds, inputSignupEmployer, inputSignupEmployee, jobCreation, updateJob, PasswordReset, PasswordResetConfirm
import ast
from datetime import datetime
import httpx
import asyncio
import re

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
from groq import Groq
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
    except Exception as e:
        return {
            "Status": "Error",
            "isAuthenticated": False,
            "Message": "Internal Server Error",
            "Details": str(e)
        }
    

    try:
        # Check both employee and employer tables
        employee_check = supabase.table("employee").select("*").eq("user_id", auth_userID).execute()
        employer_check = supabase.table("employers").select("*").eq("user_id", auth_userID).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "isAuthenticated": False,
            "Message": "User not found",
            "Details": str(e)
        }
    

    try:
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
            "Message": f"Internal Server Error",
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

#Push notification
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

def get_job_status_notification_content(status: str, job_title: str):
    """Get appropriate notification title and body based on job application status"""
    if status == "accepted":
        return {
            "title": "🎉 Application Accepted!",
            "body": f"Congratulations! Your application for {job_title} has been accepted."
        }
    elif status == "rejected":
        return {
            "title": "📋 Application Update",
            "body": f"Your application for {job_title} has been rejected."
        }
    elif status == "under_review":
        return {
            "title": "👀 Application Under Review",
            "body": f"Your application for {job_title} is now under review."
        }
    elif status == "pending_requirements":
        return {
            "title": "📄 Requirements Pending",
            "body": f"Additional requirements needed for your {job_title} application."
        }
    else:
        return {
            "title": "📋 Application Status Update",
            "body": f"There's an update on your application for {job_title}."
        }
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
            "Message":f"Signing Up Failed: {e}",
        }
    
        # Validate response and user creation
    if not response or not response.user or not response.user.id:
        return {
            "Status": "Error",
            "Message": "User creation failed - no user ID returned"
        }
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
            try:
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
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Resume upload failed. Please try again.",
                    "Details": f"{e}"
                }

        if profile_pic:
            # Validate file type (images only)
            allowed_image_types = ['.jpg', '.jpeg', '.png']
            file_ext = os.path.splitext(profile_pic.filename)[1].lower()
            if file_ext not in allowed_image_types:
                return {
                    "Status": "Error",
                    "Message": "Profile picture must be an image file (JPG, JPEG, or PNG)"
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
            try:
                supabase_insert.storage.from_("profilepic").upload(profile_pic_path, profile_pic_content)
                profile_pic_url = supabase.storage.from_("profilepic").get_public_url(profile_pic_path)
                user_data["profile_pic_url"] = profile_pic_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Profile picture upload failed. Please try again.",
                    "Details": f"{e}"
                }


        if pwd_id_front:
            # Validate file type (images only)
            file_ext = os.path.splitext(pwd_id_front.filename)[1].lower()
            if file_ext not in allowed_image_types:
                return {
                    "Status": "Error",
                    "Message": "PWD ID front must be an image file (JPG, JPEG, or PNG)"
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
            try:
                supabase_insert.storage.from_("pwdidfront").upload(pwd_id_front_path, pwd_id_front_content)
                pwd_id_front_url = supabase.storage.from_("pwdidfront").get_public_url(pwd_id_front_path)
                user_data["pwd_id_front_url"] = pwd_id_front_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "PWD ID front upload failed. Please try again.",
                    "Details": f"{e}"
                }

        if pwd_id_back:
            # Validate file type (images only)
            file_ext = os.path.splitext(pwd_id_back.filename)[1].lower()
            if file_ext not in allowed_image_types:
                return {
                    "Status": "Error",
                    "Message": "PWD ID back must be an image file (JPG, JPEG, or PNG)"
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
            try:
                supabase_insert.storage.from_("pwdidback").upload(pwd_id_back_path, pwd_id_back_content)
                pwd_id_back_url = supabase.storage.from_("pwdidback").get_public_url(pwd_id_back_path)
                user_data["pwd_id_back_url"] = pwd_id_back_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "PWD ID back upload failed. Please try again.",
                    "Details": f"{e}"
                }

        
        try:
            # Insert all data into the database
            insert_data = supabase_insert.table("employee").insert(user_data).execute()
            return {
                "Status": "Successfull",
                "Message": f"{full_name} has been successfully signed up",
                "Details": insert_data.data
            }
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Data insertion failed",
                "Details": f"{e}"
            }
    except Exception as e:
        return{
            "Status":"ERROR",
            "Message:":"Internal error. Data insertion failed",
            "Details": f"{e}"
        }

@app.post("/employee/login") # login employee
async def employee_login(user: loginCreds):
    # validate input
    if not user.email or not user.password:
        return {
            "Status": "Error",
            "Message": "Email and password are required"
        }
    
    try:
        supabase: Client = create_client(url, key)
        response = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password
            }
        )
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Login failed. Please check your credentials.",
        }
    
    if not response:
        return {
            "Status": "Error",
            "Message": "Authentication failed - no response received"
        }
    
    if not response.user or not response.user.id:
        return {
            "Status": "Error",
            "Message": "Authentication failed - invalid user data"
        }
    
    if not response.session:
        return {
            "Status": "Error",
            "Message": "Authentication failed - no session created"
        }
    
    # extract session data safely
    session_key = response.session
    access_token = session_key.access_token
    refresh_token = session_key.refresh_token
    auth_userID = response.user.id
    
    # validate session tokens
    if not access_token or not refresh_token:
        return {
            "Status": "Error",
            "Message": "Authentication failed - invalid session tokens"
        }
    
    # check if user exists in employee table
    try:
        employee_check = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to verify user account",
        }
    
    # validate employee exists
    if not employee_check.data:
        return {
            "Status": "Error",
            "Message": "Account not found. Please contact support."
        }
    
    # store session in Redis
    session_data = {
        "auth_userID": auth_userID,
        "refresh_token": refresh_token
    }
    
    try:
        await redis.set(access_token, json.dumps(session_data), ex=None)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Login successful but session storage failed. Please try again.",
        }
    
    # return success response
    return {
        "Status": "Success",
        "Message": "Login successful",
        "Token": access_token,
        "User_ID": auth_userID
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
    
    # validate required file
    if not file or not file.filename:
        return {
            "Status": "Error",
            "Message": "Company logo is required"
        }
    
    # sign up the user
    try:
        supabase = create_client(url, key)
        response = supabase.auth.sign_up(
            {
                "email": email, 
                "password": password,
            }
        )
    except Exception as e:
        return {
            "Status": "Error",
            "Message": f"Signing Up Failed: {e}",
        }
    
    # validate response and user creation
    if not response or not response.user or not response.user.id:
        return {
            "Status": "Error",
            "Message": "User creation failed - no user ID returned"
        }
    
    # process file upload and user data
    try:
        # Validate and read file
        allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            return {
                "Status": "Error",
                "Message": "Invalid file type. Allowed types: JPG, JPEG, PNG, GIF"
            }
        
        # Read file content safely
        try:
            file_content = await file.read()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to read uploaded file",
                "Details": f"{e}"
            }
        
        # Validate file size
        if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
            return {
                "Status": "Error",
                "Message": "File size exceeds 5MB limit"
            }
        
        # Upload logo to Supabase storage
        logo_path = f"logos/{response.user.id}/{file.filename}"
        try:
            supabase.storage.from_("companylogo").upload(logo_path, file_content)
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Logo upload failed. Please try again.",
                "Details": f"{e}"
            }
        
        # Get the public URL for the uploaded logo
        try:
            logo_url = supabase.storage.from_("companylogo").get_public_url(logo_path)
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to generate logo URL. Please try again.",
                "Details": f"{e}"
            }
        
        # Prepare user data
        supabase_insert = create_client(url, key)
        user_data = {
            "user_id": response.user.id,
            "email": email,
            "company_name": company_name,
            "company_level": company_level,
            "website_url": website_url,
            "company_type": company_type,
            "industry": industry,
            "admin_name": admin_name,
            "logo_url": logo_url,
            "description": description,
            "location": location,
            "tags": tags,
            "role": role,
        }
        
        # Insert data into database
        try:
            insert_data = supabase_insert.table("employers").insert(user_data).execute()
            
            if insert_data.data:
                return {
                    "Status": "Success",
                    "Message": f"{company_name} has been successfully signed up",
                    "Details": insert_data.data
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "Signup failed - no data returned from database",
                }
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Database insertion failed. Please try again.",
                "Details": f"{e}"
            }
            
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal error. Data processing failed",
            "Details": f"{e}"
        }
         
@app.post("/employer/login") # login employer
async def employer_login(user: loginCreds):
    # validate input
    if not user.email or not user.password:
        return {
            "Status": "Error",
            "Message": "Email and password are required"
        }
    
    # attempt authentication
    try:
        supabase: Client = create_client(url, key)
        response = supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": user.password
            }
        )
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Login failed. Please check your credentials.",
        }
    
    # validate authentication response
    if not response:
        return {
            "Status": "Error",
            "Message": "Authentication failed - no response received"
        }
    
    if not response.user or not response.user.id:
        return {
            "Status": "Error",
            "Message": "Authentication failed - invalid user data"
        }
    
    if not response.session:
        return {
            "Status": "Error",
            "Message": "Authentication failed - no session created"
        }
    
    # extract session data safely
    session_key = response.session
    access_token = session_key.access_token
    refresh_token = session_key.refresh_token
    auth_userID = response.user.id
    
    # Validate session tokens
    if not access_token or not refresh_token:
        return {
            "Status": "Error",
            "Message": "Authentication failed - invalid session tokens"
        }
    
    # check if user exists in employers table
    try:
        employer_check = supabase.table("employers").select("*").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to verify employer account",
        }
    
    # validate employer exists
    if not employer_check.data:
        return {
            "Status": "Error",
            "Message": "Account not found or not registered as an employer"
        }
    
    # store session in Redis
    session_data = {
        "auth_userID": auth_userID,
        "refresh_token": refresh_token
    }
    
    try:
        await redis.set(access_token, json.dumps(session_data), ex=None)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Login successful but session storage failed. Please try again.",
        }
    
    # return success response
    return {
        "Status": "Success",
        "Message": "Login successful",
        "Token": access_token,
        "User_ID": auth_userID
    }
#profile management
@app.get("/profile/view-profile") # view profile
async def viewProfile(request: Request):
    # authentication
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        if not auth_userID:
            return {
                "Status": "Error",
                "Message": "Invalid user ID"
            }
        supabase = create_client(url, key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Authentication failed",
            "Details": f"{e}"
        }
    
    # check employer table first
    try:
        response_employer = supabase.table("employers").select("*").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        # Continue to check employee table - this might just mean user is not an employer
        response_employer = None
    
    if response_employer and response_employer.data:
        return {
            "Status": "Success",
            "Message": "Employer profile retrieved successfully",
            "Profile": response_employer.data,
            "UserType": "employer"
        }
    
    # check employee table
    try:
        response_employee = supabase.table("employee").select("*").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to retrieve profile data",
            "Details": f"{e}"
        }
    
    if response_employee and response_employee.data:
        return {
            "Status": "Success",
            "Message": "Employee profile retrieved successfully",
            "Profile": response_employee.data,
            "UserType": "employee"
        }
    
    # not found in either table
    return {
        "Status": "Error",
        "Message": "User profile not found. Please contact support."
    }

# Profile Update
#this will update only name, skills, and disability 

@app.post("/profile/employer/update-profile")
async def updateEmployerProfile(
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
    
    # authentication
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        if not auth_userID:
            return {
                "Status": "Error",
                "Message": "Invalid user ID"
            }
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Authentication failed",
            "Details": f"{e}"
        }
    
    # verify user is an employer
    try:
        search_employer = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to verify employer account",
            "Details": f"{e}"
        }
    
    if not search_employer.data:
        return {
            "Status": "Error",
            "Message": "Account not found in employers table"
        }
    
    # build update data
    updated_details = {}

    # Add text fields if provided
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

    # handle logo upload if provided
    if logo and logo.filename:
        # Validate file type
        allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = os.path.splitext(logo.filename)[1].lower()
        if file_ext not in allowed_types:
            return {
                "Status": "Error",
                "Message": "Invalid logo file type. Allowed: JPG, JPEG, PNG, GIF"
            }
        
        # Read and validate file content
        try:
            logo_content = await logo.read()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to read logo file",
                "Details": f"{e}"
            }
        
        if len(logo_content) == 0:
            # Empty file, skip logo update
            pass
        elif len(logo_content) > 5 * 1024 * 1024:
            return {
                "Status": "Error",
                "Message": "Logo file size must be less than 5MB"
            }
        else:
            # Upload logo
            logo_path = f"logos/{auth_userID}/{logo.filename}"
            try:
                supabase.storage.from_("companylogo").upload(logo_path, logo_content, {"upsert": "true"})
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Logo upload failed. Please try again.",
                    "Details": f"{e}"
                }
            
            # Get logo URL
            try:
                logo_url = supabase.storage.from_("companylogo").get_public_url(logo_path)
                updated_details["logo_url"] = logo_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Logo URL retrieval failed. Please try again.",
                    "Details": f"{e}"
                }

    # check if any updates were provided
    if not updated_details:
        return {
            "Status": "Error",
            "Message": "No valid fields provided for update"
        }

    # update database
    try:
        update_employer_res = supabase.table("employers").update(updated_details).eq("user_id", auth_userID).execute()
        
        if update_employer_res.data:
            return {
                "Status": "Success",
                "Message": "Profile updated successfully",
                "Data": update_employer_res.data
            }
        else:
            return {
                "Status": "Error",
                "Message": "Update failed - no data returned"
            }
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e):
            return {
                "Status": "Error",
                "Message": "A unique field value you are trying to update already exists for another employer",
                "Details": str(e)
            }
        return {
            "Status": "Error",
            "Message": "Database update failed",
            "Details": f"{e}"
        }
@app.post("/profile/employee/update-profile")
async def updateEmployeeProfile(
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
    
    # authentication
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        if not auth_userID:
            return {
                "Status": "Error",
                "Message": "Invalid user ID"
            }
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Authentication failed",
            "Details": f"{e}"
        }
    
    # verify user is an employee
    try:
        search_employee = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to verify employee account",
            "Details": f"{e}"
        }
    
    if not search_employee.data:
        return {
            "Status": "Error",
            "Message": "Account not found in employees table"
        }
    
    # build update data
    updated_details = {}

    # Add text fields if provided
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

    # handle resume upload if provided
    if resume and resume.filename:
        # Validate file type
        if not resume.filename.lower().endswith('.pdf'):
            return {
                "Status": "Error",
                "Message": "Resume must be a PDF file"
            }
        
        # Read and validate file content
        try:
            resume_content = await resume.read()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to read resume file",
                "Details": f"{e}"
            }
        
        if len(resume_content) == 0:
            # Empty file, skip resume update
            pass
        elif len(resume_content) > 5 * 1024 * 1024:
            return {
                "Status": "Error",
                "Message": "Resume file size must be less than 5MB"
            }
        else:
            # Upload resume
            resume_path = f"resumes/{auth_userID}/{resume.filename}"
            try:
                supabase.storage.from_("resumes").upload(
                    resume_path,
                    resume_content,
                    {
                        "content-type": "application/pdf",
                        "upsert": "true",
                    },
                )
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Resume upload failed. Please try again.",
                    "Details": f"{e}"
                }
            
            # Get resume URL
            try:
                resume_url = supabase.storage.from_("resumes").get_public_url(resume_path)
                updated_details["resume_url"] = resume_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Resume URL retrieval failed. Please try again.",
                    "Details": f"{e}"
                }

    # handle profile picture upload if provided
    if profile_pic and profile_pic.filename:
        # Validate file type
        allowed_image_types = ['.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(profile_pic.filename)[1].lower()
        if file_ext not in allowed_image_types:
            return {
                "Status": "Error",
                "Message": "Profile picture must be an image file (JPG, JPEG, or PNG)"
            }
        
        # Read and validate file content
        try:
            profile_pic_content = await profile_pic.read()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to read profile picture file",
                "Details": f"{e}"
            }
        
        if len(profile_pic_content) == 0:
            # Empty file, skip profile picture update
            pass
        elif len(profile_pic_content) > 5 * 1024 * 1024:
            return {
                "Status": "Error",
                "Message": "Profile picture file size must be less than 5MB"
            }
        else:
            # Upload profile picture
            profile_pic_path = f"profilepic/{auth_userID}/{profile_pic.filename}"
            try:
                supabase.storage.from_("profilepic").upload(profile_pic_path, profile_pic_content, {"upsert": "true"})
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Profile picture upload failed. Please try again.",
                    "Details": f"{e}"
                }
            
            # Get profile picture URL
            try:
                profile_pic_url = supabase.storage.from_("profilepic").get_public_url(profile_pic_path)
                updated_details["profile_pic_url"] = profile_pic_url
            except Exception as e:
                return {
                    "Status": "Error",
                    "Message": "Profile picture URL retrieval failed. Please try again.",
                    "Details": f"{e}"
                }

    # check if any updates were provided
    if not updated_details:
        return {
            "Status": "Error",
            "Message": "No valid fields provided for update"
        }

    # update database
    try:
        update_employee_res = supabase.table("employee").update(updated_details).eq("user_id", auth_userID).execute()
        
        if update_employee_res.data:
            return {
                "Status": "Success",
                "Message": "Profile updated successfully",
                "Data": update_employee_res.data
            }
        else:
            return {
                "Status": "Error",
                "Message": "Update failed - no data returned"
            }
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e):
            return {
                "Status": "Error",
                "Message": "A unique field value you are trying to update already exists for another employee",
                "Details": str(e)
            }
        return {
            "Status": "Error",
            "Message": "Database update failed",
            "Details": f"{e}"
        }
#job shii

#create jobs
# This endpoint is for empployers to be able create jobs, view al jobs listings they created, view a specific job listinsg details, delete, and update

@app.post("/jobs/create-jobs")
async def createJob(job: jobCreation, request: Request):
    #check if the user is authenticated
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        #check first if the user exist as an employer
        supabase: Client = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error"
        }
    
    #check if the user exist as an employer
    try:
        search_id = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "User not found in employers table"
        }
    
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
        try:
            insert_response = supabase.table("jobs").insert(jobs_data).execute()
            return{
                "Status": "Sucessfull",
                "Message": "Job has been created",
                "Details": f"{insert_response}"
            }
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Job Creation Failed. Please try again.",
                "Details": str(e)
            }
    else:
        return {
            "Status": "Error",
            "Message": "Maybe the employer dosen't exist"
        }

@app.get("/jobs/view-all-jobs")
async def viewAllJobs(request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error"
        }
    try: 
        all_jobs = supabase.table("jobs").select("*").eq("user_id", auth_userID).execute()
        
        if all_jobs:
            return {"jobs": all_jobs.data}
        else:
            return {
                "Status": "Error",
                "Message": "No Jobs Found"
            }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Failed to retrieve jobs from database"
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

        # First check if the user is an employer and authorized to delete this job
        search_id = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
        
        if not search_id.data or search_id.data["user_id"] != auth_userID:
            return {
                "Status": "Error",
                "Message": "Employer not found or not authorized."
            }

        # Check if the job exists before deletion
        job_check = supabase.table("jobs").select("id").eq("id", id).single().execute()
        if not job_check.data:
            return {
                "Status": "Error",
                "Message": f"No job found with id {id} to delete."
            }

        # Delete employee history related to the job
        try:
            deleting_employee_history = supabase.table("employee_history").delete().eq("job_id", id).execute()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Error deleting employee history",
                "Details": f"{e}"
            }

        # Delete job applications related to the job
        try:
            deleting_job_applications = supabase.table("job_applications").delete().eq("job_id", id).execute()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Error deleting job applications",
                "Details": f"{e}"
            }

        # Delete messages related to the job
        try:
            deleting_messages_between_employer_and_applicant = supabase.table("messages").delete().eq("job_id", id).execute()
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Error deleting messages between employer and applicant",
                "Details": f"{e}"
            }

        # Finally delete the job itself
        try:
            delete_job = supabase.table("jobs").delete().eq("id", id).execute()
            
            if delete_job.data:  # check if any row was actually deleted
                return {
                    "Status": "Success",
                    "Message": f"Job {id} and all related data deleted successfully"
                }
            else:
                return {
                    "Status": "Error",
                    "Message": f"Failed to delete job {id}",
                    "Details": f"{delete_job}"
                }
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Error deleting job",
                "Details": f"{e}"
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

                try:
                    #get the job data for insert in "job application analysis data"
                    get_job_data = supabase.table("jobs").select("*").eq("id", job_id).single().execute()

                    #get all job appliead skills
                    skill_1 = get_job_data.data["skill_1"]
                    skill_2 = get_job_data.data["skill_2"]
                    skill_3 = get_job_data.data["skill_3"]
                    skill_4 = get_job_data.data["skill_4"]
                    skill_5 = get_job_data.data["skill_5"]

                    #get salary 
                    min_salary = get_job_data.data["min_salary"]
                    max_salary = get_job_data.data["max_salary"]

                    #get the job type
                    job_type = get_job_data.data["job_type"]
                    userid_of_employer = get_job_data.data["user_id"]

                    #calculate what month the user applied for th job
                    month = datetime.now().month

                    #calculate what year the user applied for the job
                    year = datetime.now().year
                    
                    # structure the data for insert in "job application analysis data"
                    job_application_analysis_data = {
                        "skill_1": skill_1,
                        "skill_2": skill_2,
                        "skill_3": skill_3,
                        "skill_4": skill_4,
                        "skill_5": skill_5,
                        "min_salary": min_salary,
                        "max_salary": max_salary,
                        "job_type": job_type,
                        "userid_of_employer": userid_of_employer,
                        "month": month,
                        "year": year
                    }
                

                    #insert the data in "job application analysis data"
                    insert_job_application_analysis_data = supabase.table("job_application_analysis_data").insert(job_application_analysis_data).execute()

                    if insert_job_application_analysis_data.data:
                        return {
                            "Status": "Success",
                            "Message": "Job application analysis data inserted successfully"
                        }
                except Exception as e:
                    return {
                        "Status": "Error",
                        "Message": "Error inserting job application analysis data",
                        "Details": f"{e}"
                    }
                    
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

# ======== Password Reset Endpoints ========

@app.post("/auth/request-password-reset")
async def request_password_reset(reset_request: PasswordReset):
    """
    Send a password reset email to the user.
    This uses Supabase's built-in password reset functionality.
    """
    try:
        # Validate email input
        if not reset_request.email or not reset_request.email.strip():
            return {
                "Status": "Error",
                "Message": "Email is required"
            }
        
        email = reset_request.email.strip().lower()
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return {
                "Status": "Error",
                "Message": "Please enter a valid email address"
            }
        
        # Initialize Supabase client with error handling
        try:
            supabase: Client = create_client(url, service_key)
        except Exception as client_error:
            print(f"❌ Failed to initialize Supabase client: {str(client_error)}")
            return {
                "Status": "Error",
                "Message": "Service temporarily unavailable. Please try again later."
            }
        
        # Use Supabase's built-in password reset functionality with OTP
        try:
            response = supabase.auth.reset_password_for_email(email)
            # Note: No redirect_to needed for OTP flow, Supabase will send a 6-digit code
            
            # Log successful request (without exposing sensitive data)
            print(f"✅ Password reset requested for email: {email[:3]}***@{email.split('@')[1] if '@' in email else 'unknown'}")
            
        except Exception as supabase_error:
            error_message = str(supabase_error).lower()
            
            # Handle specific Supabase errors
            if "rate limit" in error_message or "too many requests" in error_message:
                return {
                    "Status": "Error",
                    "Message": "Too many password reset requests. Please wait a few minutes before trying again."
                }
            elif "invalid email" in error_message or "email not found" in error_message:
                # Still return generic message for security (prevent email enumeration)
                pass
            elif "network" in error_message or "connection" in error_message:
                return {
                    "Status": "Error",
                    "Message": "Network error. Please check your connection and try again."
                }
            else:
                print(f"❌ Supabase password reset error: {str(supabase_error)}")
        
        # Always return success message for security reasons (to prevent email enumeration)
        return {
            "Status": "Success",
            "Message": "If an account with this email exists, a 6-digit reset code has been sent to your email address. Please check your inbox and spam folder."
        }
        
    except Exception as e:
        print(f"❌ Unexpected error in password reset request: {str(e)}")
        return {
            "Status": "Error",
            "Message": "An unexpected error occurred. Please try again later.",
            "Details": "Internal server error" if not str(e) else None
        }

@app.post("/auth/confirm-password-reset")
async def confirm_password_reset(reset_confirm: PasswordResetConfirm):
    """
    Confirm password reset using the token from email and set new password.
    """
    try:
        # Comprehensive input validation
        if not reset_confirm.email or not reset_confirm.email.strip():
            return {
                "Status": "Error",
                "Message": "Email is required"
            }
        
        if not reset_confirm.token or not reset_confirm.token.strip():
            return {
                "Status": "Error",
                "Message": "6-digit reset code is required"
            }
        
        # Validate OTP format (6 digits)
        otp_code = reset_confirm.token.strip()
        if not re.match(r'^\d{6}$', otp_code):
            return {
                "Status": "Error",
                "Message": "Reset code must be exactly 6 digits"
            }
        
        if not reset_confirm.new_password:
            return {
                "Status": "Error",
                "Message": "New password is required"
            }
        
        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, reset_confirm.email.strip().lower()):
            return {
                "Status": "Error",
                "Message": "Please enter a valid email address"
            }
        
        # Enhanced password strength validation
        new_password = reset_confirm.new_password
        if len(new_password) < 6:
            return {
                "Status": "Error",
                "Message": "Password must be at least 6 characters long"
            }
        
        if len(new_password) > 128:
            return {
                "Status": "Error",
                "Message": "Password is too long (maximum 128 characters)"
            }
        
        # Check for at least one letter and one number for better security
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            return {
                "Status": "Error",
                "Message": "Password must contain at least one letter and one number"
            }
        
        # Initialize Supabase client with error handling
        try:
            supabase: Client = create_client(url, service_key)
        except Exception as client_error:
            print(f"❌ Failed to initialize Supabase client: {str(client_error)}")
            return {
                "Status": "Error",
                "Message": "Service temporarily unavailable. Please try again later."
            }
        
        # Verify the reset token and update password
        try:
            # Use Supabase auth to verify OTP code and update password
            response = supabase.auth.verify_otp(
                {
                    "email": reset_confirm.email.strip().lower(),
                    "token": otp_code,  # Use the validated 6-digit code
                    "type": "recovery"
                }
            )
            
            if not response or not response.user:
                return {
                    "Status": "Error",
                    "Message": "Invalid or expired reset code. Please request a new password reset."
                }
            
            # Update the user's password
            try:
                update_response = supabase.auth.update_user(
                    {
                        "password": new_password
                    }
                )
                
                if not update_response or not update_response.user:
                    print(f"❌ Failed to update password for user: {response.user.id}")
                    return {
                        "Status": "Error",
                        "Message": "Failed to update password. Please try again or contact support."
                    }
                
                # Log successful password reset (without sensitive data)
                print(f"✅ Password successfully reset for user: {response.user.id}")
                
                return {
                    "Status": "Success",
                    "Message": "Password has been reset successfully. You can now login with your new password."
                }
                
            except Exception as update_error:
                error_message = str(update_error).lower()
                
                if "weak password" in error_message or "password" in error_message and "requirements" in error_message:
                    return {
                        "Status": "Error",
                        "Message": "Password does not meet security requirements. Please choose a stronger password."
                    }
                elif "rate limit" in error_message:
                    return {
                        "Status": "Error",
                        "Message": "Too many attempts. Please wait a few minutes before trying again."
                    }
                else:
                    print(f"❌ Password update error: {str(update_error)}")
                    return {
                        "Status": "Error",
                        "Message": "Failed to update password. Please try again."
                    }
                
        except Exception as auth_error:
            error_message = str(auth_error).lower()
            
            # Handle specific authentication errors
            if "invalid" in error_message and ("token" in error_message or "otp" in error_message):
                return {
                    "Status": "Error",
                    "Message": "Invalid reset code. Please request a new password reset."
                }
            elif "expired" in error_message:
                return {
                    "Status": "Error",
                    "Message": "Reset code has expired. Please request a new password reset."
                }
            elif "rate limit" in error_message or "too many" in error_message:
                return {
                    "Status": "Error",
                    "Message": "Too many attempts. Please wait a few minutes before trying again."
                }
            elif "network" in error_message or "connection" in error_message:
                return {
                    "Status": "Error",
                    "Message": "Network error. Please check your connection and try again."
                }
            else:
                print(f"❌ Auth verification error: {str(auth_error)}")
                return {
                    "Status": "Error",
                    "Message": "Authentication failed. Please request a new password reset."
                }
        
    except Exception as e:
        print(f"❌ Unexpected error in password reset confirmation: {str(e)}")
        return {
            "Status": "Error",
            "Message": "An unexpected error occurred. Please try again later.",
            "Details": "Internal server error" if not str(e) else None
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

#uplaod other required documents
@app.post("/upload-sss")
async def uploadSSS(request: Request, file: UploadFile = File(...)):
    try:
        # Debug logging
        # print(f"🔍 SSS Upload Debug - Filename: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return {
                "Status": "Error",
                "Message": "Only JPG, JPEG, PNG files are allowed"
            }

        # Read file content
        file_content = await file.read()
        
        # Validate file size (e.g., 5MB limit)
        if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
            return {
                "Status": "Error",
                "Message": "File size exceeds 5MB limit"
            }
        
        # Determine content type based on file extension
        filename_lower = file.filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif filename_lower.endswith('.png'):
            content_type = "image/png"
        else:
            content_type = "image/jpeg"  # default fallback
        
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        # print(f"🔍 Auth User ID: {auth_userID}")
        
        supabase = create_client(url, service_key)
        
        # Check if documents bucket exists
        # try:
        #     buckets = supabase.storage.list_buckets()
        #     print(f"🔍 Available buckets: {[bucket.name for bucket in buckets]}")
        #     documents_bucket_exists = any(bucket.name == "documents" for bucket in buckets)
        #     print(f"🔍 Documents bucket exists: {documents_bucket_exists}")
        # except Exception as bucket_error:
        #     print(f"⚠️ Error checking buckets: {str(bucket_error)}")
        
        # Check if the user is an employee
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        # print(f"🔍 User check result: {check_user.data}")
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            try:
                # Upload the document to the supabase storage with proper metadata
                document_path = f"documents/sss/{auth_userID}/{file.filename}"
                # print(f"🔍 Attempting upload to path: {document_path}")
                # print(f"🔍 File size: {len(file_content)} bytes")
                # print(f"🔍 Content type: {content_type}")
                
                # Try upload with upsert first, if it fails try without upsert
                try:
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                            "upsert": True,  # Use boolean instead of string
                        },
                    )
                except Exception as upsert_error:
                    # print(f"⚠️ Upload with upsert failed, trying without upsert: {str(upsert_error)}")
                    # Try removing existing file first, then upload
                    try:
                        supabase.storage.from_("documents").remove([document_path])
                    except:
                        pass  # File might not exist, that's fine
                    
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                        },
                    )
                # print(f"🔍 Upload result: {upload_result}")

                # Update the employee's profile with the document URL
                document_url = supabase.storage.from_("documents").get_public_url(document_path)
                # print(f"🔍 Generated URL: {document_url}")
                
                update_result = supabase.table("employee").update({"sss_url": document_url}).eq("user_id", auth_userID).execute()
                # print(f"🔍 Database update result: {update_result}")

                return {
                    "Status": "Success",
                    "Message": "Document uploaded successfully",
                    "DocumentURL": document_url
                }
            except Exception as storage_error:
                # print(f"💥 Storage error: {str(storage_error)}")
                # print(f"💥 Storage error type: {type(storage_error)}")
                return {
                    "Status": "Error",
                    "Message": "Failed to upload document to storage",
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

@app.get("/test-storage")
async def testStorage():
    """Test endpoint to check Supabase storage connectivity"""
    try:
        supabase = create_client(url, service_key)
        
        # List available buckets
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        # Check if documents bucket exists
        documents_exists = "documents" in bucket_names
        
        # If documents bucket doesn't exist, try to create it
        if not documents_exists:
            try:
                create_result = supabase.storage.create_bucket("documents", {"public": True})
                print(f"🔧 Created documents bucket: {create_result}")
                documents_exists = True
            except Exception as create_error:
                print(f"⚠️ Failed to create documents bucket: {str(create_error)}")
        
        return {
            "Status": "Success",
            "Message": "Storage connectivity test completed",
            "Data": {
                "buckets": bucket_names,
                "documents_bucket_exists": documents_exists,
                "service_key_configured": bool(service_key),
                "url_configured": bool(url)
            }
        }
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Storage test failed",
            "Details": str(e)
        }

@app.post("/upload-philhealth")
async def uploadPhilhealth(request: Request, file: UploadFile = File(...)):
    try:
        # Debug logging
        # print(f"🔍 PhilHealth Upload Debug - Filename: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return {
                "Status": "Error",
                "Message": "Only JPG, JPEG, PNG files are allowed"
            }

        # Read file content
        file_content = await file.read()
        
        # Validate file size (e.g., 5MB limit)
        if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
            return {
                "Status": "Error",
                "Message": "File size exceeds 5MB limit"
            }
        
        # Determine content type based on file extension
        filename_lower = file.filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif filename_lower.endswith('.png'):
            content_type = "image/png"
        else:
            content_type = "image/jpeg"  # default fallback
        
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        # print(f"🔍 Auth User ID: {auth_userID}")
        
        supabase = create_client(url, service_key)
        
        # Check if documents bucket exists
        # try:
        #     buckets = supabase.storage.list_buckets()
        #     print(f"🔍 Available buckets: {[bucket.name for bucket in buckets]}")
        #     documents_bucket_exists = any(bucket.name == "documents" for bucket in buckets)
        #     print(f"🔍 Documents bucket exists: {documents_bucket_exists}")
        # except Exception as bucket_error:
        #     print(f"⚠️ Error checking buckets: {str(bucket_error)}")
        
        # Check if the user is an employee
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        # print(f"🔍 User check result: {check_user.data}")
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            try:
                # Upload the document to the supabase storage with proper metadata
                document_path = f"documents/philhealth/{auth_userID}/{file.filename}"
                # print(f"🔍 Attempting upload to path: {document_path}")
                # print(f"🔍 File size: {len(file_content)} bytes")
                # print(f"🔍 Content type: {content_type}")
                
                # Try upload with upsert first, if it fails try without upsert
                try:
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                            "upsert": True,  # Use boolean instead of string
                        },
                    )
                except Exception as upsert_error:
                    # print(f"⚠️ Upload with upsert failed, trying without upsert: {str(upsert_error)}")
                    # Try removing existing file first, then upload
                    try:
                        supabase.storage.from_("documents").remove([document_path])
                    except:
                        pass  # File might not exist, that's fine
                    
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                        },
                    )
                # print(f"🔍 Upload result: {upload_result}")

                # Update the employee's profile with the document URL
                document_url = supabase.storage.from_("documents").get_public_url(document_path)
                # print(f"🔍 Generated URL: {document_url}")
                
                update_result = supabase.table("employee").update({"philhealth_url": document_url}).eq("user_id", auth_userID).execute()
                # print(f"🔍 Database update result: {update_result}")

                return {
                    "Status": "Success",
                    "Message": "Document uploaded successfully",
                    "DocumentURL": document_url
                }
            except Exception as storage_error:
                # print(f"💥 Storage error: {str(storage_error)}")
                # print(f"💥 Storage error type: {type(storage_error)}")
                return {
                    "Status": "Error",
                    "Message": "Failed to upload document to storage",
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

@app.post("/upload-pagibig")
async def uploadPagibig(request: Request, file: UploadFile = File(...)):
    try:
        # Debug logging
        # print(f"🔍 Pag-IBIG Upload Debug - Filename: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return {
                "Status": "Error",
                "Message": "Only JPG, JPEG, PNG files are allowed"
            }

        # Read file content
        file_content = await file.read()
        
        # Validate file size (e.g., 5MB limit)
        if len(file_content) > 5 * 1024 * 1024:  # 5MB in bytes
            return {
                "Status": "Error",
                "Message": "File size exceeds 5MB limit"
            }
        
        # Determine content type based on file extension
        filename_lower = file.filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif filename_lower.endswith('.png'):
            content_type = "image/png"
        else:
            content_type = "image/jpeg"  # default fallback
        
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        # print(f"🔍 Auth User ID: {auth_userID}")
        
        supabase = create_client(url, service_key)
        
        # Check if documents bucket exists
        # try:
        #     buckets = supabase.storage.list_buckets()
        #     print(f"🔍 Available buckets: {[bucket.name for bucket in buckets]}")
        #     documents_bucket_exists = any(bucket.name == "documents" for bucket in buckets)
        #     print(f"🔍 Documents bucket exists: {documents_bucket_exists}")
        # except Exception as bucket_error:
        #     print(f"⚠️ Error checking buckets: {str(bucket_error)}")
        
        # Check if the user is an employee
        check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
        # print(f"🔍 User check result: {check_user.data}")
        
        if check_user.data and check_user.data["user_id"] == auth_userID:
            try:
                # Upload the document to the supabase storage with proper metadata
                document_path = f"documents/pagibig/{auth_userID}/{file.filename}"
                # print(f"🔍 Attempting upload to path: {document_path}")
                # print(f"🔍 File size: {len(file_content)} bytes")
                # print(f"🔍 Content type: {content_type}")
                
                # Try upload with upsert first, if it fails try without upsert
                try:
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                            "upsert": True,  # Use boolean instead of string
                        },
                    )
                except Exception as upsert_error:
                    # print(f"⚠️ Upload with upsert failed, trying without upsert: {str(upsert_error)}")
                    # Try removing existing file first, then upload
                    try:
                        supabase.storage.from_("documents").remove([document_path])
                    except:
                        pass  # File might not exist, that's fine
                    
                    upload_result = supabase.storage.from_("documents").upload(
                        document_path,
                        file_content,
                        {
                            "content-type": content_type,
                        },
                    )
                # print(f"🔍 Upload result: {upload_result}")

                # Update the employee's profile with the document URL
                document_url = supabase.storage.from_("documents").get_public_url(document_path)
                # print(f"🔍 Generated URL: {document_url}")
                
                update_result = supabase.table("employee").update({"pagibig_url": document_url}).eq("user_id", auth_userID).execute()
                # print(f"🔍 Database update result: {update_result}")

                return {
                    "Status": "Success",
                    "Message": "Document uploaded successfully",
                    "DocumentURL": document_url
                }
            except Exception as storage_error:
                # print(f"💥 Storage error: {str(storage_error)}")
                # print(f"💥 Storage error type: {type(storage_error)}")
                return {
                    "Status": "Error",
                    "Message": "Failed to upload document to storage",
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

@app.get("/get-documents")
async def getDocuments(request: Request, user_id: str = None):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
        
        # If user_id is provided, check if requester is an employer
        if user_id:
            check_employer = supabase.table("employers").select("user_id").eq("user_id", auth_userID).single().execute()
            if check_employer.data and check_employer.data["user_id"] == auth_userID:
                # Employer can view documents for specified user
                target_user_id = user_id
            else:
                return {
                    "Status": "Error",
                    "Message": "Access denied. Only employers can view other users' documents."
                }
        else:
            # No user_id provided, check if requester is an employee viewing their own documents
            check_user = supabase.table("employee").select("user_id").eq("user_id", auth_userID).single().execute()
            if check_user.data and check_user.data["user_id"] == auth_userID:
                target_user_id = auth_userID
            else:
                return {
                    "Status": "Error",
                    "Message": "User not found or not authorized"
                }
        
        # Fetch documents for the target user
        documents = supabase.table("employee").select("sss_url, philhealth_url, pagibig_url").eq("user_id", target_user_id).single().execute()
        
        if documents.data:
            return {
                "Status": "Success",
                "Message": "Documents fetched successfully",
                "Documents": documents.data
            }
        else:
            return {
                "Status": "Success",
                "Message": "No documents found for this user",
                "Documents": {
                    "sss_url": None,
                    "philhealth_url": None,
                    "pagibig_url": None
                }
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
            elif new_status == "pending_requirements":
                category = "job_application_pending_requirements"
                content = f"Your application at {job_title.data['title']} is pending requirements"
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
                
                # Send push notification to the applicant (async, don't wait for it)
                async def send_status_push_notification():
                    try:
                        # Get applicant's push token
                        applicant_user_id = receiver_id.data["user_id"]
                        push_token = await get_user_push_token(applicant_user_id)
                        
                        if push_token:
                            # Get appropriate notification content based on status
                            notification_content = get_job_status_notification_content(new_status, job_title.data['title'])
                            
                            # Send push notification
                            await send_push_notification(
                                expo_token=push_token,
                                title=notification_content["title"],
                                body=notification_content["body"],
                                data={
                                    "type": "job_application_status",
                                    "status": new_status,
                                    "job_title": job_title.data['title'],
                                    "application_id": application_id,
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            print(f"✅ Push notification sent for job status change: {new_status}")
                        else:
                            print(f"⚠️ No push token found for user {applicant_user_id}")
                            
                    except Exception as e:
                        print(f"❌ Error sending push notification for job status: {str(e)}")
                
                # Start push notification task in background (don't block the response)
                asyncio.create_task(send_status_push_notification())
                
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
        # print(f"DEBUG - Employee table check failed: {e}")
        sender_name_in_employee = None
    
    # If not found in employee table, try employer table
    if not sender_name_in_employee or not sender_name_in_employee.data:
        try:
            sender_name_in_employer = supabase.table("employers").select("company_name").eq("user_id", payload.sender_id).single().execute()
        except Exception as e:
            # If no rows found or other error in employer table too
            # print(f"DEBUG - Employer table check failed: {e}")
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

@app.post("/register-push-token")
async def register_push_token(request: Request):
    """Register/update a user's push notification token"""
    try:
        # Get user ID from token
        user_id = await getAuthUserIdFromRequest(redis, request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        
        # Parse request body
        body = await request.json()
        expo_token = body.get('expo_token')
        
        if not expo_token:
            return {
                "Status": "Error",
                "Message": "expo_token is required"
            }
        
        # Create Supabase client
        supabase = create_client(url, service_key)
        
        # First, deactivate any existing tokens for this user
        supabase.table("push_tokens").update({
            "active": False
        }).eq("user_id", user_id).execute()
        
        # Insert or update the new token
        result = supabase.table("push_tokens").upsert({
            "user_id": user_id,
            "expo_token": expo_token,
            "active": True,
            "created_at": datetime.now().isoformat()
        }, on_conflict="expo_token").execute()
        
        if result.data:
            print(f"✅ Push token registered for user {user_id}: {expo_token[:20]}...")
            return {
                "Status": "Success",
                "Message": "Push token registered successfully",
                "data": {
                    "user_id": user_id,
                    "token_registered": True
                }
            }
        else:
            return {
                "Status": "Error",
                "Message": "Failed to register push token"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error registering push token: {str(e)}")
        return {
            "Status": "Error",
            "Message": f"Error registering push token: {str(e)}"
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

#===Notfication endpoints===

#get all notifications
@app.get("/notification/get-all-notifications/{user_id}")
async def get_all_notifications(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Get all notifications for the user
        response = supabase.table("notifications").select("*").eq("receiver_id", user_id).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "All notifications fetched successfully",
            "data": response.data
        }
    else:
        return {
            "Status": "Error",
            "Message": "No notifications found"
        }

#mark the notification as read
@app.patch("/notification/mark-as-read/{notification_id}")
async def mark_notification_as_read(notification_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Mark the notification as read
        response = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Marking notification as read failed",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "Notification marked as read"
        }
    else:
        return {
            "Message": "Notification not found"
        }

#mark all notifications as read
@app.patch("/notification/mark-all-as-read/{user_id}")
async def mark_all_notifications_as_read(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Mark all notifications as read
        response = supabase.table("notifications").update({"is_read": True}).eq("receiver_id", user_id).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Marking all notifications as read failed",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "All notifications marked as read"
        }
    else:
        return {
            "Status": "Error",
            "Message": "No notifications found"
        }

#get unread notifications
@app.get("/notification/get-unread-notifications/{user_id}")
async def get_unread_notifications(user_id: str, request: Request):
    try:
        auth_userID = await getAuthUserIdFromRequest(redis, request)
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Get unread notifications
        response = supabase.table("notifications").select("*").eq("receiver_id", user_id).eq("is_read", False).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "Unread notifications fetched successfully",
            "data": response.data
        }
    else:
        return {
            "Status": "Success",
            "Message": "No unread notifications found",
            "data": []
        }

@app.post("/notification/delete-notification/{notification_id}")
async def delete_notification(notification_id: str, request: Request):
    try:
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Delete the notification
        response = supabase.table("notifications").delete().eq("id", notification_id).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Deleting notification failed",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "Notification deleted successfully"
        }
    else:
        return {
            "Status": "Error",
            "Message": "Notification not found"
        }

@app.get("/job-application-analysis/{user_id}")
async def get_job_application_analysis(user_id: str, request: Request):
    try:
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    try:
        # Get job application analysis data
        response = supabase.table("job_application_analysis_data").select("*").eq("userid_of_employer", user_id).execute()
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Internal Server Error",
            "Details": f"{e}"
        }
    
    if response.data:
        return {
            "Status": "Success",
            "Message": "Job application analysis data fetched successfully",
            "data": response.data
        }
    else:
        return {
            "Status": "Error",
            "Message": "No job application analysis data found"
        }


# verification of the pwd id image
@app.post("/verify-pwd-id/{user_id}")
async def verify_pwd_id(user_id: str):
    # Input validation
    if not user_id or not user_id.strip():
        return {
            "Status": "Error",
            "Message": "User ID is required"
        }
    
    try:
        supabase = create_client(url, service_key)
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "Database connection failed",
            "Details": f"{e}"
        }
    
    try:
        # Fetch user data
        response = supabase.table("employee").select("*").eq("user_id", user_id).execute()

        if not response.data:
            return {
                "Status": "Error", 
                "Message": "User not found"
            }

        user_data = response.data[0]
        pwde_id_front = user_data.get("pwd_id_front_url")
        
        if not pwde_id_front:
            return {
                "Status": "Error",
                "Message": "PWD ID image not found for this user"
            }

        try:
            # Initialize Groq client
            client = Groq()

            # Call Groq API for image analysis
            groq_response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a PWD ID verification system. Analyze this PWD (Person with Disability) identification card image and extract ONLY the PWD ID number and the person's name.\n\nIMPORTANT: You must respond in EXACTLY this format with nothing else:\nPWD ID Number: [number], Name: [full name]\n\nIf you cannot find both the PWD ID number and name clearly in the image, respond with EXACTLY:\nNo number or name found in the image.\n\nDo not include any explanations, descriptions, or additional text. Only the required format."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"{pwde_id_front}"
                                }
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Image analysis failed",
                "Details": f"Groq API error: {e}"
            }

        # Check if Groq response is valid
        if not groq_response or not groq_response.choices or not groq_response.choices[0].message.content:
            return {
                "Status": "Error",
                "Message": "Invalid response from image analysis service"
            }

        analysis_result = groq_response.choices[0].message.content.strip()

        # Always return the full Groq response for debugging
        debug_info = {
            "full_groq_response": analysis_result,
            "expected_format": "PWD ID Number: [number], Name: [full name]"
        }

        if analysis_result == "No number or name found in the image.":
            return {
                "Status": "Error",
                "Message": "No PWD ID number or name found in the image",
                "Details": debug_info
            }
        
        # Parse the response safely
        try:
            if "," not in analysis_result or ":" not in analysis_result:
                return {
                    "Status": "Error",
                    "Message": "Invalid format in image analysis response",
                    "Details": {
                        **debug_info,
                        "error": "Expected comma and colon separators not found"
                    }
                }
            
            parsed_response = analysis_result.split(",")
            if len(parsed_response) < 2:
                return {
                    "Status": "Error",
                    "Message": "Incomplete data extracted from image",
                    "Details": {
                        **debug_info,
                        "error": "Could not parse both PWD ID and name - missing comma separator"
                    }
                }
            
            # Extract PWD ID number
            pwd_id_part = parsed_response[0].strip()
            if ":" not in pwd_id_part:
                return {
                    "Status": "Error",
                    "Message": "PWD ID number format invalid",
                    "Details": {
                        **debug_info,
                        "error": f"Expected 'PWD ID Number: ...' but got: '{pwd_id_part}'"
                    }
                }
            pwd_id_number = pwd_id_part.split(":", 1)[1].strip()
            
            # Extract name
            name_part = parsed_response[1].strip()
            if ":" not in name_part:
                return {
                    "Status": "Error",
                    "Message": "Name format invalid",
                    "Details": {
                        **debug_info,
                        "error": f"Expected 'Name: ...' but got: '{name_part}'"
                    }
                }
            name = name_part.split(":", 1)[1].strip()
            
            if not pwd_id_number or not name:
                return {
                    "Status": "Error",
                    "Message": "Empty PWD ID number or name extracted from image",
                    "Details": {
                        **debug_info,
                        "extracted_pwd_id": pwd_id_number,
                        "extracted_name": name
                    }
                }
                
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Failed to parse image analysis results",
                "Details": {
                    **debug_info,
                    "parsing_error": str(e)
                }
            }

        # Verify against pwd_people table
        try:
            verification_response = supabase.table("pwd_people").select("*").eq("pwd_number", pwd_id_number).eq("id_owner_name", name).execute()
            
            if verification_response.data:

                #update the employee "is_verified" to true
                supabase.table("employee").update({"is_verified": True}).eq("user_id", user_id).execute()

                return {
                    "Status": "Success",
                    "Message": "PWD ID verification successful",
                    "Details": {
                        "extracted_pwd_id": pwd_id_number,
                        "extracted_name": name,
                        "verification_data": verification_response.data[0]
                    }
                }
            else:
                return {
                    "Status": "Error",
                    "Message": "PWD ID verification failed - no matching record found",
                    "Details": f"No record found for PWD ID: {pwd_id_number}, Name: {name}"
                }
                
        except Exception as e:
            return {
                "Status": "Error",
                "Message": "Database verification failed",
                "Details": f"Error checking pwd_people table: {e}"
            }
            
    except Exception as e:
        return {
            "Status": "Error",
            "Message": "PWD ID verification process failed",
            "Details": f"Unexpected error: {e}"
        }