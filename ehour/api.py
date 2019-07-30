# -*- coding: utf-8 -*-
"""Main eHour API module.

Includes the EhourApi"""

import urllib.parse
import requests
import configparser
import datetime
import io
import zipfile

from typing import List, Dict, Optional, Any

from ehour.model import User, Client, Project, Hours, Expense, ExpenseCategory
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

    @staticmethod
    def parse_date(date_str: str) -> datetime.date:
        """Parse date in format DD/MM/YYYY."""
        day, month, year = [int(i) for i in date_str.split('/')]
        return datetime.date(year, month, day)

    @staticmethod
    def unpack_report_row(columns: List[str],
                          data: List[str]) -> dict:
        row: Dict[str, Any] = dict(zip(columns, data))
        row['date'] = EhourApi.parse_date(row.pop('daily'))
        if 'client-id' in row:
            row['client'] = Client.get(row.pop('client-id'),
                                       code=row.pop('client-code'),
                                       name=row.pop('client-name'))
        if 'project-id' in row:
            row['project'] = Project.get(row.pop('project-id'),
                                         code=row.pop('project-code'),
                                         name=row.pop('project-name'))
        if 'user-id' in row:
            row['user'] = User.get(row.pop('user-id'),
                                   name=row.pop('user-user'))
        if 'expense-category-code' in row:
            row['expense-category'] = ExpenseCategory(
                code=row.pop('expense-category-code'),
                name=row.pop('expense-category-name'),
                billable=row.pop('expense-category-billable'))

        return row

    def hours(self,
              start: datetime.date,
              end: datetime.date,
              user: User = None,
              client: Client = None,
              project: Project = None) -> List[Hours]:
        kwargs = {'start': start.isoformat(), 'end': end.isoformat()}
        kwargs['columns'] = ('HOURS_HOURS,HOURS_TURNOVER,HOURS_COMMENT,'
                             'ASSIGNMENT_RATE')
        if user:
            kwargs['userId'] = user.id
        else:
            kwargs['columns'] += ',USER_ID,USER_USER'
        if client:
            kwargs['clientId'] = client.id
        else:
            kwargs['columns'] += ',CLIENT_ID,CLIENT_CODE,CLIENT_NAME'
        if project:
            kwargs['projectId'] = project.id
        else:
            kwargs['columns'] += ',PROJECT_ID,PROJECT_CODE,PROJECT_NAME'
        # TODO: handle pagination for reports with more than 10000 entries
        rsp = self.get_dict('report', **kwargs)
        columns = rsp['columns']
        hours = []
        for data in rsp['data']:
            row = self.unpack_report_row(columns, data)
            minutes = row.pop('hours-hours')
            hours.append(Hours(
                hours=datetime.time(minutes // 60, minutes % 60),
                turnover=row.pop('hours-turnover'),
                comment=row.pop('hours-comment'),
                rate=row.pop('assignment-rate'),
                date=row.pop('date'),
                client=client or row.pop('client'),
                project=project or row.pop('project'),
                user=user or row.pop('user'),
            ))
        return hours

    def expenses(self,
                 start: datetime.date,
                 end: datetime.date,
                 user: User = None,
                 client: Client = None,
                 project: Project = None) -> List[Expense]:
        kwargs = {'start': start.isoformat(), 'end': end.isoformat()}
        kwargs['columns'] = ('EXPENSE_ID,EXPENSE_NAME,'
                             'EXPENSE_COST,EXPENSE_VAT,'
                             'EXPENSE_CATEGORY_CODE,EXPENSE_CATEGORY_NAME,'
                             'EXPENSE_CATEGORY_BILLABLE,'
                             'EXPENSE_COMMENT,EXPENSE_RECEIPT,EXPENSE_TAG,'
                             'EXPENSE_CUSTOM_1,EXPENSE_CUSTOM_2,'
                             'EXPENSE_CUSTOM_3,'
                             'EXPENSE_RECEIPT')
        if user:
            kwargs['userId'] = user.id
        else:
            kwargs['columns'] += ',USER_ID,USER_USER'
        if client:
            kwargs['clientId'] = client.id
        else:
            kwargs['columns'] += ',CLIENT_ID,CLIENT_CODE,CLIENT_NAME'
        if project:
            kwargs['projectId'] = project.id
        else:
            kwargs['columns'] += ',PROJECT_ID,PROJECT_CODE,PROJECT_NAME'
        # TODO: handle pagination for reports with more than 10000 entries
        rsp = self.get_dict('report', **kwargs)
        columns = rsp['columns']
        expenses = []
        for data in rsp['data']:
            row = self.unpack_report_row(columns, data)
            receipt_list = row.pop('expense-receipt')
            if receipt_list:
                num_receipts = len(receipt_list.split(','))
            else:
                num_receipts = 0
            expenses.append(Expense(
                date=row.pop('date'),
                client=client or row.pop('client'),
                project=project or row.pop('project'),
                user=user or row.pop('user'),
                id=row.pop('expense-id'),
                name=row.pop('expense-name'),
                cost=row.pop('expense-cost'),
                vat=row.pop('expense-vat'),
                comment=row.pop('expense-comment'),
                category=row.pop('expense-category'),
                num_receipts=num_receipts,
                tag=row.pop('expense-tag'),
                custom1=str(row.get('expense-custom-1') or ''),
                custom2=str(row.get('expense-custom-2') or ''),
                custom3=str(row.get('expense-custom-3') or ''),
            ))
        return expenses

    def expense_receipts(self, expense_id: str) -> Dict[str, bytes]:
        """Download all receipts associated with an expense."""
        receipts = {}
        rsp = self.get(f"expense/{expense_id}/receipt")
        zf = zipfile.ZipFile(io.BytesIO(rsp.content))
        for fn in zf.namelist():
            receipts[fn] = zf.read(fn)
        return receipts


# Singleton API instance.  Use this instance as the only one for easy access
# from your entire codebase without having to pass it around.  The EhourApi
# class is made for this, providing the EhourApi.connect() method to use for
# connecting to the eHour cloud service.
API = EhourApi()
