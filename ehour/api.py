import attr
import urllib.parse
import requests
import configparser

from typing import List, Union

from ehour.client import Client
from ehour.exceptions import RestError


@attr.s
class EhourApi(object):
    key = attr.ib(validator=attr.validators.instance_of(str))
    base_url = attr.ib(default='https://ehourapp.com/api/v1/',
                       validator=attr.validators.instance_of(str))
    config_file = attr.ib(default=None)

    def __attrs_post_init__(self) -> None:
        if not self.config_file:
            return
        config = configparser.ConfigParser()
        config.read_file(self.config_file)
        self.config = config

    @property
    def session(self) -> requests.Session:
        try:
            return self._session
        except AttributeError:
            self._session: requests.Session = requests.Session()
            self._session.headers.update({'X-API-Key': self.key})
            return self._session

    def get_raw(self,
                path: str,
                **kwargs: str) -> requests.Response:
        url = urllib.parse.urljoin(self.base_url, path)
        rsp = self.session.get(url, params=kwargs)
        if not rsp.ok:
            raise RestError(rsp.status_code, rsp.reason)
        return rsp

    def get(self,
            path: str,
            **kwargs: str) -> Union[dict, list]:
        return self.get_raw(path, **kwargs).json()

    def clients(self,
                query: str = None,
                only_active: bool = True,
                fill: bool = False) -> List[Client]:
        response = self.get('clients',
                            query=query or '',
                            state='active' if only_active else 'all')
        assert isinstance(response, list)
        clients = []
        for r in response:
            client = Client(self, r['clientId'],
                            r['name'], r['code'], r['active'])
            if fill:
                client.fill()
            clients.append(client)
        return clients

    def client(self, client_id: str) -> Client:
        client = Client(self, client_id)
        client.fill()
        return client
