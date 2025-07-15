# PWDE-JOB API Documentation (Complete)

## Table of Contents
1. [General Endpoints](#general-endpoints)
2. [Employee Endpoints](#employee-endpoints)
3. [Employer Endpoints](#employer-endpoints)
4. [Job Management Endpoints](#job-management-endpoints)
5. [Application Management Endpoints](#application-management-endpoints)
6. [Real-time Chat Communication](#real-time-chat-communication)
7. [Error Handling](#error-handling)
8. [Frontend Implementation Tips](#frontend-implementation-tips)

---

## General Endpoints

### Authentication

#### Employee Signup
- **Endpoint**: `POST /employee/signup`
- **Description**: Register a new employee account. Supports all profile fields and file uploads in a single step. Uses `multipart/form-data`.
- **Request (multipart/form-data)**:
  - `full_name` (string, required)
  - `email` (string, required)
  - `password` (string, required)
  - `address` (string, optional)
  - `phone_number` (string, optional)
  - `short_bio` (string, optional)
  - `disability` (string, optional)
  - `skills` (string, optional, comma-separated or JSON array)
  - `resume` (file, optional, PDF only, max 5MB)
  - `profile_pic` (file, optional, JPG/JPEG/PNG/GIF, max 5MB)
  - `pwd_id_front` (file, optional, image)
  - `pwd_id_back` (file, optional, image)

- **Sample Request (curl)**:
```bash
curl -X POST "http://your-api-url/employee/signup" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "full_name=Richard Gomex" \
  -F "email=rarara12@gmail.com" \
  -F "password=12345678" \
  -F "address=Quezon City" \
  -F "phone_number=09123456789" \
  -F "short_bio=asfdassfasfassf" \
  -F "disability=Pilay" \
  -F "skills=AWS,Figma,SEO,Python,Java" \
  -F "resume=@/path/to/resume.pdf" \
  -F "profile_pic=@/path/to/profile.jpg" \
  -F "pwd_id_front=@/path/to/pwd-front.jpg" \
  -F "pwd_id_back=@/path/to/pwd-back.jpg"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": "Richard Gomex has been successfully signed up",
  "Details": [
    {
      "id": 24,
      "user_id": "932ffa37-61d3-41a4-b621-94d9d834e032",
      "full_name": "Richard Gomex",
      "disability": "Pilay",
      "skills": "AWS,Figma,SEO,Python,Java",
      "created_at": "2025-06-13T15:53:47.207587+00:00",
      "role": "employee",
      "resume_url": "https://.../resume_sample.pdf?",
      "profile_pic_url": "https://.../77.jpg?",
      "address": "Quezon City",
      "phone_number": "09123456789",
      "short_bio": "asfdassfasfassf",
      "pwd_id_front_url": "https://.../pwdidfront/...",
      "pwd_id_back_url": "https://.../pwdidback/...",
      "email": "rarara12@gmail.com"
    }
  ]
}
```

- **Tips for React Native (Employee Frontend):**
  - Use `FormData` to build the request.
  - Use `expo-image-picker` for images and `expo-document-picker` for PDFs.
  - Example:
    ```javascript
    const formData = new FormData();
    formData.append('full_name', 'Richard Gomex');
    // ...other fields
    formData.append('resume', { uri: resume.uri, type: 'application/pdf', name: resume.name });
    formData.append('profile_pic', { uri: profilePic.uri, type: 'image/jpeg', name: 'profile.jpg' });
    await fetch('http://your-api-url/employee/signup', { method: 'POST', body: formData });
    ```
  - Always check file size and type before upload.
  - Omit fields you don't want to set.

---

#### Employer Signup
- **Endpoint**: `POST /employer/signup`
- **Description**: Register a new employer account. Supports company logo upload. Uses `multipart/form-data`.
- **Request (multipart/form-data)**:
  - `email` (string, required)
  - `password` (string, required)
  - `company_name` (string, required)
  - `company_level` (string, required)
  - `website_url` (string, required)
  - `company_type` (string, required)
  - `industry` (string, required)
  - `admin_name` (string, required)
  - `description` (string, required)
  - `location` (string, required)
  - `tags` (string, required)
  - `file` (file, required, JPG/JPEG/PNG/GIF, max 5MB)

- **Sample Request (curl)**:
```bash
curl -X POST "http://your-api-url/employer/signup" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "email=test12@gmail.com" \
  -F "password=your_secure_password" \
  -F "company_name=BlaBla Inc." \
  -F "company_level=Medium" \
  -F "website_url=blbla.com" \
  -F "company_type=LLC" \
  -F "industry=Technology" \
  -F "admin_name=John Stuart" \
  -F "description=agsdfhgashjkfghjas" \
  -F "location=London" \
  -F "tags=hiring" \
  -F "file=@/path/to/your/logo.jpg"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": "BlaBla Inc. has been successfully signed up",
  "Details": "data=[{...employer fields..., 'logo_url': 'https://.../companylogo/...'}] count=None"
}
```

- **Tips for Web Frontend (Employer):**
  - Use a standard HTML `<form>` with `enctype="multipart/form-data"` or use `FormData` in JavaScript.
  - Example with Axios:
    ```javascript
    const formData = new FormData();
    formData.append('email', 'test12@gmail.com');
    // ...other fields
    formData.append('file', logoFile);
    await axios.post('http://your-api-url/employer/signup', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    ```
  - Validate file type and size before upload.
  - Omit fields you don't want to set.

---

#### Employee Login
- **Endpoint**: `POST /employee/login`
- **Description**: Authenticate an employee and create a session. Returns an access token for subsequent requests.
- **Request (JSON)**:
  ```json
  {
    "email": "test12@gmail.com",
    "password": "your_secure_password"
  }
  ```

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/employee/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test12@gmail.com",
      "password": "your_secure_password"
    }'
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Success",
    "Message": "Login successful. Session stored in Redis.",
    "App User ID": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
    "Debug Session Key": "session:f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
    "Stored User ID": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7"
  }
  ```

- **Error Response**:
  ```json
  {
    "Status": "Error",
    "Message": "Invalid credentials"
  }
  ```

- **React Native Implementation**:
  ```javascript
  const loginEmployee = async (email, password) => {
    try {
      const response = await fetch('http://your-api-url/employee/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      });
      
      const data = await response.json();
      
      if (data.Status === 'Success') {
        // Store the session key for future requests
        await AsyncStorage.setItem('sessionKey', data['Debug Session Key']);
        await AsyncStorage.setItem('userId', data['App User ID']);
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };
  ```

---

#### Employer Login
- **Endpoint**: `POST /employer/login`
- **Description**: Authenticate an employer and create a session. Returns an access token for subsequent requests.
- **Request (JSON)**:
  ```json
  {
    "email": "rarara12@gmail.com",
    "password": "your_secure_password"
  }
  ```

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/employer/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "rarara12@gmail.com",
      "password": "your_secure_password"
    }'
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Success",
    "Message": "Login successful. Session stored in Redis.",
    "App User ID": "148cc1c6-2e81-4037-913c-7617564baa33",
    "Debug Session Key": "session:148cc1c6-2e81-4037-913c-7617564baa33",
    "Stored User ID": "148cc1c6-2e81-4037-913c-7617564baa33"
  }
  ```

- **Web Implementation (JavaScript)**:
  ```javascript
  const loginEmployer = async (email, password) => {
    try {
      const response = await fetch('http://your-api-url/employer/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      });
      
      const data = await response.json();
      
      if (data.Status === 'Success') {
        // Store the session key for future requests
        localStorage.setItem('sessionKey', data['Debug Session Key']);
        localStorage.setItem('userId', data['App User ID']);
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };
  ```

---

#### Logout
- **Endpoint**: `POST /logout`
- **Description**: Logout user and invalidate session token.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/logout" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Success",
    "Message": "Successfully logged out"
  }
  ```

- **Implementation Example**:
  ```javascript
  const logout = async () => {
    try {
      const token = localStorage.getItem('sessionKey'); // or AsyncStorage for React Native
      
      const response = await fetch('http://your-api-url/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Success') {
        // Clear stored session data
        localStorage.removeItem('sessionKey');
        localStorage.removeItem('userId');
        return data;
      }
    } catch (error) {
      console.error('Logout error:', error);
    }
  };
  ```

---

### Profile Management

#### View Profile
- **Endpoint**: `GET /profile/view-profile`
- **Description**: Get the current user's profile information. Works for both employees and employers.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/profile/view-profile" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response (Employee)**:
  ```json
  {
    "Profile": {
      "id": 24,
      "user_id": "932ffa37-61d3-41a4-b621-94d9d834e032",
      "full_name": "Richard Gomez",
      "email": "rarara12@gmail.com",
      "role": "employee",
      "disability": "Pilay",
      "skills": "AWS,Figma,SEO,Python,Java",
      "address": "Quezon City",
      "phone_number": "09123456789",
      "short_bio": "Experienced developer with PWD",
      "resume_url": "https://.../resume_sample.pdf",
      "profile_pic_url": "https://.../profile.jpg",
      "pwd_id_front_url": "https://.../pwd_front.jpg",
      "pwd_id_back_url": "https://.../pwd_back.jpg",
      "created_at": "2025-06-13T15:53:47.207587+00:00"
    }
  }
  ```

- **Sample Response (Employer)**:
  ```json
  {
    "Profile": {
      "id": 3,
      "user_id": "148cc1c6-2e81-4037-913c-7617564baa33",
      "email": "rarara12@gmail.com",
      "role": "employer",
      "company_name": "BlaBla Inc.",
      "company_level": "Medium",
      "website_url": "blbla.com",
      "company_type": "LLC",
      "industry": "Technology",
      "admin_name": "John Stuart",
      "description": "Leading tech company",
      "location": "London",
      "tags": "hiring",
      "logo_url": "https://.../logo.jpg",
      "created_at": "2025-06-03T08:16:25.221844+00:00"
    }
  }
  ```

- **Implementation Example**:
  ```javascript
  const viewProfile = async () => {
    try {
      const token = localStorage.getItem('sessionKey'); // or AsyncStorage for React Native
      
      const response = await fetch('http://your-api-url/profile/view-profile', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Profile) {
        return data.Profile;
      } else {
        throw new Error(data.Message || 'Failed to fetch profile');
      }
    } catch (error) {
      console.error('Profile fetch error:', error);
      throw error;
    }
  };
  ```

---

### Profile Management

#### Update Employee Profile
- **Endpoint**: `POST /profile/employee/update-profile`
- **Description**: Update an employee's profile information. All fields except PWD ID Front and PWD ID Back can be updated. Resume and profile picture can be uploaded. Only non-empty fields are updated; omitted or empty fields are ignored and not overwritten.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request (multipart/form-data)**:
  - `full_name` (string, optional)
  - `address` (string, optional)
  - `phone_number` (string, optional)
  - `short_bio` (string, optional)
  - `disability` (string, optional)
  - `skills` (string, optional, comma-separated or JSON array)
  - `resume` (file, optional, PDF only, max 5MB)
  - `profile_pic` (file, optional, JPG/JPEG/PNG/GIF, max 5MB)

- **Sample Request (curl)**:
```bash
curl -X POST "http://your-api-url/profile/employee/update-profile" \
  -H "Authorization: Bearer <access_token>" \
  -F "full_name=Richard Gomex" \
  -F "address=Quezon City" \
  -F "phone_number=09123456789" \
  -F "short_bio=asfdassfasfassf" \
  -F "disability=Pilay" \
  -F "skills=AWS,Figma,SEO,Python,Java" \
  -F "resume=@/path/to/resume.pdf" \
  -F "profile_pic=@/path/to/profile.jpg"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": "Update successfull"
}
```

- **Error Responses**:
```json
{
  "Status": "Error",
  "Message": "Resume must be a PDF file"
}
{
  "Status": "Error",
  "Message": "Profile picture must be an image file (JPG, JPEG, PNG, or GIF)"
}
{
  "Status": "Error",
  "Message": "No valid fields provided for update."
}
{
  "Status": "Error",
  "Message": "A unique field value you are trying to update already exists for another employee."
}
```

- **Notes:**
  - `pwd_id_front` and `pwd_id_back` cannot be updated via this endpoint.
  - If a file is provided but is empty, it will be ignored.
  - If a field is omitted or left empty, it will not overwrite the existing value in the database.
  - Only changed fields are updated.
  - Resume must be a PDF and profile picture must be an image (JPG, JPEG, PNG, or GIF).
  - File size for uploads is limited to 5MB each.
  - **React Native Tip:** Use the same `FormData` approach as signup. Omit fields you don't want to update.

#### Update Employer Profile
- **Endpoint**: `POST /profile/employer/update-profile`
- **Description**: Update an employer's profile information. All fields from signup can be updated, including company logo. Only non-empty fields are updated; omitted or empty fields are ignored and not overwritten.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request (multipart/form-data)**:
  - `company_name` (string, optional)
  - `company_level` (string, optional)
  - `website_url` (string, optional)
  - `company_type` (string, optional)
  - `industry` (string, optional)
  - `admin_name` (string, optional)
  - `description` (string, optional)
  - `location` (string, optional)
  - `tags` (string, optional)
  - `logo` (file, optional, JPG/JPEG/PNG/GIF, max 5MB)

- **Sample Request (curl)**:
```bash
curl -X POST "http://your-api-url/profile/employer/update-profile" \
  -H "Authorization: Bearer <access_token>" \
  -F "company_name=BlaBla Inc." \
  -F "company_level=Medium" \
  -F "website_url=blbla.com" \
  -F "company_type=LLC" \
  -F "industry=Technology" \
  -F "admin_name=John Stuart" \
  -F "description=agsdfhgashjkfghjas" \
  -F "location=London" \
  -F "tags=hiring" \
  -F "logo=@/path/to/logo.jpg"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": "Update successfull"
}
```

- **Error Responses**:
```json
{
  "Status": "Error",
  "Message": "Invalid logo file type. Allowed: JPG, JPEG, PNG, GIF"
}
{
  "Status": "Error",
  "Message": "Logo file size must be less than 5MB"
}
{
  "Status": "Error",
  "Message": "No valid fields provided for update."
}
{
  "Status": "Error",
  "Message": "A unique field value you are trying to update already exists for another employer."
}
```

- **Notes:**
  - If a file is provided but is empty, it will be ignored.
  - If a field is omitted or left empty, it will not overwrite the existing value in the database.
  - Only changed fields are updated.
  - Logo must be an image (JPG, JPEG, PNG, or GIF), max 5MB.
  - **Web Tip:** Use `FormData` in JavaScript or a proper HTML form. Omit fields you don't want to update.

---

## Employee Endpoints

### Job Recommendations
- **Endpoint**: `GET /reco-jobs`
- **Description**: Get personalized job recommendations based on employee's skills and disability status. Uses content-based and collaborative filtering algorithms.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/reco-jobs" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "recommendations": [
      {
        "id": 13,
        "user_id": "148cc1c6-2e81-4037-913c-7617564baa33",
        "title": "Transcriptionist",
        "job_description": "Transcribe audio content to text",
        "skill_1": "Grammar",
        "skill_2": "Transcription Tools",
        "skill_3": "Listening",
        "skill_4": "Detail Orientation",
        "skill_5": "Typing",
        "pwd_friendly": false,
        "created_at": "2025-06-05T12:57:47.917283+00:00",
        "company_name": "TechCorp",
        "location": "Remote",
        "job_type": "Part-time",
        "industry": "Technology",
        "experience": "Entry Level",
        "min_salary": 400.0,
        "max_salary": 600.0,
        "skill_match_score": 0.6,
        "matched_skills": ["typing", "listening", "grammar"]
      }
    ]
  }
  ```

- **React Native Implementation**:
  ```javascript
  const getJobRecommendations = async () => {
    try {
      const token = await AsyncStorage.getItem('sessionKey');
      
      const response = await fetch('http://your-api-url/reco-jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.recommendations) {
        return data.recommendations;
      } else {
        throw new Error(data.Message || 'No recommendations available');
      }
    } catch (error) {
      console.error('Recommendations error:', error);
      throw error;
    }
  };
  ```

---

### Resume Management

#### Upload Resume
- **Endpoint**: `POST /upload-resume`
- **Description**: Upload or update employee resume. Only PDF files are accepted.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request (multipart/form-data)**:
  - `file` (file, required, PDF only, max 5MB)

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/upload-resume" \
    -H "Authorization: Bearer <access_token>" \
    -F "file=@/path/to/resume.pdf"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Success",
    "Message": "Resume uploaded successfully",
    "ResumeURL": "https://.../resumes/user_id/resume.pdf"
  }
  ```

- **Error Responses**:
  ```json
  {
    "Status": "Error",
    "Message": "Only PDF files are allowed"
  }
  {
    "Status": "Error",
    "Message": "File size must be less than 5MB"
  }
  ```

- **React Native Implementation**:
  ```javascript
  const uploadResume = async (resumeUri) => {
    try {
      const token = await AsyncStorage.getItem('sessionKey');
      
      const formData = new FormData();
      formData.append('file', {
        uri: resumeUri,
        type: 'application/pdf',
        name: 'resume.pdf'
      });
      
      const response = await fetch('http://your-api-url/upload-resume', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (data.Status === 'Success') {
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Resume upload error:', error);
      throw error;
    }
  };
  ```

---

### Job Applications

#### Apply for Job
- **Endpoint**: `POST /apply-job/{job_id}`
- **Description**: Apply for a specific job. Employee must be authenticated.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `job_id` (path parameter, required) - The ID of the job to apply for
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/apply-job/16" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Message": "You applied to job 16",
    "Details": [
      {
        "id": 1,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": "16",
        "status": "under_review",
        "created_at": "2025-06-05T14:13:35.947101+00:00"
      }
    ]
  }
  ```

- **Error Response**:
  ```json
  {
    "Status": "Error",
    "Message": "Can't find the user"
  }
  ```

- **React Native Implementation**:
  ```javascript
  const applyForJob = async (jobId) => {
    try {
      const token = await AsyncStorage.getItem('sessionKey');
      
      const response = await fetch(`http://your-api-url/apply-job/${jobId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Job application error:', error);
      throw error;
    }
  };
  ```

---

#### View Application History
- **Endpoint**: `GET /my-applications`
- **Description**: Get all job applications submitted by the current employee.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/my-applications" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Message": [
      {
        "id": 1,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": "16",
        "status": "under_review",
        "created_at": "2025-06-05T14:13:35.947101+00:00"
      },
      {
        "id": 2,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": "14",
        "status": "accepted",
        "created_at": "2025-06-04T10:30:22.123456+00:00"
      }
    ]
  }
  ```

- **React Native Implementation**:
  ```javascript
  const getMyApplications = async () => {
    try {
      const token = await AsyncStorage.getItem('sessionKey');
      
      const response = await fetch('http://your-api-url/my-applications', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data.Message; // Contains the applications array
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Applications history error:', error);
      throw error;
    }
  };
  ```

---

## Employer Endpoints

### Job Management

#### Create Job
- **Endpoint**: `POST /jobs/create-jobs`
- **Description**: Create a new job listing. Only employers can create jobs.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request (JSON)**:
  ```json
  {
    "title": "Software Developer",
    "company_name": "TechCorp Inc.",
    "location": "Remote",
    "job_type": "Full-time",
    "industry": "Technology",
    "experience": "Mid-level",
    "description": "We are looking for a skilled software developer...",
    "skill_1": "JavaScript",
    "skill_2": "React",
    "skill_3": "Node.js",
    "skill_4": "MongoDB",
    "skill_5": "Git",
    "pwd_friendly": true,
    "min_salary": 50000.0,
    "max_salary": 80000.0
  }
  ```

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/jobs/create-jobs" \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Software Developer",
      "company_name": "TechCorp Inc.",
      "location": "Remote",
      "job_type": "Full-time",
      "industry": "Technology",
      "experience": "Mid-level",
      "description": "We are looking for a skilled software developer...",
      "skill_1": "JavaScript",
      "skill_2": "React",
      "skill_3": "Node.js",
      "skill_4": "MongoDB",
      "skill_5": "Git",
      "pwd_friendly": true,
      "min_salary": 50000.0,
      "max_salary": 80000.0
    }'
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Sucessfull",
    "Message": "Job has been created",
    "Details": "data=[{id: 8, user_id: '148cc1c6-2e81-4037-913c-7617564baa33', title: 'Software Developer', job_description: 'We are looking for...', skill_1: 'JavaScript', skill_2: 'React', skill_3: 'Node.js', skill_4: 'MongoDB', skill_5: 'Git', pwd_friendly: True, created_at: '2025-06-04T06:23:51.104274+00:00'}] count=None"
  }
  ```

- **Web Implementation (JavaScript)**:
  ```javascript
  const createJob = async (jobData) => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch('http://your-api-url/jobs/create-jobs', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(jobData)
      });
      
      const data = await response.json();
      
      if (data.Status === 'Sucessfull') {
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Job creation error:', error);
      throw error;
    }
  };
  ```

---

#### View All Jobs
- **Endpoint**: `GET /jobs/view-all-jobs`
- **Description**: Get all job listings created by the current employer.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/jobs/view-all-jobs" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "jobs": [
      {
        "id": 11,
        "user_id": "148cc1c6-2e81-4037-913c-7617564baa33",
        "title": "Content Writer",
        "job_description": "Create engaging content for our blog",
        "skill_1": "SEO",
        "skill_2": "Copywriting",
        "skill_3": "Grammar",
        "skill_4": "WordPress",
        "skill_5": "Research",
        "pwd_friendly": true,
        "created_at": "2025-06-05T12:39:57.008087+00:00",
        "company_name": "ContentCorp",
        "location": "Remote",
        "job_type": "Part-time",
        "industry": "Marketing",
        "experience": "Entry Level",
        "min_salary": 7000.0,
        "max_salary": 8000.0
      }
    ]
  }
  ```

- **Web Implementation**:
  ```javascript
  const getAllJobs = async () => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch('http://your-api-url/jobs/view-all-jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.jobs) {
        return data.jobs;
      } else {
        throw new Error(data.Message || 'No jobs found');
      }
    } catch (error) {
      console.error('Jobs fetch error:', error);
      throw error;
    }
  };
  ```

---

#### View Specific Job
- **Endpoint**: `GET /jobs/view-job/{id}`
- **Description**: Get details of a specific job listing.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `id` (path parameter, required) - The ID of the job
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/jobs/view-job/16" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Message": "Job Number 16 Found",
    "Details": [
      {
        "id": 16,
        "user_id": "148cc1c6-2e81-4037-913c-7617564baa33",
        "title": "Housekeeper",
        "job_description": "Part-time housekeeping position",
        "skill_1": "Cleaning Techniques",
        "skill_2": "Attention to Detail",
        "skill_3": "Time Management",
        "skill_4": "Safety Practices",
        "skill_5": "Organization",
        "pwd_friendly": true,
        "created_at": "2025-06-05T13:24:32.405627+00:00",
        "company_name": "CleanCorp",
        "location": "Local",
        "job_type": "Part-time",
        "industry": "Services",
        "experience": "Entry Level",
        "min_salary": 800.0,
        "max_salary": 1000.0
      }
    ]
  }
  ```

---

#### Update Job
- **Endpoint**: `POST /jobs/update-job/{id}`
- **Description**: Update an existing job listing.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `id` (path parameter, required) - The ID of the job to update
- **Request**: Same JSON structure as create job

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/jobs/update-job/16" \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Senior Housekeeper",
      "company_name": "CleanCorp",
      "location": "Local",
      "job_type": "Full-time",
      "industry": "Services",
      "experience": "Mid-level",
      "description": "Senior housekeeping position with team leadership",
      "skill_1": "Cleaning Techniques",
      "skill_2": "Team Leadership",
      "skill_3": "Time Management",
      "skill_4": "Safety Practices",
      "skill_5": "Organization",
      "pwd_friendly": true,
      "min_salary": 1200.0,
      "max_salary": 1500.0
    }'
  ```

