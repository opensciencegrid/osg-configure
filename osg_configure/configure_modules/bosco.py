"""
Module to handle attributes related to the bosco jobmanager 
configuration
"""
import errno
import os
import logging
import subprocess
import pwd
import shutil
import stat
import re

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['BoscoConfiguration']


class BoscoConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to Bosco job manager configuration"""
    SSH_CONFIG_SECTION_BEGIN = "### THIS SECTION MANAGED BY OSG-CONFIGURE\n"
    SSH_CONFIG_SECTION_END = "### END OF SECTION MANAGED BY OSG-CONFIGURE\n"

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('BoscoConfiguration.__init__ started')
        
        # dictionary to hold information about options
        self.options = {'endpoint':
                            configfile.Option(name='endpoint',
                                              requred=configfile.Option.MANDATORY),
                        'batch':
                            configfile.Option(name='batch',
                                              requred=configfile.Option.MANDATORY),
                        'users':
                            configfile.Option(name='users',
                                              requred=configfile.Option.MANDATORY),
                        'ssh_key':
                            configfile.Option(name='ssh_key',
                                              requred=configfile.Option.MANDATORY),
                        'install_cluster':
                            configfile.Option(name='install_cluster',
                                              required=configfile.Option.OPTIONAL,
                                              default_value="if_needed"),
                        'max_jobs':
                            configfile.Option(name='max_jobs',
                                              requred=configfile.Option.OPTIONAL,
                                              default_value=1000),
                        'edit_ssh_config':
                            configfile.Option(name='edit_ssh_config',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=True),
                        'override_dir':
                            configfile.Option(name='override_dir',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='')}


        self.config_section = "BOSCO"
        self.log("BoscoConfiguration.__init__ completed")
        
        
    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super().parse_configuration(configuration)

        self.log('BoscoConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.log('Bosco section not found in config file')
            self.log('BoscoConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('BoscoConfiguration.parse_configuration completed')
            return True
            
            
        self.get_options(configuration, ignore_options=['enabled'])
        
        
    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('BoscoConfiguration.check_attributes started')
        
        attributes_ok = True
        
        if not self.enabled:
            self.log('Bosco not enabled, returning True')
            self.log('BoscoConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('BoscoConfiguration.check_attributes completed')
            return attributes_ok
            
        if self.options['batch'].value not in ['pbs', 'lsf', 'sge', 'condor', 'slurm']:
            attributes_ok = False
            self.log("Batch attribute is not valid: %s" % 
                     (self.options['batch'].value),
                     option='batch',
                     section=self.config_section,
                     level=logging.ERROR)
        
        # TODO: check if the ssh_key has the correct permissions!
        if not validation.valid_file(self.options['ssh_key'].value):
            attributes_ok = False
            self.log("ssh_key given is not a file: %s" %
                     (self.options['ssh_key'].value),
                     option='ssh_key',
                     section=self.config_section,
                     level=logging.ERROR)
        
        
        if not validation.valid_integer(self.options['max_jobs'].value):
            attributes_ok = False
            self.log("max_jobs is not an integer: %s" %
                     (self.options['max_jobs'].value),
                     option='max_jobs',
                     section=self.config_section,
                     level=logging.ERROR)
        
        # Split the users, comma seperated
        split_users = self.options['users'].value.split(',')
        for user in split_users:
            if not validation.valid_user(user.strip()):
                attributes_ok = False
                self.log("%s is not a valid user" %
                         (user.strip()),
                         option='users',
                         section=self.config_section,
                         level=logging.ERROR)

        # TODO: validate list of usernames

        endpoint = self.options['endpoint'].value
        if len(endpoint.split('@')) != 2:
            attributes_ok = False
            self.log("endpoint not in user@host format: %s" %
                     endpoint,
                     option='endpoint',
                     section=self.config_section,
                     level=logging.ERROR)

        if self.opt_val("install_cluster") not in ["always", "never", "if_needed"]:
            self.log("install_cluster attribute is not valid: %s" %
                     self.opt_val("install_cluster"),
                     option="install_cluster",
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('BoscoConfiguration.check_attributes completed')
        return attributes_ok
        
        
    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('BoscoConfiguration.configure started')
        
        if not self.enabled:
            self.log('Bosco not enabled, returning True')
            self.log('BoscoConfiguration.configure completed')
            return True

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('BoscoConfiguration.configure completed')
            return True
        
        # Do all the things here!
        
        # For each user, install bosco.
        for username in self.options['users'].value.split(","):
            username = username.strip()
            if not self._installBosco(username):
                self.log('Installation of Bosco failed', level=logging.ERROR)
                return False
        
        # Step 3. Configure the routes so the default route will go to the Bosco
        # installed remote cluster.
        self._write_route_config_vars()

        if self.htcondor_gateway_enabled:
            self.write_htcondor_ce_sentinel()

        self.log('BoscoConfiguration.configure completed')
        return True
        
    def _installBosco(self, username):
        """
        Install Bosco on the remote cluster for a given username
        """
        
        # First, get the uid of the username so we can seteuid
        try:
            user_info = pwd.getpwnam(username)
        except KeyError as e:
            self.log("Error finding username: %s on system." % username, level=logging.ERROR)
            return False
        
        user_name      = user_info.pw_name
        user_home      = user_info.pw_dir
        user_uid       = user_info.pw_uid
        user_gid       = user_info.pw_gid
        
        # Copy the ssh key to the user's .ssh directory
        ssh_key = self.options["ssh_key"].value
        ssh_key_loc = os.path.join(user_home, ".ssh", "bosco_ssh_key")
        try:
            os.mkdir(os.path.join(user_home, ".ssh"))
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
        try:
            if not os.path.exists(ssh_key_loc) or not os.path.samefile(ssh_key, ssh_key_loc):
                shutil.copy(ssh_key, ssh_key_loc)
        except OSError as err:
            self.log("Error copying SSH key to %s: %s" % (ssh_key_loc, err), level=logging.ERROR)
            return False

        os.chmod(ssh_key_loc, stat.S_IRUSR | stat.S_IWUSR)

        if self.opt_val("edit_ssh_config"):
            self.edit_ssh_config(ssh_key_loc, user_home, user_name)

        # Change the ownership of everything to the user
        # https://stackoverflow.com/questions/2853723/whats-the-python-way-for-recursively-setting-file-permissions
        path = os.path.join(user_home, ".ssh")  
        for root, dirs, files in os.walk(path):  
            for momo in dirs:  
                os.chown(os.path.join(root, momo), user_uid, user_gid)
            for momo in files:
                os.chown(os.path.join(root, momo), user_uid, user_gid)
        os.chown(path, user_uid, user_gid)

        if self.opt_val("install_cluster") == "never":
            return True

        return self._run_bosco_cluster(user_gid, user_home, user_name, user_uid)

    def _run_bosco_cluster(self, user_gid, user_home, user_name, user_uid):
        # Function to demote to a specified uid and gid
        def demote(uid, gid):
            def result():
                os.setgid(gid)
                os.setuid(uid)

            return result

        try:

            # Set the user home directory
            env = os.environ.copy()
            env['HOME'] = user_home
            env['LOGNAME'] = user_name
            env['USER'] = user_name

            endpoint = self.opt_val("endpoint")
            batch = self.opt_val("batch")

            if self.opt_val("install_cluster") == "if_needed":
                # Only install if it's not in the clusterlist
                cmd = ["bosco_cluster", "-l"]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           preexec_fn=demote(user_uid, user_gid), env=env,
                                           encoding="latin-1")
                stdout, stderr = process.communicate()
                returncode = process.returncode
                if returncode == 2:
                    self.log("Bosco clusterlist empty", level=logging.DEBUG)
                elif returncode == 0:
                    self.log("Bosco clusterlist:\n%s" % stdout, level=logging.DEBUG)
                    # Looking for a line like "bosco@submit.example.net/pbs"
                    pattern = re.compile(r"^%s/%s" % (re.escape(endpoint),
                                                      re.escape(batch)), re.MULTILINE)
                    if pattern.search(stdout):
                        self.log("Entry found in clusterlist", level=logging.DEBUG)
                        return True
                else:
                    self.log("bosco_cluster -l failed with unexpected exit code %d" % returncode, level=logging.ERROR)
                    self.log("stdout:\n%s" % stdout, level=logging.ERROR)
                    self.log("stderr:\n%s" % stderr, level=logging.ERROR)
                    return False

            # Run bosco cluster to install the remote cluster
            install_cmd = ["bosco_cluster"]
            override_dir = self.opt_val('override_dir')
            if override_dir:
                install_cmd += ['-o', override_dir]
            install_cmd += ["-a", endpoint, batch]

            self.log("Bosco command to execute: %s" % install_cmd, level=logging.DEBUG)
            process = subprocess.Popen(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       preexec_fn=demote(user_uid, user_gid), env=env,
                                       encoding="latin-1")
            stdout, stderr = process.communicate()
            returncode = process.returncode
            if returncode:
                self.log("Bosco installation command failed with exit code %i" % returncode, level=logging.ERROR)
                self.log("stdout:\n%s" % stdout, level=logging.ERROR)
                self.log("stderr:\n%s" % stderr, level=logging.ERROR)
                return False
            else:
                self.log("Bosco installation successful", level=logging.DEBUG)
                self.log("stdout:\n%s" % stdout, level=logging.DEBUG)
                self.log("stderr:\n%s" % stderr, level=logging.DEBUG)

        except Exception as e:
            self.log("Error in bosco installation: %s" % e, level=logging.ERROR)
            return False
        return True

    def edit_ssh_config(self, ssh_key_loc, local_user_home, local_user_name):
        # Add a section to .ssh/config for this host
        config_path = os.path.join(local_user_home, ".ssh", "config")
        #  Split the entry point by the "@"
        endpoint_user_name, endpoint_host = self.options["endpoint"].value.split('@')
        host_config = """
