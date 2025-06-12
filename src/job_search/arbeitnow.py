import requests

class ArbeitNowAPI:
    def __init__(self):
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"

    def search_jobs(self, query, limit=5):
        try:
            params = {"search": query}
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])[:limit]
                return self.format_jobs(jobs)
            else:
                return "❌ Job search service unavailable"
        except Exception as e:
            return f"❌ Search failed: {str(e)}"

    def format_jobs(self, jobs):
        if not jobs:
            return "😔 No jobs found for your search"

        message = f"🎯 Found {len(jobs)} job opportunities:\n\n"

        for job in jobs:
            title = job.get("title", "Unknown Position")
            company = job.get("company_name", "Unknown Company")
            location = job.get("location", "Unknown Location")
            url = job.get("url", "")

            message += f"📋 **{title}**\n"
            message += f"🏢 {company}\n"
            message += f"📍 {location}\n"
            if url:
                message += f"🔗 [View Job]({url})\n"
            message += "\n"

        return message

# Initialize the job API



if __name__ == "__main__":
    job_api = ArbeitNowAPI()
    print(job_api.search_jobs('python fullstack warsaw'))