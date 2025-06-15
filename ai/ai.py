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
    try:
        client = genai.Client(
            vertexai=True,
            project="smplhr",
            location="us-central1",
        )

        prompt = f"""You are a smart AI router and task executor that determines the most appropriate agent to handle a user's question based on their role, and then processes the request accordingly.

Agent List:
1. supervisor – handles escalated issues, decision-making, and team oversight
2. recruiter – handles recruitment-related inquiries, job applications, and interviews
3. people ops – handles HR matters, employee relations, and onboarding/offboarding
4. payroll – handles salary, compensation, benefits, and payment-related issues
5. manager – handles general management, performance reviews, and project assignments

Your Tasks:
1. Analyze the user's input and route it to the most suitable agent from the list above.
2. Respond with a JSON containing:
   - The selected agent
   - A brief explanation why the agent was chosen
   - A welcome message from the agent
   - The input language
3. **If the selected agent is "recruiter"**, then:
   - Analyze the user's input to generate a structured recruitment pipeline.
   - The pipeline may include steps like generating requirements, screening, recommending, scheduling, assessing, and offering.
   - If no clear job title is found, respond with a message asking the user to clarify.

Constraints:
- Do not ask unnecessary follow-up questions.
- Identify language automatically (you may use simple rules like checking if input is in English or Indonesian).

Respond strictly in this JSON format:

```json
{{
  "agent": "<name of the selected agent>",
  "reason": "<brief explanation why this agent was selected>",
  "message": "<welcome message from the agent>",
  "language": "<detected language>",
  "pipeline": [
    {{
      "step": 1,
      "type": "<action_type e.g. generate (generate reqruitement), screening (screening candidate), recommend (candidate recomendation), schedule (schedule interview), assess (assesment), and offer (offering)>", 
      "message": "<direct message to user about what will be done>",
      "is_done": false,
      "title": "<process title>"
    }}
    // ...additional steps if applicable
  ] // If not recruiter, set this to []
}}
User input:
"{question}"
"""


        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]

        model = "gemini-2.5-flash-preview-05-20"
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=genai.types.ThinkingConfig(thinking_budget=1024)
        )

        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=generate_content_config,
        )
        response_json = json.loads(response.text)
        
        return response_json
    except Exception as e:
        print("terjadi kesalahan pada saat generate",e)

# generate("carikan saya kandidat software engineer")