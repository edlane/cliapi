import inspect
import importlib
from string import Template

class Provider(dict):
    def __init__(self):
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
            fetcher = self.fetchers[item]
            fetcher_function = fetcher[0].split('.')
            # fetcher = self.fetchers[item].split('.')
            provider = importlib.import_module('.'.join(fetcher_function[0:3]))

            arg_list = list()
            kwarg_dict = dict()
            for arg in fetcher[1][0]:
                # build the *args tuple...
                arg_list.append(Template(arg).substitute(self.template))
            for key, value in fetcher[1][1].items():
                # build the **kwargs dictionary...
                kwarg_dict[key] = Template(value).substitute(self.template)
            function = getattr(provider, fetcher_function[3])
            super().__setitem__(item, function(*arg_list, **kwarg_dict))
            result = self.get(item)
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
        func_args = []
        func_kwargs = {}
        for i, arg in enumerate(argspec.args):
            if i < last_arg:
                # substitute CLI options...
                arg = prov.options.get(arg, arg)
                func_args.append(arg)
            else:
                default = argspec.defaults[i - last_arg]
                # substitute CLI options...
                op_default = prov.options.get(arg, default)
                if op_default.startswith('$'):
                    prov.template[op_default[1:]] = default
                func_kwargs[arg] = op_default

        prov.fetchers.update({alias:
                                  (func.__module__ + '.' +
                                   func.__name__,
                                   (func_args, func_kwargs))
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
