import tempfile
import os
import logging
from pathlib import Path

import git
import yaml

from lib.retry import retry


@retry()
def get_saas_repos(gql):
    query = """
        {
            apps: apps_v1 {
                codeComponents {
                name
                resource
                url
                }
            }
        }
    """

    apps = gql.query(query)['apps']

    return [
        c['url']
        for app in apps
        for c in (app.get('codeComponents', {}) or {})
        if c['resource'] == "saasrepo"
    ]


class GitCloneError(Exception):
    pass


class MissingServicesDir(Exception):
    pass


class SaasRepo():
    def __init__(self, url):
        self.url = url
        self.services = []

        self._load()

    def _load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                git.Repo.clone_from(self.url, tmpdir, depth=1)
            except Exception:
                raise GitCloneError()

            self._load_from(tmpdir)

    def _load_from(self, saas_repo_path):
        saas_repo = Path(saas_repo_path)

        with open(saas_repo / 'config.yaml') as config_path:
            config = yaml.safe_load(config_path)

        for context in config['contexts']:
            services_dir = context['data']['services_dir']
            services_dir_full = saas_repo / services_dir

            try:
                service_file_paths = os.listdir(services_dir_full)
            except FileNotFoundError:
                logging.error(f"Missing services dir: {services_dir}")
                continue

            for service_file_path in service_file_paths:
                service_file = services_dir_full / service_file_path
                if service_file.suffix == '.yaml':
                    self._add_services(context['name'], service_file)

    def _add_services(self, context_name, service_file):
        try:
            with open(service_file) as service_yaml:
                services = yaml.safe_load(service_yaml)
        except Exception:
            logging.error(f"Error reading YAML: {service_file}")
            return

        for service in services['services']:
            # add context to the service dict
            service['context'] = context_name

            self.services.append(service)
