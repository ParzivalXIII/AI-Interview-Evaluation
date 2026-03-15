from langchain_core.prompts import ChatPromptTemplate

QUESTION_GENERATION_PROMPT_VERSION = "v1"

QUESTION_GENERATION_SYSTEM = (
    "You are an expert technical interviewer. Generate exactly {count} interview questions "
    "for a {difficulty} level {role} candidate. "
    "Return ONLY a JSON object with a 'questions' array. Each element must have: "
    "'text' (the question string) and 'type' (one of: coding, system_design, behavioral_technical, "
    "general_technical). No markdown, no explanation — only the JSON object."
)

QUESTION_GENERATION_HUMAN = (
    "Generate {count} interview questions for a {difficulty} {role} position."
)

question_generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", QUESTION_GENERATION_SYSTEM),
        ("human", QUESTION_GENERATION_HUMAN),
    ]
)

EVALUATION_PROMPT_VERSION = "v1"
RUBRIC_VERSION = "v1"

EVALUATION_SYSTEM = (
    "You are a senior technical interviewer evaluating a candidate's answer. "
    "Score the answer from 0 to 10 and provide structured feedback. "
    "Return ONLY a JSON object with the following fields: "
    "'score' (float 0-10), 'feedback' (string), 'strengths' (array of strings), "
    "'improvements' (array of strings). No markdown, no explanation — only the JSON object."
)

EVALUATION_HUMAN = (
    "Role: {role}\n"
    "Difficulty: {difficulty}\n"
    "Question: {question_text}\n"
    "Candidate Answer: {answer_text}\n\n"
    "Evaluate the answer according to the rubric."
)

evaluation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EVALUATION_SYSTEM),
        ("human", EVALUATION_HUMAN),
    ]
)
