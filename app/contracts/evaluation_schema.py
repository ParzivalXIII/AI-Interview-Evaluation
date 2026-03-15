from pydantic import BaseModel, Field


class EvaluationOutput(BaseModel):
    score: float = Field(ge=0, le=10)
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
