import os

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
        # Similar implementation to JustJoin.it scraper
        # Returns formatted job results
        pass

if __name__ == "__main__":
    api = ApifyNoFluffJobsAPI(TOKEN)
    results = api.search_jobs("https://nofluffjobs.com/pl/backend?criteria=python")
    print(results)
