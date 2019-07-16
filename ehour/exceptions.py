class RestError(Exception):
    def __init__(self, code, string):
        super(RestError, self).__init__(string)
        self.string = string
        self.code = code
