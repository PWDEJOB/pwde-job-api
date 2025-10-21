from utils.general.service import getSupabaseServiceClient
import httpx

#Send basic notification
async def sendNotification(user_id: str, receiver_id: str, content: str, category: str):
    supabase = getSupabaseServiceClient()
    
    # Validate inputs
    if not user_id or not receiver_id or not content or not category:
        raise Exception(f"Missing required notification data: user_id={user_id}, receiver_id={receiver_id}, content={content}, category={category}")
    
    # Ensure all inputs are strings
    user_id = str(user_id)
    receiver_id = str(receiver_id)
    content = str(content)
    category = str(category)

    #employer notifs categories
    
    #employee notifs categories
    if category == "new_applicant":
        title = "You have a new applicant"
    elif category == "message":
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
async def getUserPushToken(user_id: str) -> str:
    """Get the active push token for a user from the database"""
    try:
        supabase = getSupabaseServiceClient()
        response = supabase.table("push_tokens").select("expo_token").eq("user_id", user_id).eq("active", True).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["expo_token"]
        return None
    except Exception as e:
        print(f"❌ Error getting push token for user {user_id}: {str(e)}")
        return None

async def sendPushNotification(expo_token: str, title: str, body: str, data: dict = None):
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

def getNotificationContent(message_type: str):
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

def getJobStatusNotificationContent(status: str, job_title: str):
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