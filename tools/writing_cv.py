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
        user_id: str = "user_1",
        index_name_env: str = "INDEX_NAME",
        embedding_model: str = "text-embedding-3-small",
        llm_temp: float = 0.7,
):
    # 1. Load env & API key
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY w .env")
    os.environ["OPENAI_API_KEY"] = api_key

    # 2. Init embeddings, vectorstore, chat
    embeddings = OpenAIEmbeddings(model=embedding_model)
    index_name = os.environ[index_name_env]
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    chat = ChatOpenAI(temperature=llm_temp, verbose=True)

    # 3. Ingest profile fragments
    # splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # chunks: list[str] = []
    # for fragment in profile_fragments:
    #     chunks += splitter.split_text(fragment)
    # vectorstore.add_texts(chunks, metadatas=[{"user_id": user_id}] * len(chunks))

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
    cv_text = generate_cv(job_desc)
    print(cv_text)