Host %(endpoint_host)s
    HostName %(endpoint_host)s
    User %(endpoint_user_name)s
    IdentityFile %(ssh_key_loc)s
""" % locals()
        text_to_add = "%s%s%s" % (self.SSH_CONFIG_SECTION_BEGIN, host_config, self.SSH_CONFIG_SECTION_END)
        if not os.path.exists(config_path):
            utilities.atomic_write(config_path, text_to_add)
            return

        config_contents = ""
        with open(config_path, "r", encoding="latin-1") as f:
            config_contents = f.read()

        section_re = re.compile(r"%s.+?%s" % (re.escape(self.SSH_CONFIG_SECTION_BEGIN), re.escape(self.SSH_CONFIG_SECTION_END)),
                                re.MULTILINE | re.DOTALL)
        host_re = re.compile(r"^\s*Host\s+%s\s*$" % re.escape(endpoint_host), re.MULTILINE)

        if section_re.search(config_contents):
            config_contents = section_re.sub(text_to_add, config_contents)
            self.logger.debug("osg-configure section found in %s", config_path)
        elif host_re.search(config_contents):
            self.logger.info("Host %s already found in %s but not in an osg-configure section. Not modifying it.", endpoint_host, config_path)
            return
        else:
            config_contents += "\n" + text_to_add

        utilities.atomic_write(config_path, config_contents)

    def _write_route_config_vars(self):
        """
        Write condor-ce config attributes for the bosco job route. Sets values for:
        - BOSCO_RMS
        - BOSCO_ENDPOINT

        """
        contents = utilities.read_file(self.HTCONDOR_CE_CONFIG_FILE,
                                       default="# This file is managed by osg-configure\n")
        contents = utilities.add_or_replace_setting(contents, "BOSCO_RMS", self.options['batch'].value,
                                                    quote_value=False)
        contents = utilities.add_or_replace_setting(contents, "BOSCO_ENDPOINT", self.options['endpoint'].value,
                                                    quote_value=False)
        utilities.atomic_write(self.HTCONDOR_CE_CONFIG_FILE, contents)

    def _search_config(self, host, config_path):
        """
        Search the ssh config file for exactly this host
        
        Returns: true - if host section found
                 false - if host section not found
        """
        
        if not os.path.exists(config_path):
            return False
        
        host_re = re.compile("^\s*Host\s+%s\s*$" % host)

        with open(config_path, "r", encoding="latin-1") as f:
            for line in f:
                if host_re.search(line):
                    return True
        
        return False
