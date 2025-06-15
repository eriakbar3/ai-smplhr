from google import genai
from google.genai import types
import json
from utils.redis_client import get_value,set_value
from utils.get_data import get_candidate_data_json
import base64
import traceback
from typing import List, Dict
from dotenv import load_dotenv
import os
load_dotenv()
# genai.configure(api_key=os.getenv("GENAI_API_KEY"))
print(os.getenv("GENAI_API_KEY"))
key = os.getenv("GENAI_API_KEY")
client = genai.Client(
        vertexai=True,
        project="smplhr",
        location="us-central1",
    )


def recruiter_agent(message, key, file):
    try:
        # print("Agent Recruiter : Hi there! 👋 You’re now chatting with our recruiter agent. Let’s find the best candidates together!")

        # Generate pipeline dari pesan pengguna
        pipeline = generate_pipeline(message)
        print("Pipeline generated:", pipeline)

        # Ambil data lama dari key
        get_old = get_value(key)
        old_json = json.loads(get_old)

        # Tambahkan pipeline ke histori
        # old_json['data'].append(pipeline)
        # old_json['step'] = 'generate_pipeline'
        old_json['pipeline'] = pipeline.get('pipeline', [])
        new_value = json.dumps(old_json)
        set_value(key, new_value)

        # Inisialisasi variabel
        candidate_requirement = ''
        candidate_filter = []
        screening_file = []

        # Proses file jika ada
        print("file:", file)
        if len(file) > 0:
            print("extracting...")
            res = extracted_cv(file)
            screening_file = res
            data_progress = {
                "data": screening_file,
                "message": "Just a moment! I'm working on extracting your data."
            }
            # Simpan hasil ekstraksi ke histori
            get_old = get_value(key)
            old_json = json.loads(get_old)
            old_json['data'].append(data_progress)
            old_json['type'] = "extracting_data"
            new_value = json.dumps(old_json)
            set_value(key, new_value)

        # Jalankan setiap langkah pipeline
        for data in pipeline.get('pipeline', []):
            print("Step type:", data['type'])
            print("Agent Recruiter:", data['message'])
            

            # Step: generate
            if data['type'] == 'generate':
                print("starting:", data['type'])
                candidate_requirement = generate_requirement(message)
                data_res = candidate_requirement
                data_res['step'] = data['type']
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append(data_res)
                old_json['requirement']=candidate_requirement
                [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == data['type']]
                new_value = json.dumps(old_json)
                set_value(key, new_value)

                print("Agent Recruiter:", candidate_requirement)

            # Step: filter
            if data["type"] == 'filter':
                print("starting:", data['type'])
                res = filter_candidate(candidate_requirement)
                res['step'] = data['type']
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append(res)
                [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == data['type']]
                new_value = json.dumps(old_json)
                
                set_value(key, new_value)
                
                candidate_filter = res.get('data', [])
                print("Filtered candidates:", res)

            # Step: recommend
            if data["type"] == 'recommend':
                print("starting:", data['type'])

                candidate_data = screening_file if screening_file else candidate_filter
                res = recommend_candidate(candidate_data, candidate_requirement)
                res['step'] = data['type']
                
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append(res)
                old_json['status'] = "Stopped"
                [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == data['type']]
                new_value = json.dumps(old_json)
                set_value(key, new_value)

                print("Recommendations:", res)
            if data["type"] == 'screening':
                print("starting:", data['type'])

                candidate_data = screening_file if screening_file else candidate_filter
                res = screening_candidate(candidate_data, candidate_requirement)
                
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append({"is_show_data": True, "need_input":False,"message": "Berikut data kandidat yang sudah melalui tahap screening:", "data": res,"step":data['type']})
                [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == data['type']]
                new_value = json.dumps(old_json)
                set_value(key, new_value)

                print("result sccreening:", res)

    except Exception as e:
        print("❌ Error in recruiter_agent:", e)
        traceback.print_exc()
def continue_from_user_input(pipeline: List[Dict], user_type: str) -> List[Dict]:
    result = []
    found = False
    for step in pipeline:
        if step['type'] == user_type:
            found = True
        if found:
            result.append(step)
    return result        
def next_recruiter_agent(data,step,key):
    get_old = get_value(key)
    redis_data = json.loads(get_old)
    pipeline = redis_data['pipeline']
    if step != 'offer':
        steps_to_execute = continue_from_user_input(pipeline,step)
        for st in steps_to_execute:
            print(f"Step {st['step']} - Type: {st['type']}")
            print(f"Message:s {st['message']}\n")
            if st['type'] == "schedule":
                res = generate_schedule(data)
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append({"message":"Berikut adalah data kandidat yang telah dijadwalkan untuk interview:","data":res,"is_show_data":True,"is_need_input":False})
                old_json['step'] = st['type']
                new_value = json.dumps(old_json)
                set_value(key, new_value)
            if st['type'] == "assess":
                res = generate_assessments(redis_data['requirement'])
                get_old = get_value(key)
                old_json = json.loads(get_old)
                old_json['data'].append(res)
                old_json['step'] = st["type"]
                new_value = json.dumps(old_json)
                set_value(key, new_value)
    else:
        res = generate_offer(data)
        get_old = get_value(key)
        old_json = json.loads(get_old)
        old_json['data'].append(res)
        old_json['step'] = st["type"]
        new_value = json.dumps(old_json)
        set_value(key, new_value)

