# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import importutils
from oslo_log import log
import time
import subprocess
drac_exceptions = importutils.try_import('dracclient.exceptions')

LOG = log.getLogger(__name__)

def _ping_host(host):
    response = subprocess.call(
        "ping -c 1 {} 2>&1 1>/dev/null".format(host), shell=True)
    return (response == 0)

def wait_for_host_state(host,
                        alive=True,
                        ping_count=3,
                        retries=24):
    if alive:
        ping_type = "pingable"

    else:
        ping_type = "not pingable"

    LOG.info("Waiting for the iDRAC %s to become %s" % (host,ping_type))

    response_count = 0
    state_reached = False

    while retries > 0 and not state_reached:
        response = _ping_host(host)
        retries -= 1
        if response == alive:
            response_count += 1
            LOG.debug("The iDRAC for node %s is %s, count=%s",
                      host,
                      ping_type,
                      response_count)
            if response_count == ping_count:
                LOG.debug("Reached specified ping count for node %s" % host)
                state_reached = True
        else:
            response_count = 0
            if alive:
                LOG.debug("The iDRAC for node %s is still not pingable" % host)
            else:
                LOG.debug("The iDRAC for node %s is still pingable" % host)
        time.sleep(10)

    return state_reached

def wait_for_host(host):
    LOG.debug("iDRAC was reset for node %s,"
                "waiting for return to operational state" % host)
    state_reached = wait_for_host_state(
                            host,
                            alive=False,
                            ping_count=2,
                            retries=24)

    if not state_reached:
        error_msg = ("Timed out waiting for the %s iDRAC to become "
                    "not pingable" % host)
        LOG.error(error_msg)
        raise exceptions.DRACOperationFailed(drac_messages=error_msg)

    LOG.info("The iDRAC %s has become not pingable" % host)

    state_reached = wait_for_host_state(
        host,
        alive=True,
        ping_count=3,
        retries=24)
    if not state_reached:
        error_msg = ("Timed out waiting for the %s iDRAC to become "
                    "pingable" % host)
        LOG.error(error_msg)
        raise exceptions.DRACOperationFailed(drac_messages=error_msg)

    LOG.info("The iDRAC %s has become pingable" % host)

def wait_until_idrac_is_ready(oem_manager, host, retries, retry_delay):
    """Waits until the iDRAC is in a ready state
    :param retries: The number of times to check if the iDRAC is
                    ready.
    :param retry_delay: The number of seconds to wait between
                        retries.
    """

    while retries > 0:
        LOG.debug("Checking to see if the iDRAC %s is ready" % host)

        if oem_manager.is_idrac_ready():
            LOG.debug("The iDRAC %s is ready" % host)
            return

        LOG.debug("The iDRAC %s is not ready" % host)
        retries -= 1
        if retries > 0:
            time.sleep(retry_delay)

    if retries == 0:
        error_msg = ("Timed out waiting for the iDRAC %s "
                    "to become ready after reset" %
                    host)
        LOG.error(error_msg)
        raise exceptions.DRACOperationFailed(drac_messages=error_msg)
