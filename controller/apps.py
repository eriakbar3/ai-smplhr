from fastapi import BackgroundTasks
from ai.ai import generate
from ai.recruiter import recruiter_agent
from ai.agent_hr import agent_hr
from utils.vector_store import store_to_vector_db
from utils.redis_client import set_value
import json

async def recruiter_wrapper(text: str,key:str,file,pipeline):
    try:
        await recruiter_agent(text,key,file,pipeline)
    except Exception as e:
        print(f"[recruiter_agent error] {str(e)}")

async def run(text: str, key,files):
    print(f"📝 Input: {text}")
    try:
        result = await agent_hr(text)
        print(result)
        result['pipeline'][0]['is_done'] = True
        init_data = {
            "status":"running",
            "data":[result],
            "step":"generate",
            "pipeline":result['pipeline'],
            "agent":"recruiter",
        }
        files_data = {
            "files":files
        }
        set_value(key+'-file',json.dumps(files_data))
        set_value(key,json.dumps(init_data))
        return result
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {str(e)}")
        raise e



def process_candidate(data: dict):
    if "id" not in data:
        raise ValueError("Missing 'id' in data")

    vector_id = data["id"]
    content = "\n".join([f"{k}: {v}" for k, v in data.items() if k != "id"])

    return store_to_vector_db(vector_id, content)
