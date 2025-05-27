import os

from dotenv import load_dotenv
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable

load_dotenv()

# Load environment variables
INDEX_NAME = os.environ.get("INDEX_NAME")
user_id = "user_1"

# Initialize embedding and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)


@traceable(name="Analyze Job Offer")
def analyze_job_offer_against_cv(job_offer: str) -> str:
    # Initialize LLM and retrieval chain
    chat = ChatOpenAI(verbose=True, temperature=0)
    retrieval_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    combine_chain = create_stuff_documents_chain(chat, retrieval_prompt)

    retriever = vectorstore.as_retriever(search_kwargs={"filter": {"user_id": user_id}})
    retrieval_chain = create_retrieval_chain(retriever, combine_chain)

    # Compose query
    advisor_query = f"""
    You are a career advisor helping a user evaluate a job offer against their CV.
    Here is the job offer:

    {job_offer}

    Based on the user's CV (already in the system), provide:
    - An overall match summary.
    - Skills that match well.
    - Skills where the user is overqualified.
    - Skills or requirements the user lacks or should improve.

    Return your advice in structured bullet points. 
    """

    result = retrieval_chain.invoke({"input": advisor_query})
    return result["answer"]