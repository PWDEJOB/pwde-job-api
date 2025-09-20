from datetime import datetime
from datetime import date
from unittest import skip
from utils.general.service import getSupabaseServiceClient


supabase = getSupabaseServiceClient()
async def getInboxMessages(user_id):
    result = supabase.rpc("get_inbox_messages", {"uid": user_id}).execute()

    return result.data


async def getJobDetails(raw_messages):
    # Extract unique job_ids from the messages
    job_ids = list({msg["job_id"] for msg in raw_messages})

    if not job_ids:
        return []

    # Query the jobs table for matching job_ids
    result = (
        supabase.table("jobs")
        .select("*")
        .in_("id", job_ids)
        .execute()
    )

    return result.data

async def getApplicationStatus(job_details, user_id):
    statuses = []
    for job_detail in job_details:
        job_id = job_detail["id"]
        status = supabase.table("job_applications").select("status").eq("job_id", job_id).eq("user_id", user_id).execute()
        statuses.append(status.data)
    return statuses