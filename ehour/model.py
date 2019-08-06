# -*- coding: utf-8 -*-
"""Module containing eHour API data model."""

import attr
import configparser
import datetime

from typing import Dict

import ehour.api


@attr.s
class Model:
    """Base class for eHour API classes such as Client and Project."""

    id: str = attr.ib()
    _cache: dict = {}  # dummy class attribute to keep flake8 happy

    def __attrs_post_init__(self) -> None:
        """Post initialization function for attr style classes.

        Insert into cache and ensure against duplicate instances.
        """
        assert self.id not in self.__class__._cache
        self._cache[self.id] = self

    @classmethod
    def _get(cls, id: str, derived_cls, **kwargs):
        """Base function for derived get() class methods.

        It uses a per derived class cache, ensuring that the same instance is
        used for the same data.  Should be good for avoiding excessive
        re-fetching of the same information.
        """
        try:
            instance = derived_cls._cache[id]
        except KeyError:
            # Note, we don't insert into cache here, as it is self-inserting
            # in __attrs_post_init__()
            instance = derived_cls(id)
        for key, value in kwargs.items():
            setattr(instance, key, value)
        return instance

    @property
    def model_name(self):
        """Helper method to allow model generic methods.

        Produces the string 'client' for ehour.client.Client class, and so
        on.
        """
        return self.__class__.__name__.lower()

    def update(self) -> None:
        """Update instance with all data from API."""
        response = ehour.api.API.get_dict(f'{self.model_name}s/{self.id}')
        # Prune old values first to avoid mixing old and new information
        self.__dict__ = {'id': self.__dict__['id']}
        # Add received fields
        config = getattr(ehour.api.API, 'config', None)
        for key, value in response.items():
            if key in (f'{self.model_name}Id', 'links'):
                continue
            if isinstance(value, str) and '\n' in value:
                value = value.splitlines()
            if config and key.startswith('customField'):
                try:
                    key = config.get('Custom Fields',
                                     f'{self.model_name}.{key}')
                except (configparser.NoSectionError,
                        configparser.NoOptionError):
                    pass        # Field name not configured
            if isinstance(value, dict) and 'clientId' in value:
                value = Client.get(value['clientId'], code=value['code'],
                                   name=value['name'], active=value['active'])
            if isinstance(value, dict) and 'userId' in value:
                del value['links']
                value = User.get(value.pop('userId'), **value)
            setattr(self, key, value)
        attr.validate(self)


@attr.s
class User(Model):
    _cache: dict = {}  # derived class specific cache

    firstName: str = attr.ib(default=None, repr=True, kw_only=True)
    lastName: str = attr.ib(default=None, repr=True, kw_only=True)
    name: str = attr.ib(default=None, kw_only=True)
    email: str = attr.ib(default=None, kw_only=True)

    def __attrs_post_init__(self) -> None:
        self._update_name()

    def _update_name(self) -> None:
        if not getattr(self, 'name', None):
            if self.firstName:
                self.name = self.firstName
                if self.lastName:
                    self.name += f' {self.lastName}'
            elif self.lastName:
                self.name = self.lastName

    def update(self) -> None:
        super().update()
        self._update_name()

    @classmethod
    def get(cls, id: str, **kwargs):
        """Get unique Client instance."""
        return cls._get(id, cls, **kwargs)

    def __str__(self) -> str:
        if self.name is None:
            self.update()
        assert(self.name is not None)
        return self.name


@attr.s
class Client(Model):
    _cache: dict = {}  # derived class specific cache

    code: str = attr.ib(default=None, kw_only=True)
    name: str = attr.ib(default=None, kw_only=True)
    active: bool = attr.ib(default=None, kw_only=True)
    description: str = attr.ib(default=None, kw_only=True)
    customField1: str = attr.ib(default=None, kw_only=True)
    customField2: str = attr.ib(default=None, kw_only=True)
    customField3: str = attr.ib(default=None, kw_only=True)

    @classmethod
    def get(cls, id: str, **kwargs):
        """Get unique Client instance."""
        return cls._get(id, cls, **kwargs)

    def __str__(self) -> str:
        if self.name is None:
            self.update()
        assert(self.name is not None)
        return self.name


@attr.s
class Project(Model):
    _cache: dict = {}  # derived class specific cache

    code: str = attr.ib(default=None, kw_only=True)
    name: str = attr.ib(default=None, kw_only=True)
    active: bool = attr.ib(default=None, kw_only=True)
    billable: bool = attr.ib(default=None, kw_only=True)
    budgetInMinutes: int = attr.ib(default=None, kw_only=True)
    contact: str = attr.ib(default=None, kw_only=True)
    description: str = attr.ib(default=None, kw_only=True)
    projectManager: User = attr.ib(default=None, kw_only=True)
    client: Client = attr.ib(default=None, kw_only=True)

    @classmethod
    def get(cls, id: str, **kwargs):
        """Get unique Client instance."""
        return cls._get(id, cls, **kwargs)

    def __str__(self) -> str:
        if self.name is None:
            self.update()
        assert(self.name is not None)
        return self.name


@attr.s(auto_attribs=True)
class ReportEntry:

    date: datetime.date = attr.ib(kw_only=True)
    client: Client = attr.ib(kw_only=True)
    project: Project = attr.ib(kw_only=True)
    user: User = attr.ib(kw_only=True)


@attr.s(auto_attribs=True)
class Hours(ReportEntry):

    hours: datetime.time = attr.ib(kw_only=True)
    turnover: float = attr.ib(kw_only=True)
    comment: str = attr.ib(kw_only=True)
    rate: float = attr.ib(kw_only=True)


@attr.s
class ExpenseCategory:
    code: str = attr.ib(kw_only=True)
    name: str = attr.ib(kw_only=True)
    billable: bool = attr.ib(kw_only=True)


@attr.s(auto_attribs=True)
class Expense(ReportEntry):

    id: str = attr.ib(kw_only=True)
    name: str = attr.ib(kw_only=True)
    cost: float = attr.ib(kw_only=True)
    vat: float = attr.ib(kw_only=True)
    comment: str = attr.ib(kw_only=True)
    category: ExpenseCategory = attr.ib(kw_only=True)
    num_receipts: int = attr.ib(kw_only=True)
    tag: str = attr.ib(kw_only=True)
    custom1: str = attr.ib(kw_only=True)
    custom2: str = attr.ib(kw_only=True)
    custom3: str = attr.ib(kw_only=True)

    def get_receipts(self) -> Dict[str, bytes]:
        if self.num_receipts == 0:
            return {}
        return ehour.api.API.expense_receipts(self.id)
