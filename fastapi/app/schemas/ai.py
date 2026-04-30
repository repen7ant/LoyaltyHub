from pydantic import BaseModel


class AIRecommendation(BaseModel):
    recommendation: str
