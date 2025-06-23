from google import genai
from google.genai import types
import json
from utils.redis_client import get_value,set_value
from utils.get_data import get_candidate_data_json
import base64
import traceback
from typing import List, Dict
from ai.agent_hr import agent_filter,agent_recommendation
from dotenv import load_dotenv
import os
load_dotenv()

async def run_filter(data,step,key):
    res = await agent_filter(json.dumps(data))
    print("starting:", step)
    res['step'] = step
    get_old = get_value(key)
    old_json = json.loads(get_old)
    old_json['data'].append(res)
    [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == step]
    new_value = json.dumps(old_json)
    set_value(key, new_value)
    print("Filtered candidates:", res)
    return res
async def run_recommend(data,step,key,candidate_data):
    print("starting:", step)

    
    res = agent_recommendation(candidate_data, data)
    res['step'] = step
    
    get_old = get_value(key)
    old_json = json.loads(get_old)
    old_json['data'].append(res)
    old_json['status'] = "Stopped"
    [step.update({"is_done": True}) for step in old_json["pipeline"] if step["type"] == step]
    new_value = json.dumps(old_json)
    set_value(key, new_value)

    print("Recommendations:", res)
async def next_recruiter_agent(data,step,key):
    if step == 'filter':
        res_filter = await run_filter(json.dumps(data),step,key)
        res_recommend = await run_recommend(json.dumps(data),step,key,json.dumps(res_filter))
    
    if step == 'recommend':
        get_old = get_value(key)
        old_json = json.loads(get_old)
        filtered_data = [item for item in data if item['step'] == 'filter']
        generate_data = [item for item in data if item['step'] == 'generate']
        res_recommend = await run_recommend(json.dumps(generate_data),step,key,json.dumps(filtered_data))
