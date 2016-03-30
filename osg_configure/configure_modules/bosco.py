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


    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(BoscoConfiguration, self).__init__(*args, **kwargs)
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
                        'max_jobs':
                            configfile.Option(name='max_jobs',
                                              requred=configfile.Option.OPTIONAL,
                                              default_value=1000)}
                                              
        
        self.config_section = "BOSCO"
        self.log("BoscoConfiguration.__init__ completed")
        
        
    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(BoscoConfiguration, self).parse_configuration(configuration)

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
            
        #if not validation.valid_domain(self.options['endpoint'].value):
        #    attributes_ok = False
        #    self.log("Endpoint is not a valid hostname: %s" % 
        #             (self.options['endpoint'].value),
        #             option='endpoint',
        #             section=self.config_section,
        #             level=logging.ERROR)
        
        if self.options['batch'].value not in ['pbs', 'lsf', 'sge', 'condor', 'slurm']:
            attributes_ok = False
            self.log("Batch attribute is not valid: %s" % 
                     (self.options['batch'].value),
                     option='batch',
                     section=self.config_section,
                     level=logging.ERROR)
        
        # Change the  batch value to pbs if it slurm, for now
        if self.options['batch'].value is 'slurm':
            self.options['batch'].value = 'pbs'
        
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
                self.log('Installtion of Bosco failed', level=logging.ERROR)
                return False
        
        # Step 3. Configure the routes so the default route will go to the Bosco
        # installed remote cluster.
        self._install_routes()
        
        
        self.log('BoscoConfiguration.configure completed')
        return True
        
    def _installBosco(self, username):
        """
        Install Bosco on the remote cluster for a given username
        """
        
        # First, get the uid of the username so we can seteuid
        try:
            user_info = pwd.getpwnam(username)
        except KeyError, e:
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
        if not os.path.samefile(ssh_key, ssh_key_loc):
            try:
                shutil.copy(ssh_key, ssh_key_loc)
            except OSError as err:
                self.log("Error copying SSH key to %s: %s" % (ssh_key_loc, err), level=logging.ERROR)
                return False

        os.chmod(ssh_key_loc, stat.S_IRUSR | stat.S_IWUSR)

        # Add a section to .ssh/config for this host
        config_path = os.path.join(user_home, ".ssh", "config")
        #  Split the entry point by the "@"
        (username, host) = self.options["endpoint"].value.split('@')
        host_config = """
Host %(host)s
    HostName %(host)s
    User %(username)s
    IdentityFile %(key_loc)s
""" % {'host': host, 'username': user_name, 'key_loc': ssh_key_loc}

        # Search the config for the above host
        if not self._search_config(host, config_path):
            
            with open(config_path, 'a') as f:
                f.write(host_config)
        
        # Change the ownership of everything to the user
        # https://stackoverflow.com/questions/2853723/whats-the-python-way-for-recursively-setting-file-permissions
        path = os.path.join(user_home, ".ssh")  
        for root, dirs, files in os.walk(path):  
            for momo in dirs:  
                os.chown(os.path.join(root, momo), user_uid, user_gid)
            for momo in files:
                os.chown(os.path.join(root, momo), user_uid, user_gid)
        os.chown(path, user_uid, user_gid)
                
        # Function to demote to a specified uid and gid
        def demote(user_uid, user_gid):
            def result():
                os.setgid(user_gid)
                os.setuid(user_uid)
            return result
        
        try:

            # Set the user home directory
            env = os.environ.copy()
            env[ 'HOME'     ]  = user_home
            env[ 'LOGNAME'  ]  = user_name
            env[ 'USER'     ]  = user_name
            
            # Step 2. Run bosco cluster to install the remote cluster
            install_cmd = "bosco_cluster -a %(endpoint)s %(rms)s" % { 
                'endpoint': self.options['endpoint'].value,
                'rms': self.options['batch'].value}
                
            self.log("Bosco command to execute: %s" % install_cmd)
            process = subprocess.Popen(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                       preexec_fn = demote(user_uid, user_gid), env=env)
            (stdout, stderr) = process.communicate()
            returncode = process.wait()
            if returncode:
                self.log("Bosco installation command failed with exit code %i" % returncode, level=logging.ERROR)
                self.log("stdout:\n%s" % stdout, level=logging.ERROR)
                self.log("stderr:\n%s" % stderr, level=logging.ERROR)
                return False
            else:
                self.log("Bosco installation successful", level=logging.DEBUG)
                self.log("stdout:\n%s" % stdout, level=logging.DEBUG)
                self.log("stderr:\n%s" % stderr, level=logging.DEBUG)

        except Exception, e:
            self.log("Error in bosco installation: %s" % str(e), level=logging.ERROR)
            return False
            
        return True
        
        
    _route_template = """
JOB_ROUTER_ENTRIES = \\
   [ \\
     GridResource = "batch %(rms)s %(endpoint)s"; \\
     TargetUniverse = 9; \\
     name = "Local_BOSCO"; \\
   ] 
    """ 
    def _install_routes(self):
        # Install the routes in /etc/condor-ce/config.d/80-bosco-routes.conf 
        routes_file = "/etc/condor-ce/config.d/80-bosco-routes.conf"
        with open(routes_file, 'w') as routes_fd:
            routes_fd.write(self._route_template % {'rms': self.options['batch'].value, 
                                        'endpoint': self.options['endpoint'].value, 
                                        'keylocation': self.options['ssh_key'].value})
        
        
    def _search_config(self, host, config_path):
        """
        Search the ssh config file for exactly this host
        
        Returns: true - if host section found
                 false - if host section not found
        """
        
        if not os.path.exists(config_path):
            return False
        
        host_re = re.compile("^\s*Host\s+%s\s*$" % host)
        
        with open(config_path, 'r') as f:
            for line in f:
                if host_re.search(line):
                    return True
        
        return False
        
        
        
        
