import os
import urllib.parse

from github import Github
from gitlab import Gitlab

from saas_exporter.saas_repo import SaasRepo
from saas_exporter.repo import GHRepo, GLRepo

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_SERVER = os.getenv('GITLAB_SERVER')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

gh_client = Github(GITHUB_TOKEN)
gl_client = Gitlab(GITLAB_SERVER, private_token=GITLAB_TOKEN)


def inject_auth(url, auth):
    parts = list(urllib.parse.urlsplit(url))
    parts[1] = auth + '@' + parts[1]
    return urllib.parse.urlunsplit(parts)


saas_repos = ['https://github.com/app-sre/saas-app-interface',
              'https://gitlab.cee.redhat.com/service/saas-app-sre-observability.git']

for repo in saas_repos:
    if repo.startswith(GITLAB_SERVER):
        repo = inject_auth(repo, GITHUB_TOKEN)

    saas_repo = SaasRepo(repo)

    for service in saas_repo.services:
        url = service['url']

        if url.startswith(GHRepo.PREFIX):
            repo = GHRepo(gh_client, url)
        elif url.startswith(gl_client.url):
            repo = GLRepo(gl_client, url)
        else:
            raise Exception(f'Unknown repo: {url}')

        pos, ts = repo.get_commit_info(service['hash'])
        stats = {
            'context': service['context'],
            'service': service['name'],
            'upstream_commits': repo.total_commits,
            'commit_index': pos,
            'commit_ts': ts
        }

        print(stats)
