#!/usr/bin/python3

# Guide for cliapi developers found here:
# https://github.com/edlane/cliapi/blob/master/README.md

import os
if 'PYCHARM_DEBUG_ME' in os.environ:
    import pydevd
    # we want debugging enabled up top because much of the cliapi framework
    # "import-meta-magic" happens before __main__() has ever been called...
    #
    # Remote debugging session enabled in cloud environments
    # by establishing a reverse ssh tunnel with bash:
    #
    #   local_host> ssh -R 8282:localhost:8282 lane@remote_host
    #
    # Then connect back to your local pycharm debugger with:
    #
    #   remote_host> PYCHARM_DEBUG_ME= cliapi [various options]...
    #
    pydevd.settrace('localhost', port=8282, stdoutToServer=True,
                    stderrToServer=True)

import sys
import importlib
import pkgutil
import getopt
import json

import cliapi.providers as providers
from cliapi.cliapi_lib import Provider

prefix = providers.__name__ + '.'

# this will scan the "providers" directory for all candidate provider modules...
all_providers = [mod for _, mod, _ in pkgutil.iter_modules(providers.__path__, prefix)]
valid_providers = {}

# import all valid providers found in the "providers" directory...
for pro in all_providers:
    module_name = pro.split('.')[-1]
    try:
        vp = importlib.import_module(pro)
        valid_providers[module_name] = vp
    except Exception as e:
        pass

# TODO: does "xml-out" really need to be implemented in a modern Devops world???
cli_options = ['help',
               'provider=',
               'list-providers',
               "list-apis",
               'query=', 'all',
               ]
                # 'xml-out']


def _cli_parse(argv):
    cli_tree = dict()
    for arg in argv:
        kv = arg.split('=')
        if len(kv)>1:
            cli_tree[kv[0]] = kv[1]
        else:
            cli_tree[kv[0]] = None
    return  cli_tree


def _print_help(provider):
    # Help for Common CLI options...
    help = {
        'help': 'help for this CLI command',
        'provider=': 'specify name of provider module',
        'list-providers': 'list all available providers',
        'xml-out': 'output in xml format',
        'list-apis': 'list all available APIs for specified provider',
        'query=': 'specify a python dictionary style query command',
        'all': 'output all API results for specified API options or defaults',
    }

    if provider == None:
        vpp = Provider()
        # no provider supplied so at least print out the "common" help...
        vpp.help = help
    else:
        vpp = valid_providers[provider].provider
        # update help with options from this provider...
        vpp.help.update(help)
    required = list()
    for fetcher in vpp.fetchers.items():
        # create a list of required options for fast lookup...
        required += fetcher[1][1][0]
    indent2_format = '  --{:<15}  {:<15}'
    print("usage: {} [display option#1]... [API option#1]... [CLI option]".format(sys.argv[0]))
    print("\n***[ {} ]*** provider Display options:".format(provider))
    for key in vpp.scoops.keys():
        # list display options for this provider...
        print (indent2_format.format(key, vpp.help.get(key, '')))
    print("\n***[ {} ]*** provider API config options:".format(provider))
    for k, v in vpp.options.items():
        # list API configuration options for this provider...
        if v.startswith('$'):
            opt = v[1:]
            help = vpp.help.get(opt,'')
            if v in required:
                # if this option is required, say so...
                help = 'REQUIRED, ' + help

            print (indent2_format.format(opt + '=', help))
    print("\nCommon CLI options:")
    for key in cli_options:
        # list of common CLI options supported by this module, across all providers
        print (indent2_format.format(key, vpp.help.get(key, '')))

    exit(0)


def _sandbox_eval(vpp, lookup):
    return eval('vpp' + lookup,
                {'__builtins__': None},
                {'vpp': vpp})


def main():
    # must do our own parsing here since we don't know the
    # valid options until we establish the plugin provider
    # -- getopt() does not allow this usage...
    ct = _cli_parse(sys.argv[1:])

    if '--list-providers' in ct:
        print(json.dumps(list(valid_providers.keys()), indent=2))
        exit(0)

    cmd_dict = {}
    if '--provider' in ct:
        # using supplied provider...
        provider = ct['--provider']
    else:
        try:
            # use the first valid provider in list...
            provider = list(valid_providers.keys())[0]
        except Exception as e:
            # error -- print help and exit
            print('No plugin providers found')
            _print_help(None)
            exit(-1)

    vpp = valid_providers[provider].provider
    all_opts = list(vpp.scoops.keys())
    options = []
    for k, v in vpp.options.items(): # process args...
        if v.startswith('$'):
            options.append(v[1:] + '=')
    all_opts += options

    # add "plugin cli_options" to the "common" CLI options...
    all_opts += cli_options

    try:
        # now we have enough info to use getopt() for cli parsing...
        optlist, arg = getopt.gnu_getopt(sys.argv[1:], '', all_opts)
    except getopt.GetoptError as e:
        # error -- print help and exit
        print(e.msg)
        cmd_dict['help'] = None
    else:
        # build a dictionary of the actual supplied CLI options...
        for opt in optlist:
            cmd_dict[opt[0][2:]] = opt[1]

        vpp.template.update(cmd_dict)

        # use defaults if option NOT supplied in CLI...
        for default in options:
            ds = default.split('=')
            try:
                if not cmd_dict.get(ds[0]):
                    # override with default...
                    cmd_dict[ds[0]] = ds[1]
            except:
                # no option to override or none specified -- ignore this...
                pass

    if 'help' in cmd_dict:
        _print_help(provider)
        exit(0)

    if 'list-apis' in cmd_dict:
        print(json.dumps(list(vpp.fetchers.keys()), indent=2))
        exit(0)

    if 'all' in cmd_dict:
        # return a composite dictionary of all API calls...
        for fetch in vpp.fetchers:
            # prefetch all the APIs...
            scoop = "['" + fetch + "']"
            # must populate dictionary by walking the top-level API...
            try:
                query = _sandbox_eval(vpp, scoop)
            except Exception as e:
                # error caused by plugin developer...
                print(e.args[0])
                _print_help(provider)
                exit(-1)
        # return all the API results from dictionary...
        data = vpp

    else:
        data = []
        for key, value in cmd_dict.items():
            # return all specified "data scoops"...
            if key in vpp.scoops:
                query = vpp.scoops[key]
            elif key == 'query':
                query = cmd_dict['query']
            else:
                # Not a scoop or a query?
                # then ignore option, continue processing...
                continue
            try:
                # accumulate all requested scoops
                data.append(_sandbox_eval(vpp, query))
            except KeyError as e:
                # error -- print help and exit
                if key == 'query':
                    # a bogus CLI option was input by user...
                    print(('bad query -- "{}", no such item').format(query))
                else:
                    # a bogus scoop option was specified by plugin developer...
                    print(('option {} -- "{}", bad plugin query').format(key, query))
            except AssertionError as e:
                # a required option is missing...
                print(e.args[0])
            except SyntaxError as e:
                # a syntax error detected in query...
                print('error in query -- "{}" syntax error'.format(query))
            else:
                # no errors, continue processing...
                continue
            # must have encountered an error, print help and abort...
            _print_help(provider)

        if len(data) == 1:
            # a single value was returned so no list is returned...
            data = data[0]

    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
