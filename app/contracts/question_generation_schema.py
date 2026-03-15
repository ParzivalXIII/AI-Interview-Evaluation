from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    text: str = Field(min_length=1)
    type: str | None = None


class QuestionGenerationOutput(BaseModel):
    questions: list[GeneratedQuestion]
