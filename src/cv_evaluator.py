import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

chat = ChatOpenAI(temperature=0.3, model="gpt-4o")


@traceable(name="Evaluate CV Quality")
def evaluate_cv_quality(cv_text: str) -> dict:
    with open("prompts/evaluate_cv_prompt.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.format(cv_text=cv_text)


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
