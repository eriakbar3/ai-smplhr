from fastapi import BackgroundTasks
from ai.ai import generate
from ai.recruiter import recruiter_agent
from utils.vector_store import store_to_vector_db
from utils.redis_client import set_value
import json

async def recruiter_wrapper(text: str,key:str,file,pipeline):
    try:
        await recruiter_agent(text,key,file,pipeline)
    except Exception as e:
        print(f"[recruiter_agent error] {str(e)}")

def run(text: str, background_tasks: BackgroundTasks,key,file):
    print(f"📝 Input: {text}")
    try:
        result = generate(text)
        print(result)
        result_str = json.dumps(result)
        init_data = {
            "status":"running",
            "data":[result],
            "step":"finding_agent",
            "pipeline":result['pipeline'],
            "agent":result.get('agent')
        }
        set_value(key,json.dumps(init_data))
        if result.get('agent') == 'recruiter':
            background_tasks.add_task(recruiter_wrapper, text,key,file,result['pipeline'])

        return {
            "result": result,
            "recruiter_agent": "executed" if result.get('agent') == 'recruiter' else "skipped"
        }
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {str(e)}")
        raise e



def process_candidate(data: dict):
    if "id" not in data:
        raise ValueError("Missing 'id' in data")

    vector_id = data["id"]
    content = "\n".join([f"{k}: {v}" for k, v in data.items() if k != "id"])

    return store_to_vector_db(vector_id, content)
