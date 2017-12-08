# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006-2007 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""zopectl -- control Zope using zdaemon.

Usage: zopectl [options] [action [arguments]]

Options:
-h/--help -- print usage message and exit
-i/--interactive -- start an interactive shell after executing commands
action [arguments] -- see below

Actions are commands like "start", "stop" and "status". If -i is specified or
no action is specified on the command line, a "shell" interpreting actions
typed interactively is started. Use the action "help" to find out about
available actions.
"""

from pkg_resources import iter_entry_points
from Zope2.Startup import zopectl

import csv
import os
import os.path
import sys


if zopectl.WIN:
    import traceback
    from pkg_resources import resource_filename
    import pywintypes
    import win32api
    from win32com.shell import shell
    import win32con
    import win32service
    import win32serviceutil

    ERR_MSG_NOT_ADMIN = (
        'ERROR: You are not member of the "Administrators" group, '
        'or you have not run the shell as Administrator.')


class AdjustedZopeCmd(zopectl.ZopeCmd):

    if zopectl.WIN:

        # printable representations of the Windows service states
        service_state_map = {
            win32service.SERVICE_START_PENDING: 'starting',
            win32service.SERVICE_RUNNING:       'started',
            win32service.SERVICE_STOP_PENDING:  'stopping',
            win32service.SERVICE_STOPPED:       'stopped',
        }

        def is_user_admin(self):
            # http://msdn.microsoft.com/en-us/library/bb776463%28VS.85%29.aspx:
            # " This function is available through Windows Vista. It might be
            #   altered or unavailable in subsequent versions of Windows."
            # It's still available in Windows 7, but we should consider using
            # CheckTokenMembership() instead in a later Plone version.
            return shell.IsUserAnAdmin()

        def _get_pid_from_pidfile(self):
            fname = self.options.configroot.pid_filename
            if os.path.exists(fname):
                with open(fname) as f:
                    try:
                        return int(f.read().strip())
                    except ValueError:
                        # pid file for any reason empty or corrupt
                        print('ERROR: Corrupt pid file: {}'.format(fname))
                        return 0
            else:
                return 0

        def _get_service_name(self):
            return 'Zope%s' % str(hash(self.options.directory.lower()))

        def _get_service_status(self):
            """ Return status of Windows service, or None if not installed.

            Possible status values are:

            win32service.SERVICE_START_PENDING
            win32service.SERVICE_RUNNING
            win32service.SERVICE_STOP_PENDING
            win32service.SERVICE_STOPPED

            """
            name = self._get_service_name()
            try:
                status = win32serviceutil.QueryServiceStatus(name)[1]
            except pywintypes.error as err:
                # (1060, 'GetServiceKeyName', 'The specified service does not
                # exist as an installed service.')
                if err[0] == 1060:
                    return None
                else:
                    # be lazy: don't bother to take care of unexpected errors
                    traceback.print_exc()
            return status

        def _get_service_class_string(self):
            return '%s.Service' % resource_filename(
                'nt_svcutils', 'service')

        def _set_winreg_key(self, name, value, keyname='PythonClass'):
            # see "collective.buildout.cluster.ClusterBase"
            # TODO: use Python module "_winreg"

            def open_key(keyname=None):
                keypath = ('System\\CurrentControlSet\\Services\\' +
                           self._get_service_name())
                if keyname:
                    keypath += ('\\' + keyname)
                return win32api.RegOpenKey(
                    win32con.HKEY_LOCAL_MACHINE,
                    keypath,
                    0,
                    win32con.KEY_ALL_ACCESS)

            key = open_key(keyname)
            try:
                win32api.RegSetValueEx(key,
                                       name,
                                       0,
                                       win32con.REG_SZ,
                                       value)
            finally:
                win32api.RegCloseKey(key)

        def do_install(self, arg):
            # see "collective.buildout.cluster.base.ClusterBase.install()"

            if not shell.IsUserAnAdmin():
                print(ERR_MSG_NOT_ADMIN)
                return

            status = self._get_service_status()
            if status is not None:
                print('ERROR: Zope is already installed as a Windows service.')
                return

            # TODO:
            # Are return values from do_ methods are really taken care of?
            # http://docs.python.org/library/cmd.html: "The return value is a
            # flag indicating whether interpretation of commands
            # by the interpreter should stop."

            ret_code = 0

            class_string = self._get_service_class_string()
            name = self._get_service_name()
            display_name = 'Zope instance at ' + self.options.directory

            if arg.lower() == 'auto':
                start_type = win32service.SERVICE_AUTO_START
            else:
                start_type = win32service.SERVICE_DEMAND_START

            try:
                win32serviceutil.InstallService(class_string,
                                                name,
                                                display_name,
                                                start_type)

                # put info in registry for the Windows Service class to use:

                instance_script = self.options.progname
                # for example
                #     'D:\\local\\Plone-4.0b5\\bin\\instance-script.py'
                # but the Windows Service must launch
                #     'D:\\local\\Plone-4.0b5\\bin\\instance.exe'
                script_suffix = '-script.py'
                pos = instance_script.rfind(script_suffix)
                instance_exe = instance_script[:pos] + '.exe'

                self._set_winreg_key(
                    'command',
                    '"%s" console' % instance_exe
                )
                self._set_winreg_key(
                    'pid_filename',
                    self.options.configroot.pid_filename
                )

                print('Installed Zope as Windows Service "{}".'.format(name))

            except pywintypes.error:
                traceback.print_exc()
                ret_code = 1

            return ret_code

        def help_install(self):
            print('install -- Install Zope as a Windows service that must be '
                  'manually started.')
            print('install auto -- Install Zope as a Windows service that '
                  'starts at system startup.')

        def do_start(self, arg):

            if not shell.IsUserAnAdmin():
                print(ERR_MSG_NOT_ADMIN)
                return

            status = self._get_service_status()
            if status is None:
                print('ERROR: Zope is not installed as Windows service.')
                return
            elif status == win32service.SERVICE_START_PENDING:
                print('ERROR: The Zope Windows service is about to start.')
                return
            elif status == win32service.SERVICE_RUNNING:
                print('ERROR: The Zope Windows service is already running.')
                return
            name = self._get_service_name()
            try:
                win32serviceutil.StartService(name)
                print('Starting Windows Service "{}".'.format(name))
            except pywintypes.error:
                traceback.print_exc()

        def do_restart(self, arg):

            if not shell.IsUserAnAdmin():
                print(ERR_MSG_NOT_ADMIN)
                return

            status = self._get_service_status()
            if status is None:
                print('ERROR: Zope is not installed as Windows service.')
                return
            elif status == win32service.SERVICE_STOPPED:
                print('ERROR: The Zope Windows service has not been started.')
                return
            name = self._get_service_name()
            try:
                win32serviceutil.RestartService(name)
                print('Restarting Windows Service "{}".'.format(name))
            except pywintypes.error:
                traceback.print_exc()

        def do_stop(self, arg):

            if not shell.IsUserAnAdmin():
                print(ERR_MSG_NOT_ADMIN)
                return

            status = self._get_service_status()
            if status is None:
                print('ERROR: Zope is not installed as Windows service.')
                return
            elif status == win32service.SERVICE_STOPPED:
                print('ERROR: The Zope Windows service has not been started.')
                return
            name = self._get_service_name()
            try:
                win32serviceutil.StopService(name)
                print('Stopping Windows Service "{}".'.format(name))
            except pywintypes.error:
                traceback.print_exc()

        def do_remove(self, arg):

            if not shell.IsUserAnAdmin():
                print(ERR_MSG_NOT_ADMIN)
                return

            status = self._get_service_status()
            if status is None:
                print('ERROR: Zope is not installed as a Windows service.')
                return
            elif status is not win32service.SERVICE_STOPPED:
                print('ERROR: Please stop the Windows service before '
                      'removing it.')
                return

            ret_code = 0
            name = self._get_service_name()
            try:
                win32serviceutil.RemoveService(name)
                print('Removed Windows Service "{}".'.format(name))
            except pywintypes.error:
                ret_code = 1
                traceback.print_exc()

            return ret_code

        # NOTE: do not rename! called also on windows by non-windows
        # "do_" methods
        def get_status(self):
            """This method only has side effects, despite its name:

            - Set "self.zd_pid" to the PID (0 if no PID found), based on
            the content of the PID file, e.g. "var/instance.pid".
            This value is checked by the startup machinery of Zope.

            - Set "self.zd_up" to 1 or 0 (unclear what this is used for)

            """
            zopectl.ZopeCmd.get_status(self)
            # override value set by zopectl.ZopeCmd.get_status()
            # (always -1 or 0)
            self.zd_pid = self._get_pid_from_pidfile()

            if self.zd_pid > 0:
                self.zd_up = 1
            else:
                self.zd_up = 0

        def do_status(self, arg=''):
            if arg not in ('', '-l'):
                print('ERROR: The only valid option is "-l".')
                return
            service_status = self._get_service_status()
            if service_status is None:
                print('Zope is not installed as a Windows service.')
            else:
                name = self._get_service_name()
                state = self.service_state_map.get(
                    service_status, 'in an unknown state')
                print('Zope is installed as Windows service "%s", '
                      'this service is currently %s.' % (name, state))
            if arg == '-l' and self.zd_status:
                print(self.zd_status)

            # TODO: what about "self.zd_up"?

        def help_status(self):
            print('status -- Print status of the Windows service.')
            print(
                'status -l -- Print status of the Windows service, '
                'and raw status output.'
            )

        def help_EOF(self):
            print('To quit, type CTRL+Z or use the quit command.')

    # end of "if zopectl.WIN"
    else:

        def do_start(self, arg):
            self.get_status()
            if not self.zd_up:
                args = [
                    self.options.python,
                    self.options.zdrun,
                ]
                args += self._get_override("-S", "schemafile")
                args += self._get_override("-C", "configfile")
                args += self._get_override("-b", "backofflimit")
                args += self._get_override("-d", "daemon", flag=1)
                args += self._get_override("-f", "forever", flag=1)
                args += self._get_override("-s", "sockname")
                args += self._get_override("-u", "user")
                if self.options.umask:
                    args += self._get_override("-m", "umask",
                                               oct(self.options.umask))
                args += self._get_override(
                    "-x", "exitcodes",
                    ",".join(map(str, self.options.exitcodes))
                )
                args += self._get_override("-z", "directory")

                args.extend(self.options.program)

                if self.options.daemon:
                    flag = os.P_NOWAIT
                else:
                    flag = os.P_WAIT
                env = self.environment().copy()
                env.update({'ZMANAGED': '1', })
                os.spawnvpe(flag, args[0], args, env)
            elif not self.zd_pid:
                self.send_action("start")
            else:
                print('daemon process already running; pid={}'.format(
                    self.zd_pid))
                return

            def cond(n=0):
                return self.zd_pid

            self.awhile(
                cond,
                'daemon process started, pid=%(zd_pid)d'
            )

    def environment(self):
        configroot = self.options.configroot
        env = dict(os.environ)
        try:
            shome = configroot.softwarehome
        except AttributeError:
            shome = None
            shome  # pyflakes
        env.update({'INSTANCE_HOME': configroot.instancehome})
        return env

    def get_startup_cmd(self, python, more, pyflags=""):
        # If we pass the configuration filename as a win32
        # backslashed path using a ''-style string, the backslashes
        # will act as escapes.  Use r'' instead.
        # Also, don't forget that 'python'
        # may have spaces and needs to be quoted.
        cmdline = (
            '"%s" %s %s -c "from Zope2 import configure; '
            'configure(r\'%s\'); '
            'import Zope2; app=Zope2.app(); ' % (
                python, pyflags,
                pyflags,
                self.options.configfile
            )
        )

        if not self.options.no_request:
            cmdline += (
                'from Testing.ZopeTestCase.utils import makerequest; '
                'app = makerequest(app); '
                # REQUEST.traverse needs this but no reason not to set
                # this even if we're not traversing to an object
                'app.REQUEST[\'PARENTS\'] = [app]; '
                # five.globalrequest does setRequest at IPubStart
                # which is called outside of REQUEST.traverse
                'from zope.globalrequest import setRequest ;'
                'setRequest(app.REQUEST); ')
        # Need to login at different points depending on REQUEST.traverse
        login_cmdline = (
            'from AccessControl.SpecialUsers import system as user; '
            'from AccessControl.SecurityManagement import newSecurityManager; '
            'newSecurityManager(None, user); ')
        if self.options.object_path:
            if not self.options.no_request:
                cmdline += (
                    # populate the request, setSite, skin, theme, etc.
                    'app.REQUEST.traverse(r\'%s\'); '
                    % self.options.object_path)
            if not self.options.no_login:
                # REQUEST.traverse will do setSecurityManager with Anonymous
                # so we login after
                cmdline += login_cmdline
            cmdline += (
                'obj = app.restrictedTraverse(r\'%s\'); '
                % self.options.object_path)
        elif not self.options.no_login:
            # Login if we're not getting a object and we don't need to
            # worry about REQUEST.traverse
            cmdline += login_cmdline

        cmdline = cmdline + more + '\"'
        if zopectl.WIN:
            # entire command line must be quoted
            # as well as the components
            return '"%s"' % cmdline
        else:
            return cmdline

    def help_startup_command(self):
        print("""\
    Also sets up a REQUEST, logs in the
    AccessControl.SpecialUsers.system user, and may traverse
    to an object, such as a CMF portal.  This environment set
    up is controlled with following options:
    -R/--no-request -- do not set up a REQUEST.
    -L/--no-login -- do not login the system user.
    -O/--object-path <path> -- Traverse to <path> from the app
                               and make available as `obj`.
    Example usage: bin/instance -RLOPlone/front-page debug""")

    def do_run(self, arg):
        # If the command line was something like
        # """bin/instance run "one two" three"""
        # cmd.parseline will have converted it so
        # that arg == 'one two three'. This is going to
        # foul up any quoted command with embedded spaces.
        # So we have to return to self.options.args,
        # which is a tuple of command line args,
        # throwing away the "run" command at the beginning.
        #
        # Further complications: if self.options.args has come
        # via subprocess, it may look like
        # ['run "arg 1" "arg2"'] rather than ['run','arg 1','arg2'].
        # If that's the case, we'll use csv to do the parsing
        # so that we can split on spaces while respecting quotes.
        if len(self.options.args) == 1:
            tup = next(csv.reader(self.options.args, delimiter=' '))[1:]
        else:
            tup = self.options.args[1:]

        if not tup:
            print("usage: run <script> [args]")
            return

        # If we pass the script filename as a win32 backslashed path
        # using a ''-style string, the backslashes will act as
        # escapes.  Use r'' instead.
        #
        # Remove -c and add script as sys.argv[0]
        script = tup[0]
        cmd = 'import sys; sys.argv.pop(); sys.argv.append(r\'%s\'); ' % script
        if len(tup) > 1:
            argv = tup[1:]
            cmd += '[sys.argv.append(x) for x in %s]; ' % argv
        cmd += 'execfile(r\'%s\')' % script
        cmdline = self.get_startup_cmd(self.options.python, cmd)

        self._exitstatus = os.system(cmdline)

    def help_run(self):
        zopectl.ZopeCmd.help_run(self)
        self.help_startup_command()

    def do_console(self, arg):
        self.do_foreground(arg, debug=False)

    def help_console(self):
        print("""\
