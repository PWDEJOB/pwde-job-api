from datetime import datetime
from datetime import date
from utils.general.service import getSupabaseServiceClient

supabase_check = getSupabaseServiceClient()

# Limit employer signups per day (default 5)
async def limitNewUsers(supabase_check, daily_limit: int = 5):
    # Calculate start and end of current day in ISO format
    start_of_day = datetime.combine(date.today(), datetime.min.time())
    end_of_day = datetime.combine(date.today(), datetime.max.time())

    # Query count of employers created today
    result = (
        supabase_check
            .table("employers")
            .select("*", count="exact")
            .gte("created_at", start_of_day.isoformat())
            .lt("created_at", end_of_day.isoformat())
            .execute()
    )

    # Extract count safely (supports clients that may not expose .count)
    todays_count = getattr(result, "count", None)
    if todays_count is None:
        todays_count = len(result.data) if getattr(result, "data", None) else 0

    if todays_count >= daily_limit:
        return {
            "Status": "Error",
            "Message": f"Daily signup limit reached ({daily_limit}). Please try again tomorrow."
        }

    return {
        "Status": "OK"
    }


#check if user is already in the database
async def checkIfEmployerExists(supabase_check, email):
    user = supabase_check.table("employers").select("*").eq("email", email).execute()
    if user.data:
        return True
    return False

#check if employee signup email already exists
async def checkIfEmployeeExists(supabase_check, email):
    user = supabase_check.table("employee").select("*").eq("email", email).execute()
    if user.data:
        return True
    return False
