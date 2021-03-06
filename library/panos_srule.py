#!/usr/bin/env python

# Copyright (c) 2014, Palo Alto Networks <techbizdev@paloaltonetworks.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

DOCUMENTATION = '''
---
module: panos_srule
short_description: create a security rule
description:
    - Create a security rule
author:
    - Palo Alto Networks
version_added: "0.0"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    rule_name:
        description:
            - name of the security rule
        required: true
    from_zone:
        description:
            - list of source zones
        required: false
        default: "any"
    to_zone:
        description:
            - list of destination zones
        required: false
        default: "any"
    source:
        description:
            - list of source addresses
        required: false
        default: "any"
    destination:
        description:
            - list of destination addresses
        required: false
        default: "any"
    application:
        description:
            - list of applications
        required: false
        default: "any"
    service:
        description:
            - list of services
        required: false
        default: "application-default"
    hip_profiles:
        description:
            - list of HIP profiles
        required: false
        default: "any"
    group_profile:
        description:
            - security profile group
        required: false
        default: None
    log_start:
        description:
            - whether to log at session start
        required: false
        default: "false"
    log_end:
        description:
            - whether to log at session end
        required: false
        default: true
    rule_type:
        description:
            - type of security rule (6.1+)
        required: false
        default: "universal"
    vulnprofile_name:
        description:
            - name of the vulnerability profile
        required: false
        default: None
    action:
        description:
            - action
        required: false
        default: "allow"
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
# permti ssh to 1.1.1.1
- panos_srule:
    ip_address: "192.168.1.1"
    password: "admin"
    rule_name: "server permit"
    from_zone: ["public"]
    to_zone: ["private"]
    source: ["any"]
    source_user: ["any"]
    destination: ["1.1.1.1"]
    category: ["any"]
    application: ["ssh"]
    service: ["application-default"]
    hip_profiles: ["any"]
    action: "allow"

# deny all
- panos_srule:
    ip_address: "192.168.1.1"
    password: "admin"
    username: "admin"
    log_start: true
    log_end: true
    action: "deny"
    rule_type: "interzone"
'''

import sys

try:
    import pan.xapi
except ImportError:
    print "failed=True msg='pan-python required for this module'"
    sys.exit(1)

_SRULE_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
               "/vsys/entry[@name='vsys1']" +\
               "/rulebase/security/rules/entry[@name='%s']"


def security_rule_exists(xapi, rule_name):
    xapi.get(_SRULE_XPATH % rule_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_security_rule(xapi, **kwargs):
    if security_rule_exists(xapi, kwargs['rule_name']):
        return False

    # exml = ['<entry name="permit-server"%s">'%kwargs['rule_name']]
    exml = []

    exml.append('<to>')
    for t in kwargs['to_zone']:
        exml.append('<member>%s</member>' % t)
    exml.append('</to>')

    exml.append('<from>')
    for t in kwargs['from_zone']:
        exml.append('<member>%s</member>' % t)
    exml.append('</from>')

    exml.append('<source>')
    for t in kwargs['source']:
        exml.append('<member>%s</member>' % t)
    exml.append('</source>')

    exml.append('<destination>')
    for t in kwargs['destination']:
        exml.append('<member>%s</member>' % t)
    exml.append('</destination>')

    exml.append('<source-user>')
    for t in kwargs['source_user']:
        exml.append('<member>%s</member>' % t)
    exml.append('</source-user>')

    exml.append('<category>')
    for t in kwargs['category']:
        exml.append('<member>%s</member>' % t)
    exml.append('</category>')

    exml.append('<application>')
    for t in kwargs['application']:
        exml.append('<member>%s</member>' % t)
    exml.append('</application>')

    exml.append('<service>')
    for t in kwargs['service']:
        exml.append('<member>%s</member>' % t)
    exml.append('</service>')

    exml.append('<hip-profiles>')
    for t in kwargs['hip_profiles']:
        exml.append('<member>%s</member>' % t)
    exml.append('</hip-profiles>')

    if kwargs['group_profile'] is not None:
        exml.append('<profile-setting>'
                    '<group><member>%s</member></group>'
                    '</profile-setting>' % kwargs['group_profile'])

    if kwargs['log_start']:
        exml.append('<log-start>yes</log-start>')
    else:
        exml.append('<log-start>no</log-start>')

    if kwargs['log_end']:
        exml.append('<log-end>yes</log-end>')
    else:
        exml.append('<log-end>no</log-end>')

    if kwargs['rule_type'] != 'universal':
        exml.append('<rule-type>%s</rule-type>' % kwargs['rule_type'])

    exml.append('<action>%s</action>' % kwargs['action'])

    if kwargs['vulnprofile_name'] is not None:
        exml.append('<profile-setting>')
        exml.append('<profiles>')
        exml.append('<vulnerability>')
        exml.append('<member>%s</member>' % kwargs['vulnprofile_name'])
        exml.append('</vulnerability>')
        exml.append('</profiles>')
        exml.append('</profile-setting>')

    # exml.append('</entry>')

    exml = ''.join(exml)
    xapi.set(xpath=_SRULE_XPATH % kwargs['rule_name'], element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(default=None),
        password=dict(default=None, no_log=True),
        username=dict(default='admin'),
        rule_name=dict(default=None),
        from_zone=dict(default=['any']),
        to_zone=dict(default=['any']),
        source=dict(default=["any"]),
        source_user=dict(default=['any']),
        destination=dict(default=["any"]),
        category=dict(default=['any']),
        application=dict(default=['any']),
        service=dict(default=['application-default']),
        hip_profiles=dict(default=['any']),
        group_profile=dict(),
        vulnprofile_name=dict(),
        log_start=dict(type='bool', default=False),
        log_end=dict(type='bool', default=True),
        rule_type=dict(default='universal'),
        action=dict(default='allow'),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec)

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    rule_name = module.params['rule_name']
    if not rule_name:
        module.fail_json(msg='rule_name is required')
    from_zone = module.params['from_zone']
    to_zone = module.params['to_zone']
    source = module.params['source']
    source_user = module.params['source_user']
    destination = module.params['destination']
    category = module.params['category']
    application = module.params['application']
    service = module.params['service']
    hip_profiles = module.params['hip_profiles']
    action = module.params['action']

    group_profile = module.params['group_profile']
    vulnprofile_name = module.params['vulnprofile_name']
    if group_profile is not None and vulnprofile_name is not None:
        module.fail_json(msg="only one of group_profile and "
                         "vulnprofile_name should be specified")

    log_start = module.params['log_start']
    log_end = module.params['log_end']
    rule_type = module.params['rule_type']
    commit = module.params['commit']

    changed = add_security_rule(
        xapi,
        rule_name=rule_name,
        from_zone=from_zone,
        to_zone=to_zone,
        source=source,
        source_user=source_user,
        destination=destination,
        category=category,
        application=application,
        service=service,
        hip_profiles=hip_profiles,
        group_profile=group_profile,
        log_start=log_start,
        log_end=log_end,
        rule_type=rule_type,
        vulnprofile_name=vulnprofile_name,
        action=action
    )
    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")

from ansible.module_utils.basic import *  # noqa

main()
