from utils.get_data import get_candidate_data_json
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from utils.init_pipeline import pipeline
import json
def generate_requirement():
    return f"""
You are a highly intelligent Recruitment Assistant AI. Your task is to create a clear and structured **Job Description** based on the user's input.

Your output **must strictly follow this JSON Format**:
{{
    "message": "<Provide a polite and professional message to the user summarizing the extracted job details>",
    "is_show_data": true,
    "need_input": false,
    "data": {{
        "job_title": "<extracted or inferred job title>",
        "location": "<location if available or inferred, or leave as empty string>",
        "salary": "<salary if available, or leave as null>",
        "skill": [
            "<skill 1>",
            "<skill 2>",
            ...
        ],
        "description": "<a concise and professional description summarizing the role, responsibilities, and qualifications>"
    }}
}}

Your job:
- Extract relevant details from the user input.
- If any data is missing, infer it reasonably based on context.
- Ensure the **description** field is written in a formal tone, combining the job overview, key responsibilities, and qualifications into a coherent paragraph.
- Format all fields according to their type (e.g., list for `skill`, string for `job_title`, `location`, `description`).
"""

def filter_candidate(skill):
    data_candidate = get_candidate_data_json(skill)
    prompt = f"""
You are a recruitment assistant AI.

You will receive:
- A natural language job requirement description from the user
- A list of candidate data in JSON format

Your task is to:
1. Understand the user’s job requirement description.
2. Filter and return only candidates who match the requirement.
3. Base your filtering on:
   - The job description
   - The structured user criteria provided below
   - The candidate's skills, experience, and education
4. Only include up to 10 best-matching candidates in the result

Use this matching logic:
- Match keywords in required skills (partial match is acceptable, e.g., "python" matches "Strong skills in Python")
- Match minimum years of experience if stated
- Match minimum education level if stated
- Consider relevance of experience area (e.g., machine learning for AI job)

Your response must strictly follow this JSON structure:
{{
    "message": "<brief explanation of how many candidates matched and why>",
    "is_show_data": true,
    "need_input": false,
    "data": [
        {{
            "user_id":"<candidate user_id>"
            "name": "<full name>",
            "education": "<describe education background>",
            "experience_years": <describe experience number of years>,
            "skills": "<describe skill candidate>",
            "phone":"<phone number candidate>"
            "linkedin_url":"<linkedin profile  candidate>"
        }}
    ]
    
}}


Here is the list of candidate data:
{data_candidate}
"""
    return prompt

    
def recommend_candidate():
    prompt = f"""
You are an intelligent recruitment assistant AI.

Your task is to recommend the most suitable candidates based on a given job requirement.

You will receive:
- A job requirement description (from the user)
- A list of candidate profiles in JSON format

Instructions:
1. Evaluate each candidate based on job title, skills, experience, and qualifications.
2. Assign a match score from 0 to 100 for each candidate.
3. Recommend only candidates with a score of 70 or above.
4. For each recommended candidate, provide:
   - name
   - score
   - brief reason for recommendation

Respond ONLY in this JSON format:
{{
  "message": "<summary of how many candidates matched>",
  "is_show_data":true,
  "need_input":false,
  "step":"generate",
  "data": [
    {{
      "user_id":"<candidate user_id>"
      "first_name": "<candidate first name>",
      "last_name": "<candidate last name>",
      "email":"<candidate email>",
      "position":"<job position>",
      "score": <match score>,
      "reason": "<short explanation>"
    }},
    ...
  ]
}}

"""
    return prompt
async def agent_hr(message):
    print(message)
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )
    generate_agent = Agent(
        name="requirements_agent",
        model="gemini-2.5-pro-preview-05-06", # Can be a string for Gemini or a LiteLlm object
        description="Provides job requirementes.",
        instruction=generate_requirement(),
        generate_content_config=generate_content_config
    )
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="requirements_agent",
        user_id="USER_ID",
        session_id="SESSION_ID"
    )
    runner = Runner(
        agent=generate_agent, # The agent we want to run
        app_name="requirements_agent",   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    content = types.Content(role='user', parts=[types.Part(text=message)])
    final_response_text = "Agent did not produce a final response." # Default
    async for event in runner.run_async(user_id="USER_ID", session_id="SESSION_ID", new_message=content):
        if event.is_final_response():
          print(event.content.parts)
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break
    print(final_response_text)
    res = json.loads(final_response_text)
    res['pipeline'] = pipeline()
    print(res)
    return res

async def agent_filter(criteria):
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )
    requirements = json.loads(criteria)
    skill = requirements['skill']
    
    prompts =  filter_candidate(skill)
    
    generate_agent = Agent(
        name="filter_candidate_agent",
        model="gemini-2.5-pro-preview-05-06", # Can be a string for Gemini or a LiteLlm object
        description="Provides job requirementes.",
        instruction=prompts,
        generate_content_config=generate_content_config
    )
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="filter_candidate_agent",
        user_id="USER_ID",
        session_id="SESSION_ID"
    )
    runner = Runner(
        agent=generate_agent, # The agent we want to run
        app_name="filter_candidate_agent",   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    content = types.Content(role='user', parts=[types.Part(text=criteria)])
    final_response_text = "Agent did not produce a final response." # Default
    async for event in runner.run_async(user_id="USER_ID", session_id="SESSION_ID", new_message=content):
        if event.is_final_response():
          print(event.content.parts)
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break
    return json.loads(final_response_text)
    # return []
async def agent_recommendation(criteria,candidate):
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )
    generate_agent = Agent(
        name="filter_candidate_agent",
        model="gemini-2.5-pro-preview-05-06", # Can be a string for Gemini or a LiteLlm object
        description="Provides job requirementes.",
        instruction=recommend_candidate(),
        generate_content_config=generate_content_config
    )
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="filter_candidate_agent",
        user_id="USER_ID",
        session_id="SESSION_ID"
    )
    runner = Runner(
        agent=generate_agent, # The agent we want to run
        app_name="filter_candidate_agent",   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    content = types.Content(role='user', parts=[types.Part(text=criteria),types.Part(text=candidate)])
    final_response_text = "Agent did not produce a final response." # Default
    async for event in runner.run_async(user_id="USER_ID", session_id="SESSION_ID", new_message=content):
        if event.is_final_response():
          print(event.content.parts)
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break
    return json.loads(final_response_text)