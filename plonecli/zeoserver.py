# -*- coding: utf-8 -*-
"""zeocltl -- control a ZEO server using zdaemon.

Usage: zeocltl [options] [action [arguments]]

Options:
-h/--help -- print usage message and exit

Actions are commands like "start", "stop" and "status". If -i is specified or
no action is specified on the command line, a "shell" interpreting actions
typed interactively is started. Use the action "help" to find out about
available actions. """

from ZEO import runzeo
from ZEO import zeoctl

import os
import sys


if sys.platform[:3].lower() == "win":
    print('For win32 platforms, runzeo.bat or zeoservice.exe should be used')
    print('%s is based on zdaemon, which is Linux specific' % sys.argv[0])
    print('Aborting...')
    sys.exit(0)


def main(args=None):
    # When we detect Supervisord we need to make sure we do not fork a
    # sub process since Supervisord does not like that
    if 'SUPERVISOR_ENABLED' in os.environ:
        # We will ignore any command sent and always start in foreground mode
        args = args[:2]
        runzeo.main(args)
    else:
        zeoctl.main(args)
