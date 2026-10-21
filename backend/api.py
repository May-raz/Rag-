from fastapi import FastAPI
from pydantic import BaseModel
from rag import ask

app = FastAPI()

class Question(BaseModel):
    question: str

@app.post("/ask")
def ask_endpoint(body:Question):
    return ask(body.question) 