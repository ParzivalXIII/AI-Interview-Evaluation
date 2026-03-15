from app.core.config import settings

RUBRIC_VERSION = settings.rubric_version

ANSWER_EVALUATION_RUBRIC = {
    "version": RUBRIC_VERSION,
    "score_range": [0, 10],
    "criteria": [
        "Technical correctness",
        "Depth and completeness",
        "Communication clarity",
        "Relevant examples or experience",
    ],
    "scoring_guide": {
        "9-10": "Exceptional — exceeds role expectations",
        "7-8": "Strong — meets expectations with good depth",
        "5-6": "Adequate — partial answer with some gaps",
        "3-4": "Weak — significant gaps or misconceptions",
        "0-2": "Insufficient — incorrect or irrelevant",
    },
}
