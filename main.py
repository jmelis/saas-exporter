import os

from github import Github

from saas_exporter.saas_repo import SaasRepo
from saas_exporter.repo import GHRepo

gh_client = Github(os.environ["GITHUB_TOKEN"])
saas_repo = SaasRepo('https://github.com/app-sre/saas-app-interface')

for service in saas_repo.services:
    url = service['url']
    repo = GHRepo(gh_client, url)

    print([service['context'], service['name']])

    pos, ts = repo.get_commit_info(service['hash'])
    stats = {
        'upstream_commits': repo.total_commits,
        'commit_index': pos,
        'commit_ts': ts
    }

    print(stats)
