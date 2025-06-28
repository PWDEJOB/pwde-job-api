# PWDE-JOB API Documentation (Updates)

## Table of Contents
1. [Authentication Updates](#authentication-updates)
2. [Application Management Updates](#application-management-updates)

---

## Authentication Updates

### Preload Check
- **Endpoint**: `GET /preload`
- **Description**: Check if a user is logged in and determine their role (employee or employer). Used for initial app loading and role-based routing.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
```bash
curl -X GET "http://your-api-url/preload" \
  -H "Authorization: Bearer <access_token>"
```

- **Sample Response (Employee)**:
```json
{
  "Status": "Success",
  "isAuthenticated": true,
  "role": "employee",
  "userData": {
    "id": 32,
    "user_id": "f5cf5a60-f6d7-4754-b7cc-31ed083b0dd3",
    "full_name": "Kraken Slayer",
    "disability": "Ysywuwjj",
    "skills": "Bricklaying,Bug Reporting,Basic Veterinary Knowledge,Branding,Cash Handling",
    "created_at": "2025-06-26T07:24:44.275143+00:00",
    "role": "employee",
    "resume_url": "https://...",
    "profile_pic_url": "https://...",
    "address": "Tehwhwj",
    "phone_number": "919276362819",
    "short_bio": "Hshsjsjskmsn",
    "pwd_id_front_url": "https://...",
    "pwd_id_back_url": "https://...",
    "email": "kraken1234@gmail.com"
  }
}
```

- **Sample Response (Employer)**:
```json
{
  "Status": "Success",
  "isAuthenticated": true,
  "role": "employer",
  "userData": {
    // Employer data fields
  }
}
```

- **Error Response**:
```json
{
  "Status": "Error",
  "isAuthenticated": false,
  "Message": "Not authenticated"
}
```

- **React Native Implementation (Employee)**:
```javascript
const checkAuth = async () => {
  try {
    const token = await AsyncStorage.getItem('Token');
    
    const response = await fetch('http://your-api-url/preload', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.isAuthenticated) {
      if (data.role === 'employee') {
        // Navigate to employee dashboard
        navigation.replace('EmployeeDashboard');
      } else {
        // Wrong platform, show error
        Alert.alert('Error', 'Please use the web platform for employer access');
      }
    } else {
      // Navigate to login
      navigation.replace('Login');
    }
  } catch (error) {
    console.error('Auth check error:', error);
    // Navigate to login on error
    navigation.replace('Login');
  }
};
```

- **Web Implementation (Employer)**:
```javascript
const checkAuth = async () => {
  try {
    const token = localStorage.getItem('Token');
    
    const response = await fetch('http://your-api-url/preload', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.isAuthenticated) {
      if (data.role === 'employer') {
        // Navigate to employer dashboard
        window.location.href = '/dashboard';
      } else {
        // Wrong platform, show error
        alert('Please use the mobile app for employee access');
      }
    } else {
      // Navigate to login
      window.location.href = '/login';
    }
  } catch (error) {
    console.error('Auth check error:', error);
    // Navigate to login on error
    window.location.href = '/login';
  }
};
```

---

## Application Management Updates

### Decline Job Application
- **Endpoint**: `POST /decline-application/{application_id}`
- **Description**: Allow an employee to decline a job application. Creates a record in the declined_jobs table.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Parameters**:
  - `application_id` (path parameter, required) - The ID of the job to decline

- **Sample Request (curl)**:
```bash
curl -X POST "http://your-api-url/decline-application/123" \
  -H "Authorization: Bearer <access_token>"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": "Application declined successfully"
}
```

- **Error Response**:
```json
{
  "Status": "Error",
  "Message": "Failed to decline application"
}
```

- **React Native Implementation**:
```javascript
const declineJob = async (applicationId) => {
  try {
    const token = await AsyncStorage.getItem('Token');
    
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
    console.error('Job decline error:', error);
    throw error;
  }
};
```

### View Declined Applications
- **Endpoint**: `GET /declined-applications`
- **Description**: Get all job applications that have been declined by the employee.
- **Headers Required**: 
  - `Authorization: Bearer <access_token>`
- **Request**: No body required

- **Sample Request (curl)**:
```bash
curl -X GET "http://your-api-url/declined-applications" \
  -H "Authorization: Bearer <access_token>"
```

- **Sample Response**:
```json
{
  "Status": "Successfull",
  "Message": [
    {
      "id": 1,
      "user_id": "f5cf5a60-f6d7-4754-b7cc-31ed083b0dd3",
      "job_id": "123",
      "created_at": "2025-06-26T07:24:44.275143+00:00"
    }
  ]
}
```

- **Error Response**:
```json
{
  "Status": "Error",
  "Message": "No Data Found"
}
```

- **React Native Implementation**:
```javascript
const getDeclinedApplications = async () => {
  try {
    const token = await AsyncStorage.getItem('Token');
    
    const response = await fetch('http://your-api-url/declined-applications', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.Status === 'Successfull') {
      return data.Message;
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

## Implementation Notes

### Database Changes
- New table `declined_jobs` added to track declined job applications
- Fields:
  - `id` (auto-generated)
  - `user_id` (references employee table)
  - `job_id` (references jobs table)
  - `created_at` (timestamp)

### Security Considerations
- All new endpoints require authentication
- Role-based access control implemented for preload endpoint
- Platform-specific checks added to prevent cross-platform access

### Error Handling
- Consistent error response format maintained
- New error cases added for platform-specific access violations
- Proper validation of application IDs before processing

### Frontend Implementation Tips
- Use preload check on app startup
- Implement proper loading states during authentication check
- Handle platform-specific redirects appropriately
- Cache declined applications list for better performance