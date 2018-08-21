import inspect
import importlib
from string import Template

class Provider(dict):
    def __init__(self, fetchers={}):
        self.fetchers = {}
        self.scoops = {}
        self.options = {}
        self.help = {}
        self.template = {}

        return super().__init__({})

    def __getitem__(self, item):

        try:
            result = super().__getitem__(item)
        except KeyError:
            # restrict python's  eval() function -- No builtins, only "item" is accessible
            # api = eval('[' + item.replace(']', '],') + ']',
            #                {'__builtins__': None},
            #                {'item': item})[0][0]
            fetcher = self.fetchers[item].split('.')
            provider = importlib.import_module('.'.join(fetcher[0:2]))

            super().__setitem__(item, eval('provider.' +
                                              Template(fetcher[2]).substitute(self.template)))
            # restrict python's eval() functon -- No builtins, only "self" is accessible
            result = self.get(item)
            # result = eval("self" + item, {'__builtins__': None}, {'self': self})
        return result


def cliapi_decor(prov, api_alias=None, scoops={}, options={}, help={}):
    def decorate_it(func):
        if api_alias is None:
            alias = func.__name__
        else:
            alias = api_alias
        # prov.scoops=alias
        prov.scoops.update(scoops)
        prov.options.update(options)
        prov.help.update(help)
        argspec = inspect.getargspec(func)
        if argspec.defaults is None:
            default_count = 0
        else:
            default_count = len(argspec.defaults)
        last_arg = len(argspec.args) - default_count
        argspec_string = '('
        for i, arg in enumerate(argspec.args):
            if i < last_arg:
                # substitute CLI options...
                arg = prov.options.get(arg, arg)
                argspec_string += '\'' + arg + '\', '
            else:
                default = argspec.defaults[i - last_arg]
                # substitute CLI options...
                # op_default = prov.options.get(arg, default)
                op_default = prov.options.get(arg, default)
                if op_default.startswith('$'):
                    prov.template[op_default[1:]] = default
                argspec_string += arg + '=\'' + op_default + '\', '

        prov.fetchers.update({alias :
                              func.__module__ + '.' +
                              func.__name__ +
                              argspec_string + ')'
                              })

        def wrap_it(*args, **kwargs):
            if len(args) == 0:
                a = ()
            else:
                a = args
            if len(kwargs) == 0:
                b = {}
            else:
                b = kwargs
            return func(*a, **b)
        return wrap_it

    return decorate_it
