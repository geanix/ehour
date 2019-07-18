# -*- coding: utf-8 -*-
"""Main eHour API module.

Includes the EhourApi"""

import urllib.parse
import requests
import configparser

from typing import List, Optional

from ehour.model import User, Client, Project
from ehour.exceptions import RestError


class EhourApi(object):

    def connect(self,
                key: str,
                base_url: str = 'https://ehourapp.com/api/v1/',
                config_file=None) -> None:
        self.session: requests.Session = requests.Session()
        self.session.headers.update({'X-API-Key': key})
        self.base_url = base_url
        self.config: Optional[configparser.ConfigParser]
        if config_file:
            config = configparser.ConfigParser()
            config.read_file(config_file)
            self.config = config
        else:
            self.config = None

    def get(self,
            path: str,
            **kwargs: str) -> requests.Response:
        url = urllib.parse.urljoin(self.base_url, path)
        rsp = self.session.get(url, params=kwargs)
        if not rsp.ok:
            raise RestError(rsp.status_code, rsp.reason)
        return rsp

    def get_dict(self,
                 path: str,
                 **kwargs: str) -> dict:
        rsp = self.get(path, **kwargs).json()
        assert isinstance(rsp, dict)
        return rsp

    def get_list(self,
                 path: str,
                 **kwargs: str) -> list:
        rsp = self.get(path, **kwargs).json()
        assert isinstance(rsp, list)
        return rsp

    def users(self, only_active: bool = True) -> List[User]:
        response = self.get_list('users',
                                 state='active' if only_active else 'all')
        users = []
        for rsp in response:
            user = User.get(rsp['userId'], active=rsp['active'],
                            firstName=rsp['firstName'],
                            lastName=rsp['lastName'],
                            email=rsp['email'])
            user.update()
            users.append(user)
        return users

    def client(self, client_id: str) -> Client:
        client = Client(client_id)
        client.update()
        return client

    def clients(self,
                query: str = '',
                only_active: bool = True) -> List[Client]:
        kwargs = {'state': 'active' if only_active else 'all'}
        if query:
            kwargs['query'] = query
        response = self.get_list('clients', **kwargs)
        clients = []
        for rsp in response:
            client = Client.get(rsp['clientId'], code=rsp['code'],
                                name=rsp['name'], active=rsp['active'])
            client.update()
            clients.append(client)
        return clients

    def project(self, project_id: str) -> Project:
        project = Project(project_id)
        project.update()
        return project

    def projects(self,
                 query: str = None,
                 only_active: bool = True) -> List[Project]:
        kwargs = {'state': 'active' if only_active else 'all'}
        if query:
            kwargs['query'] = query
        response = self.get_list('projects', **kwargs)
        return self._projects(response)

    def projects_for_client(self,
                            client: Client,
                            only_active: bool = True) -> List[Project]:
        response = self.get_list(f'clients/{client.id}/projects')
        projects = self._projects(response)
        if only_active:
            projects = [prj for prj in projects if prj.active]
        return projects

    def _projects(self, response: list) -> List[Project]:
        projects = []
        for rsp in response:
            project = Project.get(rsp['projectId'], code=rsp['code'],
                                  name=rsp['name'], active=rsp['active'])
            project.update()
            projects.append(project)
        return projects


# Singleton API instance.  Use this instance as the only one for easy access
# from your entire codebase without having to pass it around.  The EhourApi
# class is made for this, providing the EhourApi.connect() method to use for
# connecting to the eHour cloud service.
API = EhourApi()
