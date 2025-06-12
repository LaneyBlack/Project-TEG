from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable


@traceable(name="Evaluate CV Quality")
def evaluate_cv_quality(cv_text: str) -> str:
    chat = ChatOpenAI(temperature=0.3, model="gpt-4o")

    prompt = f"""
    Jesteś ekspertem ds. rekrutacji i języka. Przeanalizuj poniższe CV pod kątem:
    - poprawności językowej (pisownia, gramatyka, interpunkcja),
    - stylu i profesjonalizmu wypowiedzi,
    - struktury i klarowności,
    - długości i adekwatności informacji.

    Dla każdej sekcji CV, wypisz:
    - problemy, jeśli występują,
    - co dokładnie należy poprawić,
    - sugestię nowej, lepszej wersji (jeśli możliwe).

    CV do analizy:
    ---
    {cv_text}
    ---
    """

    messages = [
        SystemMessage(content="Jesteś profesjonalnym rekruterem i ekspertem językowym."),
        HumanMessage(content=prompt)
    ]

    response = chat.invoke(messages)
    return response.content
