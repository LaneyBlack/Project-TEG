# pip install openai langchain-core langchain-openai numpy scikit-learn python-dotenv

from dotenv import load_dotenv
import os

# 1. Załaduj zmienne środowiskowe z pliku .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY_TEG") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY_TEG lub OPENAI_API_KEY w .env")
# Ustaw też standardową zmienną dla SDK
os.environ["OPENAI_API_KEY"] = api_key

# 2. Import klas LangChain i OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore

# 3. Przygotowanie embeddingów
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# 4. Twoje dane
doswiadczenie = [
    "Projektowanie REST API w Django",
    "Integracja z serwisami zewnętrznymi (SOAP, REST)",
    "Code review i mentoring młodszych devów"
]
umiejetnosci = ["Python", "Django", "JavaScript", "SQL", "Docker", "Git"]
job_description = (
    "Senior Backend Developer (Python/Django). Poszukujemy osoby, która prowadzi projekty backendowe, "
    "optymalizuje zapytania do bazy danych i dba o wysoką jakość kodu."
)

# 5. InMemoryVectorStore (przechowuje embeddingi w pamięci)
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_texts(doswiadczenie + umiejetnosci)

# 6. Retriev­er top-k
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# 7. Szablon promptu
template = """
Na podstawie poniższych informacji z profilu wygeneruj profesjonalne CV dla stanowiska: {job}

Profil:
{context}
"""
prompt = PromptTemplate(
    input_variables=["context", "job"],
    template=template
)

# 8. Konfiguracja LLM (ChatOpenAI jak GPT-4)
llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

# 9. Chain RetrievalQA (łączenie retrieval + generacja CV)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=False,
    chain_type_kwargs={"prompt": prompt},
)

# 10. Wykonanie łańcucha
context_docs = retriever.get_relevant_documents(job_description)
context_text = "\n".join([doc.page_content for doc in context_docs])
cv = qa_chain.run({"query": job_description, "context": context_text})

# 11. Wyświetlenie wygenerowanego CV
print(cv)
