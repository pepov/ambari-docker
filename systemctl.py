#!/usr/bin/env python2
from __future__ import print_function
import sys
import subprocess

PG_ENV = {
    "PGDATA": "/var/lib/pgsql/data",
    "PGPORT": "5432"
}
STATUS_CMD = 'su postgres -c "/usr/bin/pg_ctl status -D ${PGDATA}"'
START_CMD = 'su postgres -c "/usr/bin/postgresql-check-db-dir ${PGDATA} && /usr/bin/pg_ctl start -D ${PGDATA} -s -o \\"-p ${PGPORT}\\" -w -t 300 > /tmp/pgsql.log"'
STOP_CMD = 'su postgres -c "/usr/bin/pg_ctl stop -D ${PGDATA} -s -m fast"'

args = sys.argv[1:]

if args == ['show', '-p', 'Environment', 'postgresql.service']:
    print("Environment=PGPORT=5432")
    print("Environment=PGDATA=/var/lib/pgsql/data")
    sys.exit(0)

if args == ['status', 'postgresql']:
    try:
        output = subprocess.check_output(
            STATUS_CMD,
            shell=True,
            env=PG_ENV,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        output = e.output
    if "pg_ctl: no server running" in output:
        print("stopped")
        sys.exit(3)
    if "pg_ctl: server is running" in output:
        print("running")
        sys.exit(0)

if args == ['start', 'postgresql']:
    try:
        output = subprocess.check_output(
            START_CMD,
            shell=True,
            env=PG_ENV,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        print(e.output)
        sys.exit(3)
    sys.exit(0)

if args == ['stop', 'postgresql']:
    try:
        output = subprocess.check_output(
            STOP_CMD,
            shell=True,
            env=PG_ENV,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        if "PID file" in e.output and "does not exist" in e.output:
            sys.exit(0)
        else:
            print(e.output)
            sys.exit(3)
    sys.exit(0)

print("systemctl wrapper does not support arguments {args}".format(args=args))
sys.exit(-1)
