import os

from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langsmith import traceable

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
INDEX_NAME = os.environ.get("INDEX_NAME")

vectorstore = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embeddings
)

user_id = "user_1"

@traceable(name="Ingest CV to Knowledge Base")
def ingest_to_knowledge_base(query: str) -> str:
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_text(query)
    vectorstore.add_texts(
        texts,
        metadatas=[{"user_id": user_id}] * len(texts)
    )
    return "CV data inserted successfully."

@traceable(name="Retrieve from Knowledge Base")
def retrieve_from_knowledge_base(query: str) -> str:
    docsearch = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    chat = ChatOpenAI(verbose=True, temperature=0)

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_docs_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt)

    retrival_chain = create_retrieval_chain(
        retriever=docsearch.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}}
        ),
        combine_docs_chain=stuff_docs_chain
    )
    result = retrival_chain.invoke(input={"input": query})

    return result["answer"]
