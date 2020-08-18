from bottle import DEBUG, JSONPlugin, json_dumps

class JSONPrettyPlugin(JSONPlugin):
    name = 'json-pretty'
    api = 2

    def __init__(self, json_dumps=json_dumps, indent=2, pretty_production=True):

        self.original_json_dumps = json_dumps
        self.indent = indent
        self.pretty_production = pretty_production

        super().__init__(self.wrap_json_dumps())

    def wrap_json_dumps(self):

        def wrapper(*args, **kwargs):
            if (DEBUG or self.pretty_production):
                kwargs['indent'] = self.indent
            return self.original_json_dumps(*args, **kwargs)

        return wrapper
