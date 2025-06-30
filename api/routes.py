from fastapi import APIRouter, Body, HTTPException, BackgroundTasks,UploadFile, File, Form, Request
from pydantic import BaseModel
from controller.apps import run,process_candidate
from utils.redis_client import set_value,get_value
import json
import base64
from ai.recruiter import extracted_cv
from ai.new_recruiter import next_recruiter_agent
from utils.vector_store import search_vector_db
from utils.get_data import get_candidate_data_json
from typing import Any, Dict,List
from ai.agent_hr import agent_hr,agent_filter,agent_recommendation
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
import asyncio
import json
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
        print("to recruiter agent")
        asyncio.run(next_recruiter_agent(data, step, key))
        # await next_recruiter_agent(data,step,key)
        
    except Exception as e:
        print(data)
        print(f"[recruiter_agent error] {str(e)}")

@router.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}

@router.post("/agent_hr")
async def agent_ai(request: Request):
    payload = await request.json()
    print(payload)
    response = await agent_hr(payload['message'])
    return {"data":response}

@router.post("/agent_filter")
async def agent(request: Request):
    payload = await request.json()
    print(payload)
    response = await agent_filter(json.dumps(payload['data']))
    return {"data":response}




@router.post("/agent_recommend")
async def agent(
    criteria: Dict[str, Any] = Body(...),
    candidate: List[Dict[str, Any]] = Body(...)
):
    response = await agent_recommendation(
        json.dumps(criteria),
        json.dumps(candidate)
    )
    return {"data": response}


@router.post("/update")
def update_process(
    request: UpdateRequest
):
    print(request.step)
    # recruiter_wrapper(request.data, request.step, request.key)
    executor.submit(recruiter_wrapper, request.data, request.step, request.key)
    # background_tasks.add_task(recruiter_wrapper, request.data,request.step,request.key)
    # await next_recruiter_agent(request.data,request.step,request.key)
    return {"status":"success"}
@router.post("/agent")
async def agent(
    message: str = Form(...),
    key: str = Form(...),
    files: list[UploadFile] = File(None)
):
    print("run agent")
    try:
        base64_files = []
        if files:
            print('files')
            for file in files:
                content = await file.read()
                encoded = base64.b64encode(content).decode("utf-8")
                base64_files.append({
                    "mime_type":"application/pdf",
                    "content_base64": encoded
                })
        result = await run(message,  key,base64_files)
        return {"result":result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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
        result = run(text,  key)
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