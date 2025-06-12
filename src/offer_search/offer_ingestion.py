import json

from advisor import user_id
from knowledge import ingest_to_knowledge_base

def format_job_for_ingestion(job):
    desc = job['description'].replace('\n','')
    return (
        f"---Title: {job['title']}"
        f"---Description: {desc}"
        f"---Job url: {job['url']}"
        f"---Company: {job['company']}"
    )


def main(start_index=0, end_index=None):
    with open('../../data/jobs.json', 'r', encoding='utf-8') as f:
        jobs = json.load(f)

    if end_index is None or end_index > len(jobs):
        end_index = len(jobs)

    skip_counter = 0
    seen_prefixes = set()

    for i in range(start_index, end_index):
        job = jobs[i]
        desc = job['description'] if 'description' in job else ''
        prefix = desc[:100]

        if prefix in seen_prefixes:
            print('Skipping duplicate job')
            skip_counter += 1
            continue  # Skip this job

        formatted_text = format_job_for_ingestion(job)
        print(formatted_text)
        print(ingest_to_knowledge_base(formatted_text, user_id='offers'))

        seen_prefixes.add(prefix)
    print('Total skipped jobs: {}'.format(skip_counter))

if __name__ == '__main__':
    main(400, 800)