from fastapi import FastAPI
from api import routes

app = FastAPI()
from dotenv import load_dotenv
load_dotenv()
# Routing
app.include_router(routes.router)
