from prometheus_client.core import GaugeMetricFamily


class SaasCollector(object):
    stats = []

    GAUGES = [
        (
            'saas_upstream_commits',
            'number of commits in the upstream repo',
        ),
        (
            'saas_commit_index',
            'commit number in upstream of the promoted commit',
        ),
        (
            'saas_commit_ts',
            'timestamp of the last promoted to prod commit',
        ),
    ]

    def collect(self):
        labels = ['saas_context', 'saas_service']
        gauges = {
            g[0]: GaugeMetricFamily(g[0], g[1], labels=labels)
            for g in self.GAUGES
        }
        for stats in self.stats:
            labels = [stats['context'], stats['service']]
            for gauge in gauges.keys():
                gauges[gauge].add_metric(labels, stats[gauge])
                yield gauges[gauge]
