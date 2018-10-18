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
from collections import defaultdict

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
        print("failure to import {}, {}".format(pro, e))
        pass

# Help for Common CLI options...
common_help = {
    'help': 'help for this CLI command',
    'provider=': 'specify name of provider module',
    'list-providers': 'list all available providers',
    # TODO: does "xml-out" really need to be implemented in a modern Devops world???
    # 'xml-out': 'output in xml format',
    'list-apis': 'list all available APIs for specified provider',
    'all': 'output all API results for a specific provider',
    'item=': 'value to return from an API using right-most path name specifier'
}


def _cli_parse(argv):
    cli_tree = dict()
    for arg in argv:
        kv = arg.split('=')
        if len(kv) > 1:
            cli_tree[kv[0]] = kv[1]
        else:
            cli_tree[kv[0]] = None
    return cli_tree


def _print_help(provider):
    global common_help
    # Help for Common CLI options...

    if provider == None:
        vpp = Provider()
        # no provider supplied so at least print out the "common" help...
        vpp.help = common_help
    else:
        vpp = valid_providers[provider].provider
    required = list()
    for fetcher in vpp.fetchers.items():
        # create a list of required options for fast lookup...
        required += fetcher[Provider.FUNC_PARMS][Provider.FUNC_KWARGS][Provider.FUNC_REQUIRED]
    indent2_format = '  --{:<15}  {:<15}'
    print(
        "usage: {} --item=[API display item #1]... [API config option#1]... [API required options]... [Common CLI options]...".format(
            sys.argv[0]))
    print("\n***[ {} ]*** provider Display options:".format(provider))
    try:
        _fetch_all_apis(vpp)
    except AssertionError as e:
        print(e.args[0], 'required options must be provided to list all displayable API options')

    all_apis = _scan_apis(vpp)
    _print_api_options(all_apis)
    print("\n***[ {} ]*** provider API config options:".format(provider))
    for k, v in vpp.options.items():
        # list API configuration options for this provider...
        if v.startswith('$'):
            opt = v[1:]
            help = vpp.help.get(opt, '')
            if help != '':
                # help message is provided by plugin provider...
                help = ''.join((', ', help))
            if v in required:
                # if this option is required, then say so...
                help = ''.join(('-REQUIRED-', help))
            elif opt in vpp.template:
                # otherwise display the default...
                help = ''.join(('default=\'', vpp.template[opt], '\'', help))

            print (indent2_format.format(opt + '=', help))
    print("\nCommon CLI options:")
    for key in common_help.keys():
        # list of common CLI options supported by this module, across all providers
        print (indent2_format.format(key, common_help.get(key, '')))


def _fetch_all_apis(vpp):
    # return a composite dictionary of all API calls...
    for fetch in vpp.fetchers:
        # prefetch all the APIs...
        # must populate the vpp dictionary by walking the top-level API...
        try:
            vpp[fetch]
        except Exception as e:
            raise e
    # return all the API results from dictionary...
    return vpp


def _get_value_by_endswith(api_list, endswith):
    for path in api_list:
        if path[0].endswith(endswith):
            return path[1]


def _scan_apis(vpp, path='', path_list=[]):
    leaf = None
    if isinstance(vpp, dict):
        for element in vpp.keys():
            leaf = _scan_apis(vpp[element], path + '.' + element, path_list)
            if isinstance(leaf, tuple):
                path_list.append((list(leaf[1])))
    elif isinstance(vpp, list):
        index = 0
        for element in vpp:
            leaf = _scan_apis(element, path + '[' + str(index) + ']', path_list)
            index += 1
            if isinstance(leaf, tuple):
                path_list.append((list(leaf[1])))
    else:
        # print(path, vpp )
        return path_list, (path, vpp)

    return path_list


def _print_api_options(path_list):
    for element in path_list:
        split_element = element[0].split('.')
        element_len = len(split_element)
        print(2 * element_len * ' ', split_element[-1])


def main():
    global common_help
    # must do our own parsing here since we don't know the
    # valid options until we establish the plugin provider
    # -- getopt() does not allow this usage...
    ct = _cli_parse(sys.argv[1:])

    if '--list-providers' in ct:
        print(json.dumps(list(valid_providers.keys()), indent=2))
        exit(0)

    cmd_dict = defaultdict(list)
    _, cli_name = os.path.split(sys.argv[0])
    if '--provider' in ct:
        # using supplied provider...
        provider = ct['--provider']
    elif cli_name == 'cliapi':
        try:
            # use the first valid provider in list...
            provider = list(valid_providers.keys())[0]
        except Exception as e:
            # error -- print help and exit
            print('No valid plugin providers found')
            _print_help(None)
            exit(-1)
    else:
        # the name of calling program is used to specify the provider...
        if cli_name in list(valid_providers.keys()):
            provider = cli_name
        else:
            print('No plugin provider for {} was found'.format(cli_name))
            _print_help(None)
            exit(-1)

    vpp = valid_providers[provider].provider
    all_opts = []
    options = []
    for k, v in vpp.options.items():  # process args...
        if v.startswith('$'):
            options.append(v[1:] + '=')
    all_opts += options

    # add "common" CLI options to the plugin's cli_options...
    all_opts += common_help.keys()

    try:
        # now we have enough info to use getopt() for cli parsing...
        optlist, arg = getopt.getopt(sys.argv[1:], '', all_opts)
    except getopt.GetoptError as e:
        # error -- print help and exit
        print(e.msg)
        cmd_dict['help'] = None
    else:
        # build a dictionary of the actual supplied CLI options...
        for opt in optlist:
            if opt[0] == '--item':
                # allow for many "items" in defaultdict as a list...
                # skipping the leading '--'
                cmd_dict[opt[0][2:]].append(opt[1])
            else:
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
        data = _fetch_all_apis(vpp)

    else:
        data = []
        for key, value in cmd_dict.items():
            if key == 'item':
                try:
                    _fetch_all_apis(vpp)
                except AssertionError as e:
                    _print_help(provider)
                    exit(-1)
                all_apis = _scan_apis(vpp)
                for item in cmd_dict['item']:
                    # ensure that last name is a complete item by prepending '.' ...
                    endswith = '.' + item
                    item = _get_value_by_endswith(all_apis, endswith)
                    data.append(item)
                continue
            else:
                # Not an item?
                # then ignore option, continue processing...
                continue

        if len(data) == 1:
            # a single value was returned so no list is returned...
            data = data[0]

    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
