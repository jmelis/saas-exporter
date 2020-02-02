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


class GHRepo():
    PREFIX = 'https://github.com/'

    def __init__(self, gh_client, full_repo):
        repo_name = _get_repo_name(full_repo, self.PREFIX)
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
                ts = datetime.timestamp(commit_date)

                pos = self.total_commits - i

                return (pos, ts)


class GLRepo():
    def __init__(self, gl_client, full_repo):
        repo_name = _get_repo_name(full_repo, gl_client.url)
        self.repo = gl_client.projects.get(repo_name)
        self.commits = self.repo.commits.list(all=True,
                                              query_parameters={
                                                  'ref_name': 'master'
                                              })

    @property
    def total_commits(self):
        return len(self.commits)

    def get_commit_info(self, sha):
        for i, commit in enumerate(self.commits):
            if commit.id == sha:
                raw_date = commit.attributes['committed_date']
                commit_date = parser.parse(raw_date)
                ts = datetime.timestamp(commit_date)

                pos = self.total_commits - i

                return (pos, ts)
