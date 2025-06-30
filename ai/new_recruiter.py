from google import genai
from google.genai import types
import json
from utils.redis_client import get_value,set_value
from utils.get_data import get_candidate_data_json
import base64
import traceback
from typing import List, Dict
from ai.agent_hr import agent_filter,agent_recommendation,agent_extract_cv
from ai.recruiter import extracted_cv
from dotenv import load_dotenv
from utils.get_data import get_candidate_data_json

import os
load_dotenv()

async def run_filter(data,key,candidate):
    print(data)
    if(len(candidate) == 0):
        requirements = json.loads(data)
        skill = requirements['skill']
        data_candidate = get_candidate_data_json(skill)
    else:
        data_candidate = candidate
    res = await agent_filter(data,data_candidate)
    print("starting:filter")
    print("starting key :",key)
    res['step'] = "filter"
    get_old = get_value(key)
    old_json = json.loads(get_old)
    old_json['data'].append(res)
    [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == "filter"]
    new_value = json.dumps(old_json)
    set_value(key, new_value)
    print("Filtered candidates:", res)
    return res
async def run_recommend(data,key,candidate_data):
    print("starting:recommend")

    print("starting key :",key)
    res = await agent_recommendation(candidate_data, data)
    res['step'] = "recommend"
    
    get_old = get_value(key)
    old_json = json.loads(get_old)
    old_json['data'].append(res)
    old_json['status'] = "Stopped"
    [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == "recommend"]
    new_value = json.dumps(old_json)
    set_value(key, new_value)

    print("Recommendations:", res)
async def next_recruiter_agent(data,step,key):
    get_file = get_value(key+'-file')
    # print(get_file)
    # print("tooooo")
    files_data = json.loads(get_file)
    candidate = []
    if isinstance(files_data, dict) and 'files' in files_data and files_data['files']:
        print(files_data["files"])
        result = await extracted_cv(files_data['files'])
        print(result)
        candidate = result
    if step == 'generate':
        res_filter = await run_filter(json.dumps(data),key,candidate)
        res_recommend = await run_recommend(json.dumps(data),key,json.dumps(res_filter))
    
    if step == 'filter':
        get_old = get_value(key)
        old_json = json.loads(get_old)
        filtered_data = [item for item in data if item['step'] == 'filter']
        generate_data = [item for item in data if item['step'] == 'generate']
        res_recommend = await run_recommend(json.dumps(generate_data),step,key,json.dumps(filtered_data))
