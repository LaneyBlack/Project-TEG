import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

chat = ChatOpenAI(temperature=0.3, model="gpt-4o")


@traceable(name="Evaluate CV Quality")
def evaluate_cv_quality(cv_text: str) -> dict:
    prompt = f"""
    You are an expert in recruitment and professional writing. Please analyze the following CV for:

    - Language accuracy (spelling, grammar, punctuation),
    - Style and professionalism of writing,
    - Structure and clarity,
    - Length and relevance of the information.

    For each section of the CV, provide:
    - Identified issues (if any),
    - What exactly should be improved,
    - A suggested improved version (if applicable).

    Finally, give an overall evaluation score on a scale from **0 to 10**:
    - 0 = completely needs rewriting,
    - 10 = perfect, no changes needed.

    CV to analyze:
    ---
    {cv_text}
    ---
    """

    messages = [
        SystemMessage(content="You are a professional recruiter and language expert."),
        HumanMessage(content=prompt)
    ]

    response = chat.invoke(messages)
    response_text = response.content

    match = re.search(r"\b(?:score|rating)\b[^0-9]*(\d{1,2})\b", response_text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        score = min(score, 10)
    else:
        score = None

    return {
        "score": score,
        "details": response_text
    }
