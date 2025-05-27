import os
from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  # tak jak w pierwszym kodzie

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
INDEX_NAME = os.environ["INDEX_NAME"]
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
chat = ChatOpenAI(verbose=True, temperature=0.7)  # model_name="gpt-4" jeśli masz dostęp

user_id = "user_1"
doswiadczenie = [
    "Projektowanie REST API w Django",
    "Integracja z serwisami zewnętrznymi (SOAP, REST)",
    "Code review i mentoring młodszych devów"
]
umiejetnosci = ["Python", "Django", "JavaScript", "SQL", "Docker", "Git"]

# Ingest: dzielimy i wrzucamy do bazy
def ingest_profile(profile_fragments: list[str]):
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # każdy wpis traktujemy osobno albo łączymy
    chunks = []
    for txt in profile_fragments:
        chunks += splitter.split_text(txt)
    vectorstore.add_texts(chunks, metadatas=[{"user_id":user_id}]*len(chunks))

# Przygotuj profile
ingest_profile(doswiadczenie + umiejetnosci)

# Build retrieval chain
retriever = vectorstore.as_retriever(search_kwargs={"filter":{"user_id":user_id}, "k":5})
retrieval_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
stuff_chain = create_stuff_documents_chain(chat, retrieval_prompt)
qa_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=stuff_chain)

# Generowanie CV na podstawie opisu
job_description = (
    "Senior Backend Developer (Python/Django). Poszukujemy osoby, która prowadzi projekty backendowe, "
    "optymalizuje zapytania do bazy danych i dba o wysoką jakość kodu."
)
answer = qa_chain.invoke({"input": job_description})
print(answer)
