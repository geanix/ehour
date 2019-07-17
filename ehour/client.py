import attr

from typing import List

from ehour.project import Project


@attr.s
class Client(object):
    api = attr.ib()
    id = attr.ib()
    name = attr.ib(default=None)
    code = attr.ib(default=None)
    active = attr.ib(default=None)

    def fill(self) -> None:
        response = self.api.get(f'clients/{self.id}')
        for k, v in response.items():
            if k in ('clientId', 'links'):
                continue
            if k == 'description':
                v = v.splitlines()
            if k.startswith('customField'):
                try:
                    k = self.api.config['Custom Fields'][f'client.{k}']
                except AttributeError:
                    pass        # No configuration supplied
                except KeyError:
                    pass        # Field name not configured
            setattr(self, k, v)

    def projects(self) -> List[Project]:
        response = self.api.get(f'clients/{self.id}/projects')
        projects = []
        for r in response:
            projects.append(Project(r['projectId'], r['code'], r['name'],
                                    r['active']))
        return projects
