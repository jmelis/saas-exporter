import os
import urllib.parse
import time
import logging

from github import Github
from gitlab import Gitlab
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

from lib.saas_repo import get_saas_repos, SaasRepo
from lib.repo import GHRepo, GLRepo
from lib.metrics import SaasCollector
from lib.gql import GqlApi

logger = logging.getLogger()

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

SLEEP_TIME = 300

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_SERVER = os.getenv('GITLAB_SERVER')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

APP_INTERFACE_URL = os.getenv('APP_INTERFACE_URL')
APP_INTERFACE_TOKEN = os.getenv('APP_INTERFACE_TOKEN')

gh_client = Github(GITHUB_TOKEN)
gl_client = Gitlab(GITLAB_SERVER, private_token=GITLAB_TOKEN)
gql_client = GqlApi(APP_INTERFACE_URL, APP_INTERFACE_TOKEN)


def inject_auth(url, auth):
    parts = list(urllib.parse.urlsplit(url))
    parts[1] = auth + '@' + parts[1]
    return urllib.parse.urlunsplit(parts)


def get_stats(saas_repos):
    stats = []
    for repo in saas_repos:
        logging.info(['saas_repo', repo])

        if repo.startswith(GITLAB_SERVER):
            repo = inject_auth(repo, GITLAB_TOKEN)

        saas_repo = SaasRepo(repo)

        for service in saas_repo.services:
            url = service['url']
            context = service['context']
            name = service['name']

            logging.info(['fetching_stats', context, name])

            if url.startswith(GHRepo.PREFIX):
                repo = GHRepo(gh_client, url)
            elif url.startswith(gl_client.url):
                repo = GLRepo(gl_client, url)
            else:
                raise Exception(f'Unknown repo: {url}')

            # TODO: handle CommitNotFound
            i, commit = repo.get_commit(service['hash'])

            stats.append({
                'context': context,
                'service': name,
                'saas_upstream_commits': repo.total_commits,
                'saas_commit_index': repo.total_commits - i,
                'saas_commit_ts': repo.commit_ts(commit)
            })

    return stats


if __name__ == "__main__":
    start_http_server(8000)

    collector = SaasCollector()
    REGISTRY.register(collector)

    while True:
        # TODO: handle exception
        saas_repos = get_saas_repos(gql_client)

        # TODO: handle exception
        collector.stats = get_stats(saas_repos)

        time.sleep(SLEEP_TIME)
