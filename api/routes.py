from fastapi import APIRouter, HTTPException, BackgroundTasks,UploadFile, File, Form, Request
from pydantic import BaseModel
from controller.apps import run,process_candidate
from utils.redis_client import set_value,get_value
import json
import base64
from ai.recruiter import extracted_cv,next_recruiter_agent
from utils.vector_store import search_vector_db
from utils.get_data import get_candidate_data_json
from typing import Any, Dict

router = APIRouter()
class UpdateRequest(BaseModel):
    step: str
    data: Dict[str, Any]
    key: str

class GenerateRequest(BaseModel):
    text: str
    key:str

def recruiter_wrapper(data,step,key):
    try:
        next_recruiter_agent(data,step,key)
    except Exception as e:
        print(f"[recruiter_agent error] {str(e)}")

@router.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}
@router.post("/update")
async def update_process(
    request: UpdateRequest,
    background_tasks: BackgroundTasks = None,
):
    print(request)
    background_tasks.add_task(recruiter_wrapper, request.data,request.step,request.key)
    # await next_recruiter_agent(request.data,request.step,request.key)
    return {"status":"success"}
@router.post("/generate")
async def generate_route(
    text: str = Form(...),
    key: str = Form(...),
    background_tasks: BackgroundTasks = None,
    files: list[UploadFile] = File(None)
):
    try:
        base64_files = []
        # if not files:
        #     raise HTTPException(status_code=400, detail="No files uploaded.")
        if files:
            print("files")
            for file in files:
                content = await file.read()
                encoded = base64.b64encode(content).decode("utf-8")
                base64_files.append({
                    "mime_type":"application/pdf",
                    "content_base64": encoded
                })
        # print("files",base64_files)
        # res = await extracted_cv(base64_files)
        result = run(text, background_tasks, key,base64_files)
        return {"result":result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/candidate")
async def candidate_endpoint(request: Request):
    body = await request.json()
    data = body.get("data")

    if not data:
        return {"error": "Missing 'data' in payload"}

    result = process_candidate(data)
    return {"status": "ok", "vector_id": result}
@router.post("/candidate/search")
async def search_candidate(request: Request):
    body = await request.json()
    query = body.get("query")

    if not query:
        return {"error": "Missing 'query' in payload"}

    results = search_vector_db(query)
    return {"results": results}
@router.get("/set")
def set_data(key: str, value: str):
    set_value(key, value)
    return {"message": f"{key} disimpan"}

@router.get("/get")
def get_data(key: str):
    value = get_value(key)
    return {"key": key, "value": json.loads(value)}

@router.get('/get-candidate')
def get_candidate():
    data = get_candidate_data_json()
    data_json = json.loads(data)
    filename = f"candidates_.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)
    return {"status":"OK"}