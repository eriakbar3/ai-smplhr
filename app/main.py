from fastapi import FastAPI
from api import routes

app = FastAPI()

# Routing
app.include_router(routes.router)
