# PWDE-JOB API Documentation (Updates)

## Table of Contents
1. [Real-time Chat Updates](#real-time-chat-updates)
2. [API Updates - January 2025](#api-updates---january-2025)

---

## API Updates - January 2025

### Endpoint Renames
The following endpoints have been renamed for better consistency and clarity:

| Old Endpoint Name | New Endpoint Name |
|------------------|-------------------|
| `/signupEmployee` | `/employee/signup` |
| `/signupEmployer` | `/employer/signup` |
| `/login-employee` | `/employee/login` |
| `/login-employer` | `/employer/login` |
| `/view-profile` | `/profile/view-profile` |
| `/update-profile/employer` | `/profile/employer/update-profile` |
| `/update-profile/employee` | `/profile/employee/update-profile` |
| `/create-jobs` | `/jobs/create-jobs` |
| `/view-all-jobs` | `/jobs/view-all-jobs` |
| `/view-job/{id}` | `/jobs/view-job/{id}` |
| `/delete-job/{id}` | `/jobs/delete-job/{id}` |
| `/update-job/{id}` | `/jobs/update-job/{id}` |
| `/job/{job_id}/applicants` | `/view-applicants/{job_id}` |
| `/declined-applications` | `/get-declined-applications` |

**Key Improvements**:
- **Better Organization**: Endpoints are now grouped by functionality (employee/, employer/, profile/, jobs/)
- **Consistent Naming**: All endpoints follow consistent REST-like patterns
- **Clearer Hierarchy**: Related endpoints are grouped under common prefixes
- **Improved Readability**: Endpoint names are more descriptive and intuitive

**Other endpoints remain unchanged**:
- `/apply-job/{job_id}`
- `/application/{id}/status`
- `/my-applications`
- `/decline-application/{application_id}`
- `/reco-jobs`
- `/logout`
- `/upload-resume`
- `/preload`
- `/ws/chat/{user_id}` (WebSocket endpoint)

### Updated Apply Job Response
The `/apply-job/{job_id}` endpoint now returns enhanced response data including full applicant details.

**New Response Format**:
```json
{
  "Status": "Successfull",
  "Message": "You applied to job {job_id}",
  "Details": [
    {
      "id": 12,
      "user_id": "fb858d83-fac8-4086-9218-33f0932b60e0",
      "job_id": 23,
      "status": "under_review",
      "created_at": "2025-07-04T07:56:28.886048+00:00",
      "applicant_details": {
        "id": 33,
        "user_id": "fb858d83-fac8-4086-9218-33f0932b60e0",
        "full_name": "Tester TEST",
        "disability": "Pilay",
        "skills": "AWS, Figma, Java, Typing, Organizing",
        "created_at": "2025-07-04T07:14:20.048208+00:00",
        "role": "employee",
        "resume_url": "https://pyakerdijdkscgtalugu.supabase.co/storage/v1/object/public/resumes/...",
        "profile_pic_url": "https://pyakerdijdkscgtalugu.supabase.co/storage/v1/object/public/profilepic/...",
        "address": "sample address",
        "phone_number": "13124124512",
        "short_bio": "sample bio",
        "pwd_id_front_url": "https://pyakerdijdkscgtalugu.supabase.co/storage/v1/object/public/pwdidfront/...",
        "pwd_id_back_url": "https://pyakerdijdkscgtalugu.supabase.co/storage/v1/object/public/pwdidback/...",
        "email": "qwer@gmail.com"
      }
    }
  ]
}
```

**Key Changes**:
- The response now includes complete `applicant_details` object with all employee information
- Applicant details include profile URLs, contact information, skills, and disability status
- The `job_applications` table now stores full applicant profiles for easier access by employers

**Benefits**:
- Employers can immediately access applicant information without additional API calls
- Faster application review process
- Complete applicant profile available in single response

---

## Real-time Chat Updates

### WebSocket Chat Connection
- **Endpoint**: `WebSocket /ws/chat/{user_id}?token={access_token}`
- **Description**: Establishes a WebSocket connection for real-time chat. Handles both online and offline messaging.
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
  "type": "text", // Can be: "text", "zoom_link", "form_link", "status_update"
  "message": "Hello, this is a test message!"
}
```

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

  sendMessage(receiverId, jobId, message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        sender_id: this.userId,
        receiver_id: receiverId,
        job_id: jobId,
        type: "text",
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
      const token = await AsyncStorage.getItem('Token');
      
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

  const sendMessage = (receiverId, jobId, message) => {
    chatService.current?.sendMessage(receiverId, jobId, message);
  };

  return (
    // Your chat UI components
  );
};
```

### Features
- Real-time messaging between users
- Offline message storage and delivery
- Message read status tracking
- Support for different message types (text, zoom links, form links, status updates)
- Automatic reconnection handling
- Message persistence in Supabase database
- Token-based authentication
- Proper connection cleanup

### Error Codes
- `4001`: Missing authentication token
- `4002`: Invalid or expired token
- `4003`: User ID mismatch
- `4500`: Internal authentication error
