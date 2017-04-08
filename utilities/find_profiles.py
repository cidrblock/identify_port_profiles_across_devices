import os
import yaml
from glob import glob
import uuid
import collections
from os import listdir
from os.path import isfile, join

HOST_VARS = '../host_vars'
COUNT_FOR_PROFILE = 1
PROFILES_FILE = '../group_vars/all/port_profiles.yml'

device_vars = [fname for fname in listdir(HOST_VARS) \
                  if isfile(join(HOST_VARS, fname))]

if not os.path.exists(HOST_VARS + '_original'):
    os.makedirs(HOST_VARS + '_original')

# load the device configurations
devices = []
for device_file in device_vars:
    hostname = '.'.join(device_file.split('.')[:-1])
    device = {}
    device['hostname'] = hostname
    exisiting_fname = '%s/%s' % (HOST_VARS, device_file)
    with open(exisiting_fname, 'r') as stream:
        device['vars'] = yaml.load(stream)
    devices.append(device)
    new_fname = '%s/%s' % (HOST_VARS + '_original', device_file)
    os.rename(exisiting_fname, new_fname)

# Build a list of interfaces without name or description
all_interfaces = []
for device in devices:
    for interface in device['vars']['interfaces']:
        repl = device['vars']['interfaces'][interface].copy()
        repl.pop('name', None)
        repl.pop('description', None)
        all_interfaces.append(yaml.dump(repl))

# Indentify profiles based on count
profiles = {}
for item, count in collections.Counter(all_interfaces).items():
    if count > COUNT_FOR_PROFILE:
        profiles[str(uuid.uuid4())] = yaml.load(item)

#Interate back through to find matches
for profile in profiles:
    for device in devices:
        for interface in device['vars']['interfaces']:
            repl = device['vars']['interfaces'][interface].copy()
            name = repl.pop('name', None)
            description = repl.pop('description', None)
            if yaml.dump(profiles[profile]) == yaml.dump(repl):
                repl = { "inherit_from": profile }
            repl['name'] = name
            if description:
                repl['description'] = description
            device['vars']['interfaces'][interface] = repl.copy()

# dump the devices
for device in devices:
    fname = '%s/%s.yml' % (HOST_VARS, device['hostname'])
    with open(fname, 'w') as outfile:
        yaml.dump(device['vars'], outfile, default_flow_style=False)

# dump the profiles
with open(PROFILES_FILE, 'w') as outfile:
    yaml.dump(profiles, outfile, default_flow_style=False)

print "%s profiles identified and written to port_profiles.yml" % len(profiles)
