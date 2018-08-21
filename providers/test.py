
from cliapi_lib import Provider, cliapi_decor

provider = Provider()

scoops = {
    'test': "['test']",
    'meta-data': "['meta_data']",
}

help = {
    'smurf': 'required, what is smurf name?',
    'lorax': 'who is the lorax?',
    'dweebville': 'where is dweebville?',
}

options = dict(arg1='$smurf', key1='$dufus', key2='$dweebville',)

@cliapi_decor(provider, api_alias='test', scoops=scoops, help=help, options=options)
def dork(arg1, key1='foo', key2='bar'):
    return [arg1, key1, key2]


scoops = {
            'instance-name': "['meta_data']['compute']['name']",
            'mac': "['meta_data']['network']['interface'][0]['macAddress']",
            'location': "['meta_data']['compute']['location']",
            'external-ip': "['meta_data']['network']['interface'][0]"
                       "['ipv4']['ipAddress'][0]['publicIpAddress']",
            'internal-ip': "['meta_data']['network']['interface'][0]"
                           "['ipv4']['ipAddress'][0]['privateIpAddress']",
}

help = {
    'instance-name': 'name of instance',
    'location': 'region location',
    'mac': 'the MAC address for this interface',
}

@cliapi_decor(provider, api_alias='meta_data', scoops=scoops, help=help)
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

@cliapi_decor(provider, api_alias='some_stuff', scoops=scoops, help=help, options=options)
def get_stuff(api_version='2017-08-01'):
    return api_version
