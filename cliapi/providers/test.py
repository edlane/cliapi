
from cliapi.cliapi_lib import Provider, cliapi_compile

provider = Provider()


help = {
    'smurf': 'what is smurf name?',
    'dweebville': 'where is dweebville?',
}

# options = dict(arg1='hello', key1='$dufus', key2='$dweebville',)
options = dict(arg1='$smurf', key1='$dufus', key2='$dweebville',)

@cliapi_compile(provider, api_alias='test', help=help, options=options)
def foo(arg1, key1='bar', key2='baz'):
    return [arg1, key1, key2]


@cliapi_compile(provider, api_alias='meta_data')
def get_meta_data_mock():
    return {"compute": {"location": "westus",
                        "name": "ed-sle12sp3byos", "offer": "SLES-BYOS",
                        "osType": "Linux", "placementGroupId": "",
                        "platformFaultDomain": "0",
                        "platformUpdateDomain": "0", "publisher": "SUSE",
                        "resourceGroupName": "ed_lane", "sku": "12-SP3",
                        "subscriptionId": "ce73a2b0-d2e7-4ff6-b987-b32d6908de4e",
                        "tags": "", "version": "2018.02.21", "vmId": "ce01dc32-6d0a-40bd-9534-a3509f768a53",
                        "vmSize": "Standard_B1ms"},
            "network": {"interface": [{"ipv4": {"ipAddress":
                                                    [{"privateIpAddress": "172.16.3.8",
                                                      "publicIpAddress": "104.42.34.116"}],
                                                "subnet": [{"address": "172.16.3.0", "prefix": "24"}]},
                                       "ipv6": {"ipAddress": []},
                                       "macAddress": "000D3A3AE8A5"}]}}


options = dict(api_version='$api_version')

@cliapi_compile(provider, api_alias='some_stuff', options=options)
def get_stuff(api_version='2017-08-01'):
    return api_version