---

#### Delete Job
- **Endpoint**: `POST /jobs/delete-job/{id}`
- **Description**: Delete a job listing.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `id` (path parameter, required) - The ID of the job to delete
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/jobs/delete-job/16" \
    -H "Authorization: Bearer <access_token>"
  ```

---

### Application Management

#### View Job Applicants
- **Endpoint**: `GET /view-applicants/{job_id}`
- **Description**: Get all applicants for a specific job listing.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `job_id` (path parameter, required) - The ID of the job
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/view-applicants/16" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Applicants": [
      {
        "id": 1,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": 16,
        "status": "under_review",
        "created_at": "2025-06-05T14:13:35.947101+00:00"
      }
    ]
  }
  ```

- **Web Implementation**:
  ```javascript
  const getJobApplicants = async (jobId) => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch(`http://your-api-url/view-applicants/${jobId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data.Applicants;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Applicants fetch error:', error);
      throw error;
    }
  };
  ```

---

#### Update Application Status
- **Endpoint**: `PATCH /application/{id}/status`
- **Description**: Update the status of a job application (e.g., accepted, rejected, under_review).
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `id` (path parameter, required) - The ID of the application
  - `new_status` (query parameter, required) - The new status ('under_review', 'accepted', 'rejected')

- **Sample Request (curl)**:
  ```bash
  curl -X PATCH "http://your-api-url/application/1/status?new_status=accepted" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Applicants": [
      {
        "id": 1,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": 16,
        "status": "accepted",
        "created_at": "2025-06-05T14:13:35.947101+00:00"
      }
    ]
  }
  ```

- **Web Implementation**:
  ```javascript
  const updateApplicationStatus = async (applicationId, newStatus) => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch(`http://your-api-url/application/${applicationId}/status?new_status=${newStatus}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Status update error:', error);
      throw error;
    }
  };
  ```

---

#### Decline Application
- **Endpoint**: `POST /decline-application/{application_id}`
- **Description**: Decline a specific job application. This sets the application status to "rejected".
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `application_id` (path parameter, required) - The ID of the application to decline
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X POST "http://your-api-url/decline-application/5" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Message": "Application declined successfully",
    "Application": {
      "id": 5,
      "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
      "job_id": 16,
      "status": "rejected",
      "created_at": "2025-06-05T14:13:35.947101+00:00",
      "updated_at": "2025-06-06T10:30:00.000000+00:00"
    }
  }
  ```

- **Error Response**:
  ```json
  {
    "Status": "Error",
    "Message": "Application not found"
  }
  ```

- **Web Implementation**:
  ```javascript
  const declineApplication = async (applicationId) => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch(`http://your-api-url/decline-application/${applicationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Decline application error:', error);
      throw error;
    }
  };
  ```

---

#### Get Declined Applications
- **Endpoint**: `GET /get-declined-applications`
- **Description**: Get all declined job applications for the current employer. Returns applications that have been rejected.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
  ```bash
  curl -X GET "http://your-api-url/get-declined-applications" \
    -H "Authorization: Bearer <access_token>"
  ```

- **Sample Response**:
  ```json
  {
    "Status": "Successfull",
    "Message": "Declined applications retrieved successfully",
    "Applications": [
      {
        "id": 5,
        "user_id": "f9b86db6-93dc-4e29-a1be-6dfcb114b8f7",
        "job_id": 16,
        "status": "rejected",
        "created_at": "2025-06-05T14:13:35.947101+00:00",
        "updated_at": "2025-06-06T10:30:00.000000+00:00",
        "applicant_details": {
          "full_name": "John Doe",
          "email": "john.doe@example.com",
          "skills": "JavaScript, React, Node.js",
          "disability": "None",
          "resume_url": "https://example.com/resume.pdf"
        },
        "job_details": {
          "title": "Software Developer",
          "company_name": "TechCorp",
          "location": "Remote"
        }
      }
    ]
  }
  ```

- **Error Response**:
  ```json
  {
    "Status": "Error",
    "Message": "No declined applications found"
  }
  ```

- **Web Implementation**:
  ```javascript
  const getDeclinedApplications = async () => {
    try {
      const token = localStorage.getItem('sessionKey');
      
      const response = await fetch('http://your-api-url/get-declined-applications', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.Status === 'Successfull') {
        return data.Applications;
      } else {
        throw new Error(data.Message);
      }
    } catch (error) {
      console.error('Declined applications fetch error:', error);
      throw error;
    }
  };
  ```

---

## Real-time Chat Communication

### WebSocket Chat Connection
- **Endpoint**: `WebSocket /ws/chat/{user_id}?token={access_token}`
- **Description**: Establishes a WebSocket connection for real-time chat between employers and employees. Handles both online and offline messaging with persistent storage.
- **Parameters**:
  - `user_id` (path parameter, required) - The ID of the connecting user
  - `token` (query parameter, required) - The authentication token from login

- **Sample Connection (JavaScript)**:
```javascript
const token = "your_auth_token";
const userId = "your_user_id";
const ws = new WebSocket(`ws://your-api-url/ws/chat/${userId}?token=${token}`);

ws.onopen = () => {
  console.log('Connected to chat');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received message:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Disconnected from chat:', event.reason);
};
```

### Sending Messages
- **Message Format**:
```json
{
  "sender_id": "user_id_of_sender",
  "receiver_id": "user_id_of_receiver",
  "job_id": "related_job_id",
  "type": "text",
  "message": "Hello, this is a test message!"
}
```

- **Message Types**:
  - `"text"` - Regular text message
  - `"zoom_link"` - Zoom meeting link
  - `"form_link"` - Form or document link
  - `"status_update"` - Application status update

- **Sample Message Send**:
```javascript
ws.send(JSON.stringify({
  "sender_id": "sender_user_id",
  "receiver_id": "receiver_user_id",
  "job_id": "123",
  "type": "text",
  "message": "Hello!"
}));
```

### Message Response Format
- **Success Response**:
```json
{
  "Status": "Success",
  "Message": "Message is sent and Stored in the database",
  "data": {
    "id": "message_id",
    "sender_id": "sender_user_id",
    "receiver_id": "receiver_user_id",
    "job_id": "123",
    "type": "text",
    "message": "Hello!",
    "created_at": "2025-06-15T10:30:00Z"
  }
}
```

- **Error Response**:
```json
{
  "Status": "Error",
  "Message": "Error message here"
}
```

### React Native Implementation
```javascript
class ChatService {
  constructor(userId, token) {
    this.userId = userId;
    this.token = token;
    this.ws = null;
    this.messageHandlers = new Set();
  }

  connect() {
    this.ws = new WebSocket(`ws://your-api-url/ws/chat/${this.userId}?token=${this.token}`);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageHandlers.forEach(handler => handler(data));
    };

    this.ws.onclose = () => {
      // Implement reconnection logic
      setTimeout(() => this.connect(), 5000);
    };
  }

  sendMessage(receiverId, jobId, message, type = "text") {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        sender_id: this.userId,
        receiver_id: receiverId,
        job_id: jobId,
        type: type,
        message: message
      }));
    }
  }

  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
  }

  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage in a React Native component:
