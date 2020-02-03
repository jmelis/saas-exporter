from datetime import datetime

from dateutil import parser


def _get_repo_name(full_url, prefix):
    url = full_url

    if not prefix.endswith('/'):
        prefix += '/'

    if url.startswith(prefix):
        url = url[len(prefix):]

    if url.endswith('.git'):
        url = url[:len('.git')]

    return url


class CommitNotFound(Exception):
    pass


class Repo():
    def __init__(self, client, full_repo):
        self.client = client
        self.repo = self._get_repo(full_repo)
        self.commits = self._get_commits()

    def get_commit(self, sha):
        for i, commit in enumerate(self.commits):
            if self._commit_hash(commit) == sha:
                return (i, commit)

        # not found
        raise CommitNotFound()

    def commit_ts(self, commit):
        raw_date = self._commit_date(commit)
        commit_date = parser.parse(raw_date)
        return datetime.timestamp(commit_date)


class GHRepo(Repo):
    PREFIX = 'https://github.com/'

    def _get_repo(self, full_repo):
        repo_name = _get_repo_name(full_repo, self.PREFIX)
        return self.client.get_repo(repo_name)

    def _get_commits(self):
        return self.repo.get_commits()

    @property
    def total_commits(self):
        return self.commits.totalCount

    @staticmethod
    def _commit_date(commit):
        return commit.raw_data['commit']['author']['date']

    @staticmethod
    def _commit_hash(commit):
        return commit.sha


class GLRepo(Repo):
    def _get_repo(self, full_repo):
        repo_name = _get_repo_name(full_repo, self.client.url)
        return self.client.projects.get(repo_name)

    def _get_commits(self):
        params = {'ref_name': 'master'}
        return self.repo.commits.list(all=True,
                                      query_parameters=params)

    @property
    def total_commits(self):
        return len(self.commits)

    @staticmethod
    def _commit_date(commit):
        return commit.attributes['committed_date']

    @staticmethod
    def _commit_hash(commit):
        return commit.id
