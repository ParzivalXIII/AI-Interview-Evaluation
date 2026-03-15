from enum import StrEnum


class Difficulty(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class SessionStatus(StrEnum):
    READY = "ready"
    FAILED = "failed"
    COMPLETED = "completed"


class AnswerStatus(StrEnum):
    PENDING_EVALUATION = "pending_evaluation"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


class JobType(StrEnum):
    ANSWER_EVALUATION = "answer_evaluation"


DEFAULT_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 10
MIN_QUESTION_COUNT = 1

EVALUATION_QUEUE_NAME = "arq:evaluation"