const ChatScreen = () => {
  const [messages, setMessages] = useState([]);
  const chatService = useRef(null);

  useEffect(() => {
    const initChat = async () => {
      const userId = await AsyncStorage.getItem('userId');
      const token = await AsyncStorage.getItem('sessionKey');
      
      chatService.current = new ChatService(userId, token);
      chatService.current.addMessageHandler((data) => {
        setMessages(prev => [...prev, data]);
      });
      chatService.current.connect();
    };

    initChat();

    return () => {
      chatService.current?.disconnect();
    };
  }, []);

  const sendMessage = (receiverId, jobId, message, type = "text") => {
    chatService.current?.sendMessage(receiverId, jobId, message, type);
  };

  return (
    // Your chat UI components
  );
};
```

### Web Implementation
```javascript
class WebChatService {
  constructor(userId, token) {
    this.userId = userId;
    this.token = token;
    this.ws = null;
    this.messageHandlers = [];
  }

  connect() {
    this.ws = new WebSocket(`ws://your-api-url/ws/chat/${this.userId}?token=${this.token}`);
    
    this.ws.onopen = () => {
      console.log('Connected to chat');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageHandlers.forEach(handler => handler(data));
    };

    this.ws.onclose = () => {
      console.log('Disconnected from chat');
      // Implement reconnection logic
      setTimeout(() => this.connect(), 5000);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  sendMessage(receiverId, jobId, message, type = "text") {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        sender_id: this.userId,
        receiver_id: receiverId,
        job_id: jobId,
        type: type,
        message: message
      }));
    }
  }

  addMessageHandler(handler) {
    this.messageHandlers.push(handler);
  }

  removeMessageHandler(handler) {
    const index = this.messageHandlers.indexOf(handler);
    if (index > -1) {
      this.messageHandlers.splice(index, 1);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage in a web component:
const initializeChat = () => {
  const userId = localStorage.getItem('userId');
  const token = localStorage.getItem('sessionKey');
  
  const chatService = new WebChatService(userId, token);
  chatService.addMessageHandler((data) => {
    // Handle received message
    displayMessage(data);
  });
  chatService.connect();
  
  return chatService;
};
```

### Chat Features
- **Real-time messaging** between employers and employees
- **Offline message storage** and delivery when users come back online
- **Message read status** tracking
- **Multiple message types** support (text, zoom links, form links, status updates)
- **Automatic reconnection** handling for dropped connections
- **Message persistence** in Supabase database
- **Token-based authentication** for secure connections
- **Proper connection cleanup** to prevent memory leaks

### Error Codes
- `4001`: Missing authentication token
- `4002`: Invalid or expired token
- `4003`: User ID mismatch with token
- `4500`: Internal authentication error

### Connection Best Practices
1. **Always authenticate** with a valid token before connecting
2. **Handle connection drops** gracefully with automatic reconnection
3. **Clean up connections** when components unmount
4. **Validate message format** before sending
5. **Implement message queuing** for offline scenarios
6. **Use proper error handling** for all WebSocket events

---

### Chat History API

#### Get Chat History
- **Endpoint**: `GET /messages/{sender_id}/{receiver_id}`
- **Description**: Retrieve chat message history between two users. This endpoint fetches messages in one direction only (from sender to receiver). To get complete conversation history, you need to make two API calls with swapped sender/receiver IDs.
- **Parameters**:
  - `sender_id` (path parameter, required) - The ID of the message sender
  - `receiver_id` (path parameter, required) - The ID of the message receiver (note: there's a typo in the actual endpoint parameter name: `reciever_id`)
- **Request**: No body required

- **Sample Request (curl)**:
```bash
curl -X GET "http://your-api-url/messages/a14887b6-6292-4fd9-85c7-8cd821c19d22/f5cf5a60-f6d7-4754-b7cc-31ed083b0dd3"
```

- **Sample Response (Success)**:
```json
{
  "Status": "Success",
  "Message": "Chat history fetched successfully",
  "data": [
    {
      "id": 2,
      "job_id": 24,
      "sender_id": "a14887b6-6292-4fd9-85c7-8cd821c19d22",
      "receiver_id": "f5cf5a60-f6d7-4754-b7cc-31ed083b0dd3",
      "message": "test",
      "type": "text",
      "created_at": "2025-07-14T05:18:39.50607+00:00",
      "is_read": false
    },
    {
      "id": 3,
      "job_id": 24,
      "sender_id": "a14887b6-6292-4fd9-85c7-8cd821c19d22",
      "receiver_id": "f5cf5a60-f6d7-4754-b7cc-31ed083b0dd3",
      "message": "LALALA",
      "type": "text",
      "created_at": "2025-07-14T05:20:37.308868+00:00",
      "is_read": false
    }
  ]
}
```

- **Sample Response (No History)**:
```json
{
  "Status": "Error",
  "Message": "No chat history found"
}
```

- **Error Response**:
```json
{
  "Status": "Error",
  "Message": "Failed to fetch chat history",
  "Details": "Error details here"
}
```

#### Implementation Examples

**JavaScript/Web Implementation**:
```javascript
const getChatHistory = async (senderId, receiverId) => {
  try {
    const response = await fetch(`http://your-api-url/messages/${senderId}/${receiverId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
        // Note: Add Authorization header when authentication is implemented
      }
    });
    
    const data = await response.json();
    
    if (data.Status === 'Success') {
      return data.data; // Returns the messages array
    } else {
      throw new Error(data.Message);
    }
  } catch (error) {
    console.error('Chat history fetch error:', error);
    throw error;
  }
};

// To get complete conversation history (both directions):
const getCompleteConversation = async (userId1, userId2) => {
  try {
    const [messages1, messages2] = await Promise.all([
      getChatHistory(userId1, userId2),
      getChatHistory(userId2, userId1)
    ]);
    
    // Combine and sort messages by creation date
    const allMessages = [...(messages1 || []), ...(messages2 || [])];
    return allMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  } catch (error) {
    console.error('Complete conversation fetch error:', error);
    return [];
  }
};
```

**React Native Implementation**:
```javascript
const getChatHistory = async (senderId, receiverId) => {
  try {
    const response = await fetch(`http://your-api-url/messages/${senderId}/${receiverId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
        // Note: Add Authorization header when authentication is implemented
      }
    });
    
    const data = await response.json();
    
    if (data.Status === 'Success') {
      return data.data;
    } else {
      throw new Error(data.Message);
    }
  } catch (error) {
    console.error('Chat history fetch error:', error);
    throw error;
  }
};

