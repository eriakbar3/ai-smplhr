from google import genai
from google.genai import types
import base64
import json
import re

def convertjson(text):
    try:
        # Hilangkan ```json jika ada, lalu convert
        clean_text =text.replace("```json","")
        return clean_text
    except Exception as e:
        print("❌ Gagal parsing JSON:", e)
        return {"error": str(e), "raw": text}



def generate(question):
    client = genai.Client(
        vertexai=True,
        project="smplhr",
        location="us-central1",
    )

    prompt = f"""You are an intelligent AI router that determines the most appropriate agent to handle a user's question based on their role. Choose only one agent from the list below:

1. supervisor – handles escalated issues, decision-making, and team oversight
2. recruiter – handles recruitment-related inquiries, job applications, and interviews
3. people ops – handles HR matters, employee relations, and onboarding/offboarding
4. payroll – handles salary, compensation, benefits, and payment-related issues
5. manager – handles general management, performance reviews, and project assignments

Your task:
Based on the user's question below, identify the most relevant agent, explain your reasoning briefly, and provide a message to the user.

notes : 
- Don't ask about the details.

User question: "{question}"

Respond strictly in this JSON format:

{{
    "agent": "<name of the selected agent>",
    "reason": "<brief explanation of why this agent is the best fit>",
    "message": "<welcome & introduce message of the  selected agent>."
}}"""


    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]

    model = "gemini-2.5-pro-preview-05-06"
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
    )

    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )
    response_json = json.loads(response.text)
    
    return response_json

# generate("carikan saya kandidat software engineer")