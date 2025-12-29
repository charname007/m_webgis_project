from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class QueryResponse(BaseModel):
    result: list[Message]
    


