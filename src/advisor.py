from langsmith import traceable

from src.managers.knowledge import retrieve_from_knowledge_base, ingest_to_knowledge_base
from langsmith import traceable

from src.managers.knowledge import retrieve_from_knowledge_base, ingest_to_knowledge_base


# load_dotenv()


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
def get_job_offers_cv(job_title: str) -> str:
    query = f"""
       Find the top 5 most relevant job offers (compare only job titles) based on the following job query:

       "{job_title}"

       Provide:
       - Job title
       - One-sentence summary or key skills
       - Location (if available)
       - Small description of this job offer
       - This Job url

       Format the result as a numbered list.
       """
    return retrieve_from_knowledge_base(query=query, user_id="offers")


@traceable(name="Insert Job Offer")
def insert_job_offer(job_offer: str) -> str:
    return ingest_to_knowledge_base(job_offer, 'offers')
