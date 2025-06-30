from utils.get_data import get_candidate_data_json
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from utils.init_pipeline import pipeline
import json
import base64
def generate_requirement():
    return """
You are an AI Recruiter Agent that processes natural language input from a user (e.g., "I need a software engineer in Jakarta") and returns a structured recruitment response in **strict JSON format**.

Your tasks:
1. Extract and generate a professional **Job Description** from the user's input.
2. Build a step-by-step **Recruitment Pipeline** tailored to that job.

---

### Response Format (must strictly follow this structure):
{
    "message": "<Provide a polite and professional summary of the extracted job>",
    "is_show_data": true,
    "need_input": false,
    "step":"generate",
    "data": {{
        "job_title": "<extracted or inferred job title>",
        "location": "<location if available, otherwise empty string>",
        "salary": <salary as number if available, otherwise null>,
        "skill": [
            "<skill 1>",
            "<skill 2>",
            ...
        ],
        "description": "<Formal summary of the role, responsibilities, and qualifications>"
    },
    "pipeline": [
    {
      "step": 1,
      "type": "<action_type>",  // e.g., "generate", "filter", "recommend", "schedule", "assess", "offer"
      "message": "<Direct message to user about what we will do in this step>",
      "is_done": false,
      "title": "<title of the process>"
    },
    ...
  ]
  },
}

---

### Rules:
- For job description:
  - Extract all relevant data (job title, location, salary, required skills).
  - If some fields are missing, infer if possible or leave as empty/null.
  - Description must be written in a formal and concise tone.
  - Description must detail & clear
  - **Description must include (when possible)**:
    - **Key Responsibilities**
    - **Required Skills or Qualifications**
    - **Preferred Qualifications**
    - **Experience Level**

- For recruitment pipeline:
  - Always start with `generate` step.
  - If screening is implied or mentioned, include `screening` step after generate.
  - If scheduling is required, prompt user for date details.
  - Continue with recommend → assess → offer as needed.

"""


def filter_candidate(data_candidate):
    
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
def extract_cv():
   return """
You are an AI extractor tasked with reading and extracting structured information from CVs in **PDF format**. Your goal is to accurately identify and return key personal and professional details from the document.

### Extract the following information:

1. Full name  
2. Address  
3. Email  
4. Phone number  
5. Date of birth (if available)  
6. Education (institution name, major, start year, end year)  
7. Work experience (position, company name, employment period, short description)  
8. Skills  
9. Certifications or training  
10. Languages spoken  
11. Notable projects (project name, description, role)  
12. Links (LinkedIn, GitHub, portfolio – if available)

---

### Output Format:
Return the extracted data in the following strict JSON structure:

```json
{
  "name": "",
  "address": "",
  "email": "",
  "phone": "",
  "birth_date": "",
  "education": [
    {
      "institution": "",
      "major": "",
      "year_in": "",
      "year_out": ""
    }
  ],
  "work_experience": [
    {
      "position": "",
      "company": "",
      "period": "",
      "description": ""
    }
  ],
  "skills": [],
  "certifications": [],
  "languages": [],
  "projects": [
    {
      "name": "",
      "description": "",
      "role": ""
    }
  ],
  "links": {
    "linkedin": "",
    "github": "",
    "portfolio": ""
  },
  "additional_data": {}
}
"""
async def agent_extract_cv(files):
   result = []
   for file in files :
      data_file = types.Part.from_bytes(
                    data=base64.b64decode(file['content_base64']),
                    mime_type=file['mime_type']
                )
      generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            )
      generate_agent = Agent(
            name="requirements_agent",
            model="gemini-2.5-pro-preview-05-06", # Can be a string for Gemini or a LiteLlm object
            description="Provides job requirementes.",
            instruction=extract_cv(),
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
            session_service=session_service
        )
      content = types.Content(role='user', parts=[data_file])
      async for event in runner.run_async(user_id="USER_ID", session_id="SESSION_ID", new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break
        print(final_response_text)
        res = json.loads(final_response_text)
        result.append(res)
   return result

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
    print(res)
    return res

async def agent_filter(criteria,data_candidate):
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )
    requirements = json.loads(criteria)
    skill = requirements['skill']
    
    prompts =  filter_candidate(data_candidate)
    
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
        print("filter response",final_response_text)
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
        print("recommend response",final_response_text)
    return json.loads(final_response_text)