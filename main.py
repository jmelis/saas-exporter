import os
import urllib.parse
import time
import logging
import re

from github import Github
from gitlab import Gitlab
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
from sentry_sdk import init as sentry_sdk_init

from lib.saas_repo import get_saas_repos, SaasRepo
from lib.repo import GHRepo, GLRepo, CommitNotFound
from lib.metrics import SaasCollector
from lib.gql import GqlApi

logger = logging.getLogger()

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GITLAB_SERVER = os.environ['GITLAB_SERVER']
GITLAB_TOKEN = os.environ['GITLAB_TOKEN']

APP_INTERFACE_URL = os.environ['APP_INTERFACE_URL']
APP_INTERFACE_TOKEN = os.environ['APP_INTERFACE_TOKEN']

SENTRY_DSN = os.getenv('SENTRY_DSN')

gh_client = Github(GITHUB_TOKEN)
gl_client = Gitlab(GITLAB_SERVER, private_token=GITLAB_TOKEN)
gql_client = GqlApi(APP_INTERFACE_URL, APP_INTERFACE_TOKEN)

if os.getenv('SLEEP_TIME'):
    SLEEP_TIME = int(os.environ['SLEEP_TIME'])
else:
    SLEEP_TIME = 300


if SENTRY_DSN:
    def before_breadcrumb(crumb, hint):
        # remove authentication from http urls
        if crumb['category'] == 'subprocess':
            crumb['message'] = re.sub(r'//.*?@', '//***@', crumb['message'])
        return crumb

    sentry_sdk_init(SENTRY_DSN, before_breadcrumb=before_breadcrumb)


def inject_auth(url, auth):
    parts = list(urllib.parse.urlsplit(url))
    parts[1] = auth + '@' + parts[1]
    return urllib.parse.urlunsplit(parts)


def get_stats(saas_repos):
    stats = []
    for saas_repo_full in saas_repos:
        logging.info(['saas_repo', saas_repo_full])

        if saas_repo_full.startswith(GITLAB_SERVER):
            saas_repo_auth = inject_auth(saas_repo_full, GITLAB_TOKEN)
        else:
            saas_repo_auth = saas_repo_full

        try:
            saas_repo = SaasRepo(saas_repo_auth)
        except Exception as e:
            logging.error(e)
            continue

        for service in saas_repo.services:
            upstream_url = service['url']
            context = service['context']
            name = service['name']
            sha = service['hash']

            if sha in ['none', 'ignore', None]:
                logging.info(['ignore', saas_repo_full, upstream_url,
                              context, name, sha])
                continue

            logging.info(['fetching_stats', context, name])

            if upstream_url.startswith(GHRepo.PREFIX):
                repo = GHRepo(gh_client, upstream_url)
            elif upstream_url.startswith(gl_client.url):
                repo = GLRepo(gl_client, upstream_url)
            else:
                logging.error(['Invalid upstream repo',
                               saas_repo_full, upstream_url])

            try:
                commit_index, commit = repo.get_commit(sha)
            except CommitNotFound:
                logging.error(['CommitNotFound', saas_repo_full, upstream_url,
                               context, name, sha])
                continue

            stats.append({
                'context': context,
                'service': name,
                'saas_upstream_commits': repo.total_commits,
                'saas_commit_index': repo.total_commits - commit_index,
                'saas_commit_ts': repo.commit_ts(commit)
            })

    return stats


if __name__ == "__main__":
    start_http_server(8000)

    collector = SaasCollector()
    REGISTRY.register(collector)

    while True:
        saas_repos = get_saas_repos(gql_client)

        collector.stats = get_stats(saas_repos)

        time.sleep(SLEEP_TIME)
