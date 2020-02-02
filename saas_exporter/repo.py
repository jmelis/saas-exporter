from datetime import datetime

from dateutil import parser

class GHRepo():
    PREFIX = 'https://github.com/'

    def __init__(self, gh_client, full_repo):
        repo_name = self._get_repo_name(full_repo)
        self.repo = gh_client.get_repo(repo_name)
        self.commits = [c for c in self.repo.get_commits()]

    @property
    def total_commits(self):
        return len(self.commits)

    def get_commit_info(self, sha):
        for i, commit in enumerate(self.commits):
            if commit.sha == sha:
                raw_date = commit.raw_data['commit']['author']['date']
                commit_date = parser.parse(raw_date)
                return (self.total_commits - i, datetime.timestamp(commit_date))

    def _get_repo_name(self, full_url):
        url = full_url

        if url.startswith(self.PREFIX):
            url = url[len(self.PREFIX):]

        if url.endswith('.git'):
            url = url[:len('.git')]

        return url

    def is_valid(self, full_repo):
        return full_repo.startswith(self.PREFIX)
