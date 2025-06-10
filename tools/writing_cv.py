import os
from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain.prompts import PromptTemplate


def generate_cv(
        job_description: str,
        user_id: str = "user_1"
):
    # 1. Load env & API key
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY w .env")
    os.environ["OPENAI_API_KEY"] = api_key

    # 2. Init embeddings, vectorstore, chat
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    index_name = os.environ["INDEX_NAME"]
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    chat = ChatOpenAI(temperature=0.7, verbose=True)

    # 4. Build retrieval → generation chain
    retriever = vectorstore.as_retriever(search_kwargs={"filter": {"user_id": user_id}, "k": 5})

    # 1. Zdefiniuj swój szablon
    my_template = PromptTemplate(
        input_variables=["context", "input"],
        template="""
    Na podstawie poniższych informacji z profilu wygeneruj profesjonalne CV dla stanowiska: {input}

    Profil:
    {context}

    Twoje CV powinno być zwięzłe i konkretne.
    """
    )

    # 2. Użyj go zamiast domyślnego
    stuff_chain = create_stuff_documents_chain(chat, my_template)

    qa_chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=stuff_chain)

    # 5. Invoke chain with job description
    result = qa_chain.invoke({"input": job_description})
    return result["answer"]


# PRZYKŁAD UŻYCIA:
if __name__ == "__main__":
    job_desc = (
        "Senior Backend Developer (Python/Django). Poszukujemy osoby, która prowadzi "
        "projekty backendowe, optymalizuje zapytania do bazy danych i dba o wysoką jakość kodu."
    )
    user_id = "user_1";
    cv_text = generate_cv(user_id=user_id, job_description=job_desc)
    print(cv_text)
