from fastapi import APIRouter, HTTPException, BackgroundTasks,UploadFile, File, Form
from pydantic import BaseModel
from controller.apps import run
from utils.redis_client import set_value,get_value
import json
import base64
from ai.recruiter import extracted_cv,next_recruiter_agent
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
@router.get("/set")
def set_data(key: str, value: str):
    set_value(key, value)
    return {"message": f"{key} disimpan"}

@router.get("/get")
def get_data(key: str):
    value = get_value(key)
    return {"key": key, "value": json.loads(value)}