// Usage in a React Native component:
const ChatScreen = ({ route }) => {
  const { receiverId } = route.params;
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const userId = await AsyncStorage.getItem('userId');
        const history = await getCompleteConversation(userId, receiverId);
        setMessages(history);
      } catch (error) {
        console.error('Failed to load chat history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadChatHistory();
  }, [receiverId]);

  // Rest of your component logic
};
```

#### Important Notes

1. **Directional Messages**: This endpoint only returns messages sent from `sender_id` to `receiver_id`. For a complete conversation, you need two API calls with swapped user IDs.

2. **Missing Authentication**: The current implementation doesn't require authentication. Consider adding authorization to prevent unauthorized access to private conversations.

3. **Parameter Typo**: The actual endpoint has a typo in the parameter name (`reciever_id` instead of `receiver_id`). Use the typo when making API calls.

4. **Message Ordering**: Messages are returned in chronological order (oldest first) based on `created_at` timestamp.

5. **Integration with WebSocket**: Use this endpoint to load chat history when opening a conversation, then use WebSocket for real-time messaging.

#### Recommended Usage Pattern

```javascript
// 1. Load chat history when opening conversation
const initializeChat = async (currentUserId, otherUserId) => {
  // Load historical messages
  const history = await getCompleteConversation(currentUserId, otherUserId);
  displayMessages(history);
  
  // Connect to WebSocket for real-time messaging
  const chatService = new WebChatService(currentUserId, token);
  chatService.connect();
  
  return chatService;
};
```

---

## Error Handling

All endpoints follow a consistent error response format:
```json
{
  "Status": "ERROR",
  "Message": "Error message here",
  "Details": "Detailed error information (if available)"
}
```

Common error scenarios:
1. Authentication failures
2. Invalid input data
3. Resource not found
4. Server errors
5. Unique constraint violations (duplicate values)
6. File validation errors (type/size)

---

## Frontend Implementation Tips

### Authentication Flow
1. **Initial Setup**: Store session tokens securely (localStorage for web, AsyncStorage for React Native)
2. **Token Management**: Include tokens in Authorization headers for all authenticated endpoints
3. **Session Handling**: Implement automatic logout on token expiration

### For Employers (Web Frontend)

#### General Setup
```javascript
// API Base Configuration
const API_BASE_URL = 'http://your-api-url';
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('sessionKey')}`,
  'Content-Type': 'application/json'
});
```

