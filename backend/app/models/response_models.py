from pydantic import BaseModel
from typing import List


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]