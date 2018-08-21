from os import popen


def determine_provider():
    result = popen('/usr/sbin/dmidecode -t system').read()
    output = result.lower()
    if 'amazon' in output:
        provider = 'ec2'
    elif 'microsoft' in output:
        provider = 'azure'
    elif 'google' in output:
        provider = 'gce'
    else:
        raise Exception('Provider not found.')
    return provider