console -- Run the program in the console.
    In contrast to foreground this does not turn on debug mode.""")

    def do_debug(self, arg):
        # `-c` disables the PYTHONSTARTUP feature; load it explicitly
        interactive_startup = (
            "import os;"
            "os.path.exists(os.environ.get('PYTHONSTARTUP', '')) "
            "and execfile(os.environ['PYTHONSTARTUP']); del os;"
        )
        cmdline = self.get_startup_cmd(
            self.options.python,
            interactive_startup,
            pyflags='-i',
        )
        print('Starting debugger (the name "app" is bound to the top-level '
              'Zope object)')
        os.system(cmdline)

    def help_debug(self):
        zopectl.ZopeCmd.help_debug(self)
        self.help_startup_command()

    def do_foreground(self, arg, debug=True):
        self.get_status()
        pid = self.zd_pid
        if pid:
            print(
                'The program seems already to be running. If you believe not, '
                'check for dangling .pid and .lock files in var/.'
            )
            return

        import subprocess
        env = self.environment()
        program = self.options.program
        local_additions = []

        if debug:
            if not program.count('-X'):
                local_additions += ['-X']
            if not program.count('debug-mode=on'):
                local_additions += ['debug-mode=on']
            program.extend(local_additions)

        if zopectl.WIN:
            # The outer quotes were causing
            # "WindowsError: [Error 87] The parameter is incorrect"
            # command = zopectl.quote_command(program)
            command = ' '.join(['"%s"' % x for x in program])
        else:
            command = program

        if debug or zopectl.WIN:
            try:
                self._exitstatus = subprocess.call(command, env=env)
            except KeyboardInterrupt:
                return
            finally:
                for addition in local_additions:
                    program.remove(addition)
        else:
            # non-debug mode on Unix: replace the current process
            # (required by e.g. supervisord)
            os.execve(program[0], command, env)

    def do_test(self, arg):
        print("The test command is no longer supported. Please use a "
              "zc.recipe.testrunner section in your buildout config file "
              "to get a test runner for your environment. Most often you "
              "will name the section `test` and can run tests via: "
              "bin/test -s <my.package>")
        return


def main(args=None):
    """Customized entry point for launching Zope without forking other processes
    """

    options = zopectl.ZopeCtlOptions()
    options.add(name="no_request", short="R", long="no-request", flag=1)
    options.add(name="no_login", short="L", long="no-login", flag=1)
    options.add(name="object_path", short="O:", long="object-path=")
    # Realize arguments and set documentation which is used in the -h option
    options.realize(args, doc=__doc__)

    # Change the program to avoid warning messages
    options.program = [
        options.python, '-m', 'Zope2.Startup.run', '-C', options.configfile]

    # We use our own ZopeCmd set, that is derived from the original one.
    c = AdjustedZopeCmd(options)

    # Mix in any additional commands supplied by other packages:
    for ep in iter_entry_points('plone.recipe.zope2instance.ctl'):
        func_name = 'do_' + ep.name
        func = ep.load()
        # avoid overwriting the standard commands
        if func_name not in dir(c):
            setattr(c.__class__, func_name, func)

    # If a command was specified: call the corresponding do_*() method.
    #
    # If that method set an exit status, exit this Python script
    # with exit status 1 ("abnormal termination"). Otherwise use the
    # default exit code 0 ("successful termination").
    #
    # The exit status is used for "Restart" on the ZMI Control Panel or
    # @@maintenance-controlpanel (see http://dev.plone.org/plone/ticket/10906).
    #
    # Arguably we should return the exit status and let the wrapper script
    # exit.
    # But it's generated by setuptools, and doesn't have that functionality.

    if options.args:
        c.onecmd(' '.join(options.args))
        sys.exit(min(c._exitstatus, 1))

    # If no command was specified: enter interactive mode.

    try:
        import readline
        assert readline
    except ImportError:
        pass
    print('Program: {}'.format(' '.join(options.program)))
    c.do_status()
    c.cmdloop()