def generate_pipeline(message):
    prompt = f"""
You are an AI Recruiter Agent that processes natural language input from a user (e.g., "I need a software engineer") and returns a structured recruitment pipeline in JSON format.

Your responsibilities include:
- Generate requirements
- Finding candidates
- Recommending matches
- Scheduling interviews required
- Sending assessments required
- Sending offer letters required
- Screening if user input screening data


Your response must follow this strict JSON structure:

{{
  "pipeline": [
    {{
      "step": 1,
      "type": "<action_type>",  // e.g., "generate", "filter", "screening","recommend", "schedule", "assess", "offer"
      "message":"<direct message to user what will we do>",
      "is_done":false,
      "title":"<title proses>"
    }},
    ...
  ]
}}
notes : 
- if screening pipeline must be generate,screening
- if schedule ask to user for detail date
If the job title is not clearly mentioned in the user input, return a clarification message instead of the JSON pipeline.

Now respond based on this user input:
"{message}"
"""
    
    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    response_json = json.loads(response.text)
    return response_json

def generate_requirement(message):
    prompt = f"""
You are a highly intelligent Recruitment Assistant AI. Your task is to create a clear and structured **Job Description** based on the user's input.

Your output **must strictly follow this JSON Format**:
{{
    "message": "<Provide a polite and professional message to the user summarizing the extracted job details>",
    "is_show_data": true,
    "need_input": false,
    "data": "<Formatted Job Description in bullet points>"
}}

For the **data** field, follow this structure (use bullet points for each section):
- **Job Title**: (extracted or inferred)
- **Employment Type**: (e.g., Full-time, Part-time, Contract, Internship; make a reasonable guess if missing)
- **Experience Level**: (e.g., Entry-level, Mid-level, Senior; make a reasonable guess if missing)
- **Key Responsibilities**:
  - (list responsibilities in bullet points)
- **Required Skills or Qualifications**:
  - (list must-have skills in bullet points)
- **Preferred Qualifications**:
  - (list nice-to-have skills in bullet points)

    If some information is missing, **infer it logically based on the context** and ensure the output is complete, professional, and easy to understand.

Here’s the user’s input:
\"{message}\"
"""

    try:
        model = "gemini-2.5-pro-preview-05-06"
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            }
        )
        print(response.text)
        if hasattr(response, "text") and isinstance(response.text, str):
            response_json = json.loads(response.text)
            return response_json
        else:
            return "⚠️ Sorry, I couldn't generate a valid response."
    except Exception as e:
        print("❌ generate_requirement ERROR:", e)
        return f"Error generating requirement: {str(e)}"
    
