# -*- coding: utf-8 -*-
"""Module containing eHour API data model."""

import attr
import configparser

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
            setattr(self, key, value)
        attr.validate(self)


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
