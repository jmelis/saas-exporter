import os
import urllib.parse

from github import Github
from gitlab import Gitlab

from saas.saas_repo import SaasRepo
from saas.repo import GHRepo, GLRepo

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

        # TODO: handle CommitNotFound
        i, commit = repo.get_commit(service['hash'])

        stats = {
            'context': service['context'],
            'service': service['name'],
            'upstream_commits': repo.total_commits,
            'commit_index': repo.total_commits - i,
            'commit_ts': repo.commit_ts(commit)
        }

        print(stats)
