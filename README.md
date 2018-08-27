## GUIDE FOR CLIAPI DEVELOPERS:
**cliapi** ( pronounced _calliope_ ): A Python framework for creating Unix, "getopt()" style CLI scripts
composed from an arbitrary set of APIs.

...at its core, **cliapi** is _a data driven, state machine for dynamically generating CLIs_.

### cliapi features:
- entire CLI is generated by applying python decorators to API calls together with a dictionary with
a _backing-API-store_.
This decorator is applied to each API that is supported by a "plugin provider".
For each cloud provider (eg. Azure or GCE) a supporting "plugin" module is added to the
`cliapi/providers` directory (see **`cliapi directory layout`** below)

- consistent command line behavior is enforced by the cliapi framework across all plugin providers.
Several common commands are automatically inherited by all plugin providers:
(this allows a level of "discoverablility" to the CLI across all plugin providers)
  - "**--list-providers**" Lists all the available plugin providers.
  - "**--provider=**" specify a particular provider plugin for all CLI commands.
  - "**--all**" Lists all data returned by all APIs supported by a single provider.
  - "**--list-apis**" Lists all the APIs available by a particular plugin provider.
  - "**--query=**" extracts specified API data using a python-dictionary-restricted syntax.
- other behaviors enforced by the cliapi framework:
  - error handling and help is also consistent across all plugin providers.
  - multiple queries in same command will return a JSON list in "option order" by default
  - single query will return a single JSON element.

- multiple data queries within the same CLI will result in "at most" a single API call.

- presumably the plugin developer will rarely need to change the cliapi framework involving
python meta-programming.
Most plugins can be supported with a single module, a few dictionary initializers, 
and some function decorators.

### Key cliapi developer concepts:

- **provider**:  an associated set of APIs accessed from the CLI in a particular context or cloud
 environment e.g. "azure", "gce", "ec2", ... but can essentially be any mix of apis

- **api**: an API for interfacing to remote or local services.  If the interface can be implemented as
a python function with an (_*args, **kwargs_) style calling convention AND it returns a JSON serializable
object, THEN it can easily become a configurable CLI query.  With the cliapi decorator, both required and
optional parameters are expressible through the CLI.  Help is also handled by the cliapi framework.

- **scoops**: a dictionary which maps a CLI query name to a particular API data scoop. "scoops" are really just
"_sandboxed_ python _eval()_" statements.  This allows scoops to be expressed as Python slices,
comprehensions, ect.  It also allows restricted ad-hoc queries to be provided on the command line
when a return value is not currently supported as an option in the CLI.

- **fetchers**: a dictionary which maps from a particular API name to the actual python function which
provides the _backing store_ for the contents of the top-level API dictionary.

### cliapi directory layout:
```
├── cliapi                      root of cliapi package
│   ├── __init__.py
│   ├── cliapi_lib.py           framework meta classes and decorators
│   ├── cliapi.py               main() and the CLI generation code
│   └── what_cloud.py           module (useful for detecting which cloud plugins are valid)
│   ├── providers               directory for plugin providers
│   │   ├── __init__.py
│   │   ├── azure.py            plugin for Azure APIs
│   │   └── test.py             plugin for Test APIs (an included "test" API for hacking)
├── design.md                   design considerations for cliapi
├── LICENSE                     provisional license (Apache2 is mutable into any other license)
├── README.md                   this document
└── setup.py                    Python installation script
```

### Examples:
**example #1** - help (provider=azure and cliapi common)
```
ed-sle12sp3byos:/home/lane/cliapi # cliapi --help --provider=azure
usage: /usr/bin/cliapi [display option#1]... [API option#1]... [CLI option]

***[ azure ]*** provider Display options:
  --internal-ip                     
  --cloud-service    what           
  --instance-name    name of instance
  --external-ip                     
  --mac              the MAC address for this interface
  --location         region location

***[ azure ]*** provider API config options:
  --api_version=     azure metadata api version, default = '2017-08-01'

Common CLI options:
  --help             help for this CLI command
  --provider=        specify name of provider module
  --list-providers   list all available providers
  --list-apis        list all available APIs for specified provider
  --query=           specify a python dictionary style query command
  --all              output all API results for specified API options or defaults
  --pycharm-debug                   
```

**example #2** - a predefined query option
```
ed-sle12sp3byos:/home/lane/cliapi # cliapi --internal-ip --provider=azure
"172.16.3.8"
```

**example #3** - all values returned by all provider APIs
```
ed-sle12sp3byos:/home/lane/cliapi # cliapi --all --provider=azure
{
  "tag": "391e4f53-b82d-5af5-8f58-dc1035e46e5e",
  "meta_data": {
    "network": {
      "interface": [
        {
          "ipv6": {
            "ipAddress": []
          },
          "ipv4": {
            "ipAddress": [
              {
                "publicIpAddress": "40.112.253.198",
                "privateIpAddress": "172.16.3.8"
              }
            ],
            "subnet": [
              {
                "address": "172.16.3.0",
                "prefix": "24"
              }
            ]
          },
          "macAddress": "000D3A3AE8A5"
        }
      ]
    },
    "compute": {
      "offer": "SLES-BYOS",
      "publisher": "SUSE",
      "subscriptionId": "ce73a2b0-d2e7-4ff6-b987-b32d6908de4e",
      "name": "ed-sle12sp3byos",
      "platformUpdateDomain": "0",
      "version": "2018.02.21",
      "placementGroupId": "",
      "sku": "12-SP3",
      "tags": "",
      "vmId": "ce01dc32-6d0a-40bd-9534-a3509f768a53",
      "resourceGroupName": "ed_lane",
      "osType": "Linux",
      "location": "westus",
      "platformFaultDomain": "0",
      "vmSize": "Standard_B1ms"
    }
  },
  "cloud-service": "__ed-sle12sp3byosService.cloudapp.net"
}

```

**example #4** - a sandboxed python query
```
lane@suse-laptop:~/develop/garage/cliapi> cliapi --query="['meta_data']['compute']['offer']" --provider=test 
"SLES-BYOS"

```

**example #5** - multiple queries (single CLI call)
```
lane@suse-laptop:~/develop/garage/cliapi> cliapi --location --query="['meta_data']['compute']['offer']" --provider=test 
[
  "westus",
  "SLES-BYOS"
]

```

