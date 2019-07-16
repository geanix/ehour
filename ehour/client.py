import attr


@attr.s
class Client(object):
    id = attr.ib()
    name = attr.ib(default=None)
    code = attr.ib(default=None)
    active = attr.ib(default=None)

    def fill(self, api):
        response = api.get(f'clients/{self.id}')
        for k, v in response.items():
            if k in ('clientId', 'links'):
                continue
            if k == 'description':
                v = v.splitlines()
            if k.startswith('customField'):
                try:
                    k = api.config['Custom Fields'][f'client.{k}']
                except AttributeError:
                    pass        # No configuration supplied
                except KeyError:
                    pass        # Field name not configured
            setattr(self, k, v)
