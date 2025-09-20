import ast

async def parseSkills(skills_raw):
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
    
    return user_skills_set

async def calculateJobMatchScore(user_skills_set, jobs_data):
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
    return recommendations