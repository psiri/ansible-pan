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
module: panos_admpwd
short_description: change admin password of PAN-OS device using SSH with SSH key
description:
    - Change the admin password of PAN-OS via SSH using a SSH key for authentication.
    - Useful for AWS instances where the first login should be done via SSH.
author:
    - Palo Alto Networks
    - Luigi Mori (jtschichold)
version_added: "0.0"
requirements:
    - paramiko
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    key_filename:
        description:
            - filename of the SSH Key to use for authentication
        required: true
    password:
        description:
            - password to configure for admin on the PAN-OS device
        required: true
'''

EXAMPLES = '''
# Tries for 10 times to set the admin password of 192.168.1.1 to "badpassword"
# via SSH, authenticating using key /tmp/ssh.key
- name: set admin password
  panos_admpwd:
    ip_address: "192.168.1.1"
    key_filename: "/tmp/ssh.key"
    password: "badpassword"
  register: result
  until: not result|failed
  retries: 10
  delay: 30
'''

import time
import sys

try:
    import paramiko
except ImportError:
    print "failed=True msg='paramiko required for this module'"
    sys.exit(1)

_PROMPTBUFF = 4096


def wait_with_timeout(module, shell, prompt, timeout=60):
    now = time.time()
    result = ""
    while True:
        if shell.recv_ready():
            result += shell.recv(_PROMPTBUFF)
            endresult = result.strip()
            if len(endresult) != 0 and endresult[-1] == prompt:
                break

        if time.time()-now > timeout:
            module.fail_json(msg="Timeout waiting for prompt")

    return result


def set_pavmaws_password(module, ip_address, key_filename, password):
    stdout = ""

    ssh = paramiko.SSHClient()

    # add policy to accept all host keys, I haven't found
    # a way to retreive the instance SSH key fingerprint from AWS
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(ip_address, username="admin", key_filename=key_filename)
    shell = ssh.invoke_shell()

    # wait for the shell to start
    buff = wait_with_timeout(module, shell, ">")
    stdout += buff

    # step into config mode
    shell.send('configure\n')
    # wait for the config prompt
    buff = wait_with_timeout(module, shell, "#")
    stdout += buff

    # set admin password
    shell.send('set mgt-config users admin password\n')

    # wait for the password prompt
    buff = wait_with_timeout(module, shell, ":")
    stdout += buff

    # enter password for the first time
    shell.send(password+'\n')

    # wait for the password prompt
    buff = wait_with_timeout(module, shell, ":")
    stdout += buff

    # enter password for the second time
    shell.send(password+'\n')

    # wait for the config mode prompt
    buff = wait_with_timeout(module, shell, "#")
    stdout += buff

    # commit !
    shell.send('commit\n')

    # wait for the prompt
    buff = wait_with_timeout(module, shell, "#", 120)
    stdout += buff

    if 'success' not in buff:
        module.fail_json(msg="Error setting admin password: "+stdout)

    # exit
    shell.send('exit\n')

    ssh.close()

    return stdout


def main():
    argument_spec = dict(
        ip_address=dict(default=None),
        key_filename=dict(default=None),
        password=dict(default=None, no_log=True)
    )
    module = AnsibleModule(argument_spec=argument_spec)

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    key_filename = module.params["key_filename"]
    if not key_filename:
        module.fail_json(msg="key_filename should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")

    stdout = set_pavmaws_password(module, ip_address, key_filename, password)

    module.exit_json(changed=True, stdout=stdout)


from ansible.module_utils.basic import *  # noqa

main()
