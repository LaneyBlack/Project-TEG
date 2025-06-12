import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('APIFY_TOKEN')


class ApifyNoFluffJobsAPI:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.apify.com/v2/acts/memo23~apify-nofluffjobs-cheerio-scraper"

    def search_jobs(self, search_url=None, limit=10):
        '''
        Search jobs using Apify NoFluffJobs scraper

        search_url: URL from nofluffjobs.com (e.g., filtered search)
        If no URL provided, will search all Polish jobs
        '''
        try:
            run_input = {
                "startUrls": [
                    {"url": search_url or "https://nofluffjobs.com/pl"}
                ],
                "maxItems": limit
            }

            response = requests.post(
                f"{self.base_url}/runs?token={self.api_token}",
                json=run_input,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:
                run_data = response.json()["data"]
                return self._wait_for_results(run_data["id"])
            else:
                return f"❌ Failed to start search: {response.text}"

        except Exception as e:
            return f"❌ Search failed: {str(e)}"

    def _wait_for_results(self, run_id):
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

        return jobs

if __name__ == "__main__":
    with open('jobs.json', 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    api = ApifyNoFluffJobsAPI(TOKEN)
    results = api.search_jobs("https://nofluffjobs.com/pl/backend?criteria=java")

    print(results)
    for job in results:
        musts = [item['value'] for item in job['requirements'].get('musts', [])]
        nices = [item['value'] for item in job['requirements'].get('nices', [])]
        # Build the requirements section as plain text
        requirements_section = ""
        if musts:
            requirements_section += "Must have: " + ", ".join(musts) + "\n"
        if nices:
            requirements_section += "Nice to have: " + ", ".join(nices) + "\n"
        job_dict = {
            "url": f'https://nofluffjobs.com/pl/job/{job["id"]}',
            "description": (
                    job["details"]["description"] + "\n\nRequirements:\n" +
                    requirements_section
            ),
            "company": job["company"]["url"],
            "title": job["title"]
        }
        jobs.append(job_dict)

    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

