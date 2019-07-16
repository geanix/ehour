import attr


@attr.s
class Project(object):
    id = attr.ib()
    code = attr.ib(default=None)
    name = attr.ib(default=None)
    active = attr.ib(default=None)
