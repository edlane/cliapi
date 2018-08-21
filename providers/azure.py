from cliapi_lib import Provider, cliapi_decor
from what_cloud import determine_provider

import json
import os
import uuid
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET

#----- raises an error on import if not running in a "proper" cloud...
try:
    cp = determine_provider()
    if cp != 'azure':
        raise Exception("not a valid provider")
except Exception as e:
    raise e

provider = Provider()

scoops = {
    'instance-name': "['meta_data']['compute']['name']",
    'mac': "['meta_data']['network']['interface'][0]['macAddress']",
    'location': "meta_data['compute']['location']",
    'external-ip': "['meta_data']['network']['interface'][0]"
                   "['ipv4']['ipAddress'][0]['publicIpAddress']",
    'internal-ip': "['meta_data']['network']['interface'][0]"
                   "['ipv4']['ipAddress'][0]['privateIpAddress']",
    'cloud-service': "['get_cloud_service']"
}

help = {
    'instance-name': 'name of instance',
    'location': 'region location',
    'mac': 'the MAC address for this interface',
    'api_version': 'azure metadata api version, default = \'2017-08-01\'',
    'cloud-service': 'what'
}

options = dict(api_version='$api_version')

@cliapi_decor(provider, api_alias='meta_data', scoops=scoops, help=help, options=options)
def get_meta_data_azure(api_version='2017-08-01'):
    HEADERS = {'Metadata': 'true'}
    IP = '169.254.169.254'
    url = 'http://{0}/metadata/instance?api-version={1}'.format(IP, api_version)
    req = urllib.request.Request(url, headers=HEADERS)
    content = urllib.request.urlopen(req).read()
    result = json.loads(content.decode('utf-8'))
    return result


@cliapi_decor(provider, api_alias='cloud-service')
def get_cloud_service():
    # tree = ET.parse('/home/lane/Downloads/SharedConfig.xml')
    tree = ET.parse('/var/lib/waagent/SharedConfig.xml')
    root = tree.getroot()
    cloud_service = root.find('Deployment').find('Service').get('name') + '.cloudapp.net'
    return cloud_service


@cliapi_decor(provider, api_alias='tag')
def read_billing_guid(device='/dev/sda'):
    fd = os.open(device, os.O_RDONLY)
    os.lseek(fd, 65536, os.SEEK_SET)
    uuid_string = str(uuid.UUID(bytes_le=os.read(fd, 16)))
    return uuid_string