#### File Upload Implementation
```javascript
// For multipart/form-data endpoints (signup, profile updates)
const uploadWithFiles = async (endpoint, formData) => {
  const token = localStorage.getItem('sessionKey');
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // Don't set Content-Type for multipart/form-data
    },
    body: formData
  });
  
  return response.json();
};
```

#### Complete Authentication Implementation
```javascript
class AuthService {
  static async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/employer/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (data.Status === 'Success') {
      localStorage.setItem('sessionKey', data['Debug Session Key']);
      localStorage.setItem('userId', data['App User ID']);
      return data;
    }
    throw new Error(data.Message);
  }
  
  static async logout() {
    const token = localStorage.getItem('sessionKey');
    await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    localStorage.removeItem('sessionKey');
    localStorage.removeItem('userId');
  }
}
```

#### Job Management Implementation
```javascript
class JobService {
  static async createJob(jobData) {
    const response = await fetch(`${API_BASE_URL}/jobs/create-jobs`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(jobData)
    });
    return response.json();
  }
  
  static async getJobs() {
    const response = await fetch(`${API_BASE_URL}/jobs/view-all-jobs`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    return response.json();
  }
  
  static async deleteJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/jobs/delete-job/${jobId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return response.json();
  }
}
```

### For Employees (React Native)

