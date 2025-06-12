import os

from dotenv import load_dotenv
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable

from knowledge import retrieve_from_knowledge_base, ingest_to_knowledge_base

load_dotenv()

# Load environment variables
INDEX_NAME = os.environ.get("INDEX_NAME")
user_id = "user_1"

# Initialize embedding and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)


@traceable(name="Analyze Job Offer")
def analyze_job_offer_against_cv(job_offer: str, user_id: str) -> str:
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

    # Reuse retrieval pipeline
    return retrieve_from_knowledge_base(advisor_query, user_id)

@traceable(name="Get Job Offer")
def get_job_offers_cv(user_id: str) -> str:
    retrieve_from_knowledge_base()

@traceable(name="Insert Job Offer")
def insert_job_offer(job_offer: str) -> str:
    ingest_to_knowledge_base(job_offer, 'offers')