"""

============ Cyberus ============

The MIT License

Copyright (c) 2023 Xavier Mercerweiss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


============ psutil ============

BSD 3-Clause License

Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola'
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither the name of the psutil authors nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


============ uptime ============

BSD 2-Clause License

Copyright (c) 2012, Koen Crolla
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import subprocess
import datetime
import pathlib

import psutil
import uptime


### General Operations ###

ARG_TOKENS = {
    "$SPACE": " "
}
detection_operations = []


def detection_operation(operation):
    """
    Adds the given function to the list of detection operations
    :param operation: The operation to be added to the list of detection operations
    """
    detection_operations.append(operation)
    return operation


def run(command, initial_input=""):
    """
    Executes a given bash command
    :param command: A bash command
    :param initial_input: A string to be passed to the command as input
    :return: The output of the command as a string
    """
    piped = bytes(initial_input, "utf-8")
    commands = (s.strip().replace("'", "") for s in command.split("|"))
    for cmd in commands:
        arguments = get_arguments(cmd)
        result = subprocess.run(arguments, stdout=subprocess.PIPE, input=piped)
        piped = result.stdout
    return piped.decode("utf-8")


def get_arguments(command):
    """
    Splits a given bash command along spaces and converts any present tokens with their mapped values
    :param command: A bash command
    :return: The detokened command split along spaces
    """
    output = []
    for arg in command.split():
        for token, value in ARG_TOKENS.items():
            arg = arg.replace(token, value)
        output.append(arg)
    return output


def is_overlap(parent, children):
    """
    Determines whether any string within the child set is a substring of the parent string
    :param parent: The parent string
    :param children: A collection of child strings to be tested
    :return: Whether any string within the child set is a substring of the parent string
    """
    for child in children:
        if child in parent:
            return True
    return False


### App Management Operations ###

@detection_operation
def banned_apps(*processes):
    """
    Yields the number of specified processes which are currently running
    :param processes: A list of process names
    """
    banned_set = set(processes)
    while True:
        running_set = get_running_apps()
        yield len(banned_set & running_set)


@detection_operation
def allowed_apps(*processes):
    """
    Yields the number of processes other than specified processes which are currently running
    :param processes: A list of process names
    """
    allowed_set = set(processes)
    while True:
        running_set = get_running_apps()
        yield len(running_set - allowed_set)


def get_running_apps():
    """
    Determines the names of all processes currently running
    :return: The names of all currently running processes as a set
    """
    return set(i.name() for i in psutil.process_iter())


### Time Management Operations ###

@detection_operation
def expected_uptime(expected):
    """
    Yields 1 if the current system uptime is greater than that expected, yields 0 otherwise
    :param expected: The expected system uptime in seconds
    """
    while True:
        observed = uptime.uptime()
        yield int(observed > expected)


@detection_operation
def expected_hours(start, stop):
    """
    Yields 1 if the current system time is beyond the expected time range, yields 0 otherwise
    :param start: The start of the expected time range in ISO format
    :param stop: The end of the expected time range in ISO format
    """
    start_time = datetime.time.fromisoformat(start)
    stop_time = datetime.time.fromisoformat(stop)
    while True:
        current_time_iso_format = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")
        current_time = datetime.time.fromisoformat(current_time_iso_format)
        yield int(not start_time <= current_time <= stop_time)


### User Management Operations ###

@detection_operation
def banned_users(*users):
    """
    Yields the number of specified users which currently exist on the system
    :param users: A list of usernames
    """
    banned_set = set(users)
    while True:
        current_set = get_users()
        yield len(banned_set & current_set)


@detection_operation
def allowed_users(*users):
    """
    Yields the number of users which currently exist on the system other than the specified users
    :param users: A list of usernames
    """
    allowed_set = set(users)
    while True:
        current_set = get_users()
        yield len(current_set - allowed_set)


@detection_operation
def admin_users(*users):
    """
    Yields the number of users in the 'admin' group which do not exist in the specified user set plus the number of
    users in the specified set which are not in the 'admin' group.
    :param users: A list of usernames
    """
    authorized_admin = set(users)
    while True:
        observed_admin = get_admin_users()
        yield len(authorized_admin.symmetric_difference(observed_admin))
        # In this context, symmetric difference will return both admin who do not have admin
        # privileges (authorized - observed) and non-admin users who have admin rights (observed - authorized)


def get_non_admin_users():
    """
    :return: A set of all human users which are not admin
    """
    admin_set = get_admin()
    users_set = get_users()
    return users_set - admin_set


def get_admin_users():
    """
    :return: A set of all human users which are admin
    """
    admin_set = get_admin()
    users_set = get_users()
    return admin_set & users_set


def get_admin():
    """
    :return: A set of users in the 'admin' group
    """
    return set(
        a.strip() for a in
        run("grep admin /etc/group | cut -d: -f4").split(",")
        if a.strip() != ""
    )


def get_users():
    """
    :return: A set of all human users
    """
    return set(
        u.strip() for u in
        run("cut -d: -f1,3 /etc/passwd | egrep ':[0-9]{4}$' | cut -d: -f1").split("\n")
        if u.strip() != ""
    )


### Connection Management Operations ###

INCOMING_SERVICE_TO_PORT = {
    "ftp":   20,
    "ssh":   22,
    "smtp":  25,
    "http":  80,
    "https": 443,
    "rdp":   3389,
}


OUTGOING_SERVICE_TO_PORT = {
    "ftp":   21,
    "ssh":   22,
    "smtp":  25,
    "http":  80,
    "https": 443,
    "rdp":   3389,
}


@detection_operation
def banned_connections(*connections):
    """
    Yields the number of currently connected IPs which exist in the specified set
    :param connections: A list of IP addresses (Any format)
    """
    banned_set = set(connections)
    while True:
        current_connections, _ = get_incoming_connections()
        current_set = set(current_connections)
        yield len(banned_set & current_set)


@detection_operation
def allowed_connections(*connections):
    """
    Yields the number of currently connected IPs other than those which exist in the specified set
    :param connections: A list of IP addresses (Any format)
    """
    allowed_set = set(connections)
    while True:
        current_connections, _ = get_incoming_connections()
        current_set = set(current_connections)
        yield len(current_set - allowed_set)


@detection_operation
def banned_ports(*ports):
    """
    Returns the number of currently connected ports or services which exist in the specified set
    :param ports: A list of ports or services
    """
    banned_set = set(INCOMING_SERVICE_TO_PORT[port.lower()] if port in INCOMING_SERVICE_TO_PORT else port for port in ports)
    banned_set.update(set(OUTGOING_SERVICE_TO_PORT[port.lower()] for port in ports if port in OUTGOING_SERVICE_TO_PORT))
    while True:
        _, incoming_ports = get_incoming_connections()
        _, outgoing_ports = get_outgoing_connections()
        current_set = incoming_ports | outgoing_ports
        yield len(banned_set & current_set)


@detection_operation
def allowed_ports(*ports):
    """
    Returns the number of currently connected ports or services other than those which exist in the specified set
    :param ports: A list of ports or services
    """
    allowed_set = set(
        INCOMING_SERVICE_TO_PORT[port.lower()] if port in INCOMING_SERVICE_TO_PORT else int(port) for port in ports
    )
    allowed_set.update(
        set(
            INCOMING_SERVICE_TO_PORT[port.lower()] if port in INCOMING_SERVICE_TO_PORT else int(port) for port in ports
        )
    )
    while True:
        _, incoming_ports = get_incoming_connections()
        _, outgoing_ports = get_outgoing_connections()
        current_set = incoming_ports | outgoing_ports
        yield len(current_set - allowed_set)


def get_incoming_connections():
    """
    Determines all incoming ports and IP connections
    :return: A set of all incoming IP connections as strings, a set of all incoming ports as integers
    """
    connections = list(c.strip() for c in run("ss | grep tcp | cut -c 102-").split("\n") if c.strip() != "")
    ips, ports = set(), set()
    for connection in connections:
        *head, foot = connection.split(":")
        ip = ":".join(head)
        port = INCOMING_SERVICE_TO_PORT[foot] if foot in INCOMING_SERVICE_TO_PORT else int(foot)
        ips.add(ip)
        ports.add(port)
    return ips, ports


def get_outgoing_connections():
    """
    Determines all incoming ports and IP connections
    :return: A set of all outgoing IP connections as strings, a set of all outgoing ports as integers
    """
    connections = list(c.strip() for c in run("ss | grep tcp | cut -c 77-102").split("\n") if c.strip() != "")
    ips, ports = set(), set()
    for connection in connections:
        *head, foot = connection.split(":")
        ip = ":".join(head)
        port = INCOMING_SERVICE_TO_PORT[foot] if foot in INCOMING_SERVICE_TO_PORT else int(foot)
        ips.add(ip)
        ports.add(port)
    return ips, ports


### File Management Operations ###

PATH_TOKENS = {
    "~": "/home/$USER"
}

OMITTED = (
    "pipe",
    "/bin",
    "/dev",
    "/var",
    "/lib",
    "/tmp",
    "/run",
    "type=",
    "/proc",
    "/memfd",
    "/usr/lib",
    "/usr/bin",
    "/usr/share",
    "/var/cache",
)


@detection_operation
def user_accessible(path):
    """
    Yields the number of files/directories currently accessed by the user which exist outside the specified directory
    :param path: A path to any directory
    """
    users = get_admin_users()
    user_directories = {
        u: resolve_path_for_user(path, u)
        for u in users
    }
    while True:
        violations = 0
        for user, directory in user_directories.items():
            accessing = [pathlib.Path(p) for p in get_open_files(user)]
            violations += sum(
                int(directory not in a.parents)
                for a in accessing
                if directory not in a.parents and a != directory
            )
        yield violations


def resolve_path_for_user(path, user):
    """
    Detokens and resolves a given path based on a given user
    :param path: A path to a file/directory
    :param user: A given user
    :return: The resolved path
    """
    detokened = path
    for token, value in PATH_TOKENS.items():
        detokened = detokened.replace(token, value)
    detokened = detokened.replace("$USER", user)
    return pathlib.Path(detokened).resolve()


def get_open_files(user):
    """
    Returns a set of all files currently accessed by a given user other than those omitted due to technical reasons
    (see OMITTED tuple)
    :param user: A given user
    """
    return set(
        f for f in
        run(f'lsof -w -c smbd -u {user} | tr -s $SPACE | cut -d$SPACE -f9 | grep /').split("\n")[1:]
        if f.strip() != "" and not is_overlap(f, OMITTED)
    )


### Finalization ###

DETECTION_OPERATIONS = tuple(detection_operations)