#### Dependencies Setup
```bash
npm install @react-native-async-storage/async-storage
expo install expo-image-picker expo-document-picker
```

#### General Setup
```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';

const API_BASE_URL = 'http://your-api-url';

const getAuthHeaders = async () => {
  const token = await AsyncStorage.getItem('sessionKey');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};
```

#### Complete Authentication Implementation
```javascript
class AuthService {
  static async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/employee/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (data.Status === 'Success') {
      await AsyncStorage.setItem('sessionKey', data['Debug Session Key']);
      await AsyncStorage.setItem('userId', data['App User ID']);
      return data;
    }
    throw new Error(data.Message);
  }
  
  static async logout() {
    const token = await AsyncStorage.getItem('sessionKey');
    await fetch(`${API_BASE_URL}/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    await AsyncStorage.removeItem('sessionKey');
    await AsyncStorage.removeItem('userId');
  }
}
```

#### File Upload Implementation
```javascript
class FileService {
  static async pickImage() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    
    if (!result.canceled) {
      return result.assets[0];
    }
    return null;
  }
  
  static async pickDocument() {
    const result = await DocumentPicker.getDocumentAsync({
      type: 'application/pdf',
      copyToCacheDirectory: false,
    });
    
    if (result.type === 'success') {
      return result;
    }
    return null;
  }
  
  static async uploadResume(resumeUri) {
    const token = await AsyncStorage.getItem('sessionKey');
    
    const formData = new FormData();
    formData.append('file', {
      uri: resumeUri,
      type: 'application/pdf',
      name: 'resume.pdf'
    });
    
    const response = await fetch(`${API_BASE_URL}/upload-resume`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      },
      body: formData
    });
    
    return response.json();
  }
}
```

#### Job Application Implementation
```javascript
class JobApplicationService {
  static async getRecommendations() {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/reco-jobs`, {
      method: 'GET',
      headers
    });
    return response.json();
  }
  
  static async applyForJob(jobId) {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/apply-job/${jobId}`, {
      method: 'POST',
      headers
    });
    return response.json();
  }
  
  static async getApplicationHistory() {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/my-applications`, {
      method: 'GET',
      headers
    });
    return response.json();
  }
}
```

### Error Handling Best Practices

#### Standard Error Handler
```javascript
const handleApiError = (error) => {
  if (error.message.includes('401')) {
    // Redirect to login
    window.location.href = '/login'; // Web
    // or navigation.navigate('Login'); // React Native
  } else if (error.message.includes('404')) {
    console.error('Resource not found');
  } else if (error.message.includes('500')) {
    console.error('Server error');
  } else {
    console.error('API Error:', error.message);
  }
};
```

#### File Validation
```javascript
const validateFile = (file, type = 'image', maxSize = 5) => {
  const maxSizeBytes = maxSize * 1024 * 1024; // Convert MB to bytes
  
  if (file.size > maxSizeBytes) {
    throw new Error(`File size must be less than ${maxSize}MB`);
  }
  
  if (type === 'image') {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      throw new Error('Only JPG, JPEG, PNG, and GIF files are allowed');
    }
  } else if (type === 'pdf') {
    if (file.type !== 'application/pdf') {
      throw new Error('Only PDF files are allowed');
    }
  }
};
```

### UI/UX Implementation Tips

#### Loading States
```javascript
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  try {
    await apiCall();
    // Success feedback
  } catch (error) {
    // Error feedback
  } finally {
    setLoading(false);
  }
};
```

#### Form Validation
```javascript
const validateForm = (formData) => {
  const errors = {};
  
  if (!formData.email) errors.email = 'Email is required';
  if (!formData.password || formData.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }
  
  return errors;
};
```

---

## Additional Notes

### Security Considerations
- Always validate file types and sizes on the frontend before upload
- Store session tokens securely (never in plain text)
- Implement proper error handling to avoid exposing sensitive information
- Use HTTPS in production environments

### Performance Tips
- Implement request caching for frequently accessed data
- Use image compression before upload
- Implement pagination for large data sets
- Add loading states for better user experience

### API Response Formats
- All responses follow a consistent format with `Status`, `Message`, and optional `Details`
- Success status can be "Success", "Successfull", or "Successful" (note the inconsistency in the API)
- Error status is always "Error" or "ERROR"
- Always check the status field before processing response data

### Required Headers
- **Authentication**: `Authorization: Bearer <access_token>` for all protected endpoints
- **Content-Type**: 
  - `application/json` for JSON requests
  - `multipart/form-data` for file uploads (don't set manually, let the browser/framework handle it)

### File Upload Limitations
- **Resume**: PDF only, max 5MB
- **Profile Pictures**: JPG, JPEG, PNG, GIF only, max 5MB
- **Company Logo**: JPG, JPEG, PNG, GIF only, max 5MB
- **PWD ID**: JPG, JPEG, PNG, GIF only, max 5MB

### Status Codes
- **200**: Success
- **401**: Unauthorized (invalid or missing token)
- **404**: Resource not found
- **500**: Internal server error
