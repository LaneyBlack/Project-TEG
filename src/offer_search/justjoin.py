import os

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('APIFY_TOKEN')

class JustJoinItAPI:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.apify.com/v2/acts/piotrv1001~just-join-it-scraper"

    def search_jobs(self, filters=None, limit=10):
        '''
        Search jobs using Apify JustJoin.it scraper

        filters can include:
        - technology: e.g., "python", "javascript"
        - experience_level: "junior", "mid", "senior"
        - employment_type: "b2b", "permanent"
        - workplace_type: "remote", "hybrid", "office"
        - salary_from: minimum salary
        - salary_to: maximum salary
        '''
        try:
            # Prepare input for the Apify actor
            run_input = {
                "maxItems": limit
            }

            if filters:
                run_input.update(filters)

            # Start the actor run
            response = requests.post(
                f"{self.base_url}/runs?token={self.api_token}",
                json=run_input,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:
                run_data = response.json()["data"]
                run_id = run_data["id"]

                # Wait for completion and get results
                return self._wait_for_results(run_id)
            else:
                return f"❌ Failed to start job search: {response.text}"

        except Exception as e:
            return f"❌ Search failed: {str(e)}"

    def _wait_for_results(self, run_id):
        import time

        # Poll for completion (simplified version)
        for _ in range(30):  # Wait up to 5 minutes
            status_response = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}?token={self.api_token}"
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]

                if status == "SUCCEEDED":
                    # Get dataset results
                    dataset_id = status_response.json()["data"]["defaultDatasetId"]
                    results_response = requests.get(
                        f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={self.api_token}"
                    )

                    if results_response.status_code == 200:
                        jobs = results_response.json()
                        return self.format_jobs(jobs)

                elif status == "FAILED":
                    return "❌ Job search failed"

            time.sleep(10)

        return "⏰ Search timed out"

    def format_jobs(self, jobs):
        if not jobs:
            return "😔 No jobs found"

        message = f"🎯 Found {len(jobs)} job opportunities:\\n\\n"

        for job in jobs[:5]:  # Show first 5 jobs
            title = job.get("title", "Unknown Position")
            company = job.get("companyName", "Unknown Company")
            location = job.get("city", "Unknown Location")
            salary_from = job.get("salaryFrom")
            salary_to = job.get("salaryTo")
            currency = job.get("currency", "PLN")
            url = job.get("jobUrl", "")

            message += f"📋 **{title}**\\n"
            message += f"🏢 {company}\\n"
            message += f"📍 {location}\\n"

            if salary_from and salary_to:
                message += f"💰 {salary_from:,.0f} - {salary_to:,.0f} {currency}\\n"
            elif salary_from:
                message += f"💰 From {salary_from:,.0f} {currency}\\n"

            if url:
                message += f"🔗 [Apply Here]({url})\\n"
            message += "\\n"

        return message




if __name__ == "__main__":
    print(TOKEN)
    api = JustJoinItAPI(TOKEN)
    results = api.search_jobs(filters={"technology": "python"}, limit=1 )
    print(results)