def load_candidates(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
def filter_candidate(criteria):
    data_candidate = get_candidate_data_json()
    print(data_candidate)
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
   - The candidate's skills, experience, and position
4. max candidate filtered is 10
Your response must strictly follow this JSON structure:
{{
  "message": "<brief explanation of the result, e.g., how many candidates found>",
  "is_show_data":true,
  "need_input":false,
  "data": [<list of filtered candidate objects>]
}}
User's job requirement description:
"{criteria}"

Here is the list of candidate data:
```json
{data_candidate}
"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    print(response.text)
    response_json = json.loads(response.text)
    return response_json

def recommend_candidate(candidate,requirement):
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

Job Requirement:
\"\"\"{requirement}\"\"\"

Candidate List:
```json
{json.dumps(candidate, indent=2)}
"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    response_json = json.loads(response.text)
    return response_json

def extracted_cv(files):
    model = "gemini-2.5-pro-preview-05-06"
    text1 = types.Part.from_text(text="""You are an AI extractor tasked with reading and extracting structured information from all CV in PDF format. Extract the following key details accurately:

1. Full name  
2. Address  
3. Email  
4. Phone number  
5. Date of birth (if available)  
6. Education (institution name, major, start and end year)  
7. Work experience (position, company name, period of employment, short description)  
8. Skills  
9. Certifications or training  
10. Languages spoken  
11. Notable projects (project name, description, role)  
12. Links (LinkedIn, GitHub, portfolio, if available)

Return the result in the following JSON format:

```json
{{
 \"name\": \"\",
 \"address\": \"\",
 \"email\": \"\",
 \"phone\": \"\",
 \"birth_date\": \"\",
 \"education\": [
  {
   \"institution\": \"\",
   \"major\": \"\",
   \"year_in\": \"\",
   \"year_out\": \"\"
  }
 ],
 \"work_experience\": [
  {
   \"position\": \"\",
   \"company\": \"\",
   \"period\": \"\",
   \"description\": \"\"
  }
 ],
 \"skills\": [],
 \"certifications\": [],
 \"languages\": [],
 \"projects\": [
  {
   \"name\": \"\",
   \"description\": \"\",
   \"role\": \"\"
  }
 ],
 \"links\": {
  \"linkedin\": \"\",
  \"github\": \"\",
  \"portfolio\": \"\"
 }
\"additional_data\":{}
}}""")
    result = []
    for file in files :
        part_data = [text1]
        data_file = types.Part.from_bytes(
            data=base64.b64decode(file['content_base64']),
            mime_type=file['mime_type']
        )
        part_data.append(data_file)
        contents = [
            types.Content(
            role="user",
            parts=part_data
            ),
        ]
        client = genai.Client(
            vertexai=True,
            project="smplhr",
            location="us-central1",
        )
        response =  client.models.generate_content(
            model=model,
            contents=contents,
            config={
                "response_mime_type": "application/json",
            },
        )
        result.append(json.loads(response.text))
    # print(response.text)
    return result

def screening_candidate(data_candidate,requirement):
    prompt = f"""
You are an AI recruiter assistant. You will receive:
1. A list of candidate data in JSON format
2. A job requirement description in natural language

Your task is to evaluate each candidate's suitability for the job and assign a numeric score from 0 to 100 based on relevance. Return a new list where each candidate object is extended with a `score` key.

Guidelines:
- Score should reflect how closely the candidate matches the job requirement.
- Consider skills, job titles, years of experience, education, and relevant projects.
- Do not change the original candidate data. Only add the `score` key.
- Provide a brief reason for each score in a `reason` field.

Format your response as a JSON array like this:

[
  {{
    "full_name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "React", "SQL"],
    "experience": 3,
    "score": 85,
    "reason": "Strong match with required skills and relevant experience."
  }},
  ...
]

Begin screening using the following:

Job Requirement:
\"\"\"
{requirement}
\"\"\"

Candidate List:
```json
{data_candidate}
"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    print(response.text)
    response_json = json.loads(response.text)
    return response_json

def generate_schedule(data):
    prompt=f"""
You are an AI assistant tasked with generating a professional job interview invitation email.

You will be given the following parameters:
{data}

Your task is to create a polite, professional, and friendly interview invitation email.

Your response must be formatted as a JSON object with the following structure:
[{{
  "subject": "string",      // A concise and relevant email subject line
  "body": "string"          // The email body text, personalized with the candidate's name and details
  "name":"string"   // candidate name
  "email":"string" // candidate email
}}]

Guidelines:
- The subject should clearly mention the interview and position.
- The body should greet the candidate by name, confirm the position applied for, mention the scheduled date/time, and include a polite closing.
- Do not include any HTML or markdown.

Example parameters:
name: <candidate name>  
Email: <candidate email>  
Position: <position>  
Date: <date>

Generate the JSON output.

"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    print(response.text)
    response_json = json.loads(response.text)
    return response_json

def generate_assessments(requirement):
    prompt=f"""
You are an AI assessment generator. Your task is to create a customized job assessment based on a given job requirement.

Job Requirement:
    {requirement}

Output:
- A JSON object containing the assessment details with the following format:

{{
  "title": "string",              // Title of the assessment
  "description": "string",        // Brief description of the purpose of the test
  "questions": [                  // A list of 3 to 5 relevant questions
    {{
      "question": "string",       // The assessment question
      "type": "string",           // Type of question: "multiple_choice", "open_ended", or "coding"
      "choices": ["A", "B", "C"], // (optional) Choices for multiple_choice questions
      "answer": "string"          // (optional) Expected answer (for internal use)
    }}
  ]
}}

Instructions:
- Ensure the questions are relevant to the job's required skills or responsibilities.
- If the job involves technical skills, include at least one coding or technical problem.
- The tone should be professional and neutral.
- Avoid any bias in the questions.

Example Input:
"
We are hiring a Backend Developer with experience in Python, Django, and PostgreSQL. Candidates should have a strong understanding of REST APIs, database design, and performance optimization.
"

Now, generate the assessment JSON.

"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    print(response.text)
    response_json = json.loads(response.text)
    return response_json

def generate_offer(data):
    prompt=f"""
You are an AI HR assistant. Your task is to generate a professional and personalized job offering letter using structured data provided by the user.

You will be given the following input data:
- `full_name`: Candidate's full name
- `position`: Job position being offered
- `start_date`: Proposed start date
- `salary`: Monthly or annual salary (with currency)
- `company_name`: Name of the company
- `company_address`: (optional) Company's office address
- `benefits`: (optional) List of benefits (e.g., health insurance, remote work, bonuses)

Your job is to write a clear, polite, and formal offering letter that includes:
- A warm greeting and expression of excitement
- A statement of the position being offered
- Details of the salary and start date
- Mention of any key benefits (if provided)
- Instructions on how to accept the offer or respond
- A closing statement with the company name
Input data:
    {data}
Output format must be in JSON like this:
```json
{{
  "subject": "Job Offer for [Position] at [Company Name]",
  "body": "Dear [Full Name],\n\n[Body of the offer letter with all information above]\n\nSincerely,\n[Company Name] HR Team"
}}

"""

    model = "gemini-2.5-pro-preview-05-06"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    print(response.text)
    response_json = json.loads(response.text)
    return response_json