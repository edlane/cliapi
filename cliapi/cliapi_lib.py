import inspect
import importlib
from string import Template

class Provider(dict):
    # The Provider class overrides Python's dictionary with
    # an API-backing-store.
    # When a KeyError is encountered during lookup,
    # a fetcher, or "API call", is prepared with the appropriate CLI
    # options substituted as python function arguments.
    # CLI "help" and predefined dictionary lookups, or "scoops",
    # are also assembled in this class...

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
            # this dictionary item does not currently exist
            # so fetch it using the API which resolves to
            # the top level dictionary with that API key name...
            fetcher = self.fetchers[item]
            fetcher_function = fetcher[0].split('.')

            # setup for calling the appropriate plugin API...
            provider = importlib.import_module('.'.join(fetcher_function[0:3]))

            arg_list = list()
            kwarg_dict = dict()
            try:
                # replace API args and kwargs with CLI provided options...
                for arg in fetcher[1][0]:
                    # build the *args tuple...
                    arg_list.append(Template(arg).substitute(self.template))
                for key, value in fetcher[1][1].items():
                    # build the **kwargs dictionary...
                    kwarg_dict[key] = Template(value).substitute(self.template)
                function = getattr(provider, fetcher_function[3])
                    # fault-in the API values...
                super().__setitem__(item, function(*arg_list, **kwarg_dict))
            except Exception as e:
                raise AssertionError('required option {}, missing'.format(e))
            # rerun the dictionary lookup and return results...
            result = self.get(item)
        return result


def cliapi_assembler(prov, api_alias=None, scoops={}, options={}, help={}):
    # Compile each API supported by the plugin provider as a python
    # function and assemble into the various dictionaries of
    # the "Provider" class.
    # These dictionaries are later used by the "cliapi engine"
    # in "cliapi.main()" to create a Unix, getopt()-style CLI...

    def assemble_it(func):
        # REMEMBER: All this work happens at "import time"...
        if api_alias is None:
            alias = func.__name__
        else:
            alias = api_alias
        # assemble more scoops...
        prov.scoops.update(scoops)
        # assemble more plugin options...
        prov.options.update(options)
        # assemble more help...
        prov.help.update(help)

        # Here is some meta-magic...
        # use introspection to extract calling requirements
        # for this particular "API fetcher" and save in fetchers
        # dictionary for later when it is actually called...
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

        # Register this function as an "API fetcher"...
        prov.fetchers.update({alias:
                                  (func.__module__ + '.' +
                                   func.__name__,
                                   (func_args, func_kwargs))
                              })

        def do_it(*args, **kwargs):
            # REMEMBER: All this work happens at call time...
            # TODO: this is a hack
            # at a "Universal Python Function Wrapper".
            # There is probably a better way to do this but it
            # eludes me at the moment...
            if len(args) == 0:
                a = ()
            else:
                a = args
            if len(kwargs) == 0:
                b = {}
            else:
                b = kwargs
            return func(*a, **b)
        return do_it

    return assemble_it
