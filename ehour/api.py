import attr
import urllib.parse
import requests
import configparser

from typing import Optional, List

from ehour.client import Client
from ehour.exceptions import RestError


@attr.s
class EhourApi(object):
    key = attr.ib(validator=attr.validators.instance_of(str))
    base_url = attr.ib(default='https://ehourapp.com/api/v1/',
                       validator=attr.validators.instance_of(str))
    config_file = attr.ib(default=None)

    def __attrs_post_init__(self):
        if not self.config_file:
            return
        config = configparser.ConfigParser()
        config.read_file(self.config_file)
        self.config = config

    @property
    def session(self):
        try:
            return self._session
        except AttributeError:
            self._session = requests.Session()
            self._session.headers.update({'X-API-Key': self.key})
            return self._session

    def get_raw(self, path, **kwargs):
        url = urllib.parse.urljoin(self.base_url, path)
        rsp = self.session.get(url, params=kwargs)
        if not rsp.ok:
            raise RestError(rsp.status_code, rsp.reason)
        return rsp

    def get(self, path, **kwargs):
        return self.get_raw(path, **kwargs).json()

    def clients(self,
                query: Optional[str] = None,
                state: bool = True,
                fill: bool = False) -> List[Client]:
        response = self.get('clients', query=query, state=state)
        clients = []
        for r in response:
            client = Client(r['clientId'], r['name'], r['code'], r['active'])
            if fill:
                client.fill(self)
            clients.append(client)
        return clients
