"""Class for verifying gip information"""

import os
import re
import pwd
import logging

from osg_configure.modules import subcluster
from osg_configure.modules import exceptions
from osg_configure.modules.baseconfiguration import BaseConfiguration
from osg_configure.modules import utilities
from osg_configure.modules import validation

__all__ = ['GipConfiguration']

from osg_configure.modules.subcluster import REQUIRED, OPTIONAL, STRING, POSITIVE_INT, POSITIVE_FLOAT, LIST, BOOLEAN

OSG_ENTRIES = {
    "Site Information": ["host_name", "site_name", "sponsor", "site_policy",
                         "contact", "email", "city", "longitude", "latitude"],
    "Storage": ["app_dir", "data_dir", "worker_node_temp"],
}

SE_ENTRIES = {
    "name": (REQUIRED, STRING),
    "unique_name": (OPTIONAL, STRING),
    "srm_endpoint": (REQUIRED, STRING),
    "srm_version": (OPTIONAL, STRING),
    "transfer_endpoints": (OPTIONAL, STRING),
    "provider_implementation": (OPTIONAL, STRING),
    "implementation": (REQUIRED, STRING),
    "version": (REQUIRED, STRING),
    "default_path": (REQUIRED, STRING),
    "allowed_vos": (OPTIONAL, LIST),
    "mount_point": (OPTIONAL, LIST),
}

SE_BANNED_ENTRIES = {
    "name": "SE_CHANGEME",
    "srm_endpoint": "httpg://srm.example.com:8443/srm/v2/server",
}

# Error messages
MOUNT_POINT_ERROR = """\
You have enabled the mount_point option, but your input, %(input)s, is invalid
because of:
%(reason)s

mount_point should be enabled for sites where the SE is mounted on the worker
nodes and provides a POSIX-like interface (POSIX-like includes Lustre, HDFS,
XrootDFS, but not dCache PNFS).
The value of `mount_point` should be two paths; first, the path where the
file system is mounted on the worker nodes, followed by the exported directory
of the file system.  If you mount your file system on the worker nodes with
the following command:
  $ mount -t nfs nfs.example.com:/exported/dir /mnt/nfs
then mount_point should look like this:
   mount_point = /mnt/nfs,/exported/dir

Paths are lightly validated; they must start with "/" and contain alphanumeric
characters plus "-" or "_".
"""


class GipConfiguration(BaseConfiguration):
    """
    Class to handle attributes related to GIP.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(GipConfiguration, self).__init__(*args, **kwargs)
        self.log('GipConfiguration.__init__ started')
        self.config_section = "GIP"
        self.vo_dir = "VONAME"  # default to allowing substitution in vo_dir
        self._valid_batch_opt = ['pbs',
                                 'lsf',
                                 'condor',
                                 'sge',
                                 'slurm',
                                 'forwarding']

        self.gip_user = None
        self.log('GipConfiguration.__init__ completed')

    _check_entry = staticmethod(subcluster.check_entry)

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser
        object given by configuration and write recognized settings to attributes
        dict
        """
        self.log('GipConfiguration.parse_configuration started')

        if not utilities.rpm_installed('gip'):
            self.log('GIP not installed, disabling GIP')
            self.log('GipConfiguration.parse_configuration completed')
            self.enabled = False
            return
        else:
            self.enabled = True

        # TODO Do we want to force the user to have a GIP section? Uncomment the following if not.
        # if not configuration.has_section(self.config_section):
        #   self.log("%s section not in config file" % self.config_section)
        #   self.log('GipConfiguration.parse_configuration completed')
        #   self.enabled = False
        #   return

        self.check_config(configuration)

        self._parse_configuration(configuration)

        self.log('GipConfiguration.parse_configuration completed')

    check_subclusters = staticmethod(subcluster.check_config)

    def _parse_configuration(self, configuration):
        """
        The meat of parse_configuration, runs after we've checked that GIP is
        enabled and we have the right RPMs installed.
        """
        # The following is to set the user that gip files need to belong to
        # This can be overridden by setting the 'user' option in the [GIP] section
        self.gip_user = 'tomcat'
        if configuration.has_option(self.config_section, 'batch'):
            batch_opt = configuration.get(self.config_section, 'batch').lower()
            if (not utilities.blank(batch_opt) and
                        batch_opt not in self._valid_batch_opt):
                msg = "The batch setting in %s must be a valid option " \
                      "(e.g. %s), %s was given" % (self.config_section,
                                                   ",".join(self._valid_batch_opt),
                                                   batch_opt)
                self.log(msg, level=logging.ERROR)
                raise exceptions.SettingError(msg)

        if utilities.ce_installed():
            # All CEs must advertise subclusters
            has_sc = self.check_subclusters(configuration)
            if not has_sc:
                try:
                    self._check_entry(configuration, "GIP", "sc_number", REQUIRED,
                                      POSITIVE_INT)
                except (TypeError, ValueError, exceptions.SettingError):
                    msg = "There is no `subcluster` section and the old-style subcluster" + \
                          "setup in GIP is not configured. " + \
                          " Please see the configuration documentation."
                    raise exceptions.SettingError(msg)


        # Check for the presence of the classic SE
        has_classic_se = True
        try:
            has_classic_se = configuration.getboolean("GIP", "advertise_gsiftp")
        # pylint: disable-msg=W0702
        # pylint: disable-msg=W0703
        # pylint: disable-msg=W0704
        except Exception:
            pass

        has_se = False
        for section in configuration.sections():
            if not section.lower().startswith('se'):
                continue
            has_se = True
            self.check_se(configuration, section)
        if not has_se and not has_classic_se:
            try:
                self._check_entry(configuration, "GIP", "se_name", REQUIRED, STRING)
            except:
                msg = "There is no `SE` section, the old-style SE" + \
                      "setup in GIP is not configured, and there is no classic SE. " + \
                      " At least one must be configured.  Please see the configuration" \
                      " documentation."
                raise exceptions.SettingError(msg)
        if configuration.has_option(self.config_section, 'user'):
            username = configuration.get(self.config_section, 'user')
            if not validation.valid_user(username):
                err_msg = "%s is not a valid account on this system" % username
                self.log(err_msg,
                         section=self.config_section,
                         option='user',
                         level=logging.ERROR)
                raise exceptions.SettingError(err_msg)
            self.gip_user = username

    check_sc = staticmethod(subcluster.check_section)

    def check_se(self, config, section):
        """
        Check attributes currently stored and make sure that they are consistent
        """
        self.log('GipConfiguration.check_se started')
        attributes_ok = True

        enabled = True
        try:
            if config.has_option(section, 'enabled'):
                enabled = config.getboolean(section, 'enabled')
        # pylint: disable-msg=W0703
        except Exception:
            enabled = False

        if not enabled:
            # if section is disabled, we can exit
            return attributes_ok

        if section.lower().find('changeme') >= 0:
            msg = "You have a section named 'SE CHANGEME', but it is not turned off.\n"
            msg += "'SE CHANGEME' is an example; you must change it if it is enabled."
            raise exceptions.SettingError(msg)

        for option, value in SE_ENTRIES.items():
            status, kind = value
            entry = self._check_entry(config, section, option, status, kind)
            if option in SE_BANNED_ENTRIES and entry == SE_BANNED_ENTRIES[option]:
                raise exceptions.SettingError("Value for %s in section %s is " \
                                              "a default or banned entry (%s); " \
                                              "you must change this value." % \
                                              (option, section, SE_BANNED_ENTRIES[option]))
            if entry is None:
                continue

            # Validate the mount point information
            if option == 'mount_point':
                regex = re.compile(r"/(/*[A-Za-z0-9_\-]/*)*$")
                err_info = {'input': value}
                if len(entry) != 2:
                    err_info['reason'] = "Only one path was specified!"
                    msg = MOUNT_POINT_ERROR % err_info
                    raise exceptions.SettingError(msg)
                if not regex.match(entry[0]):
                    err_info['reason'] = "First path does not pass validation"
                    msg = MOUNT_POINT_ERROR % err_info
                    raise exceptions.SettingError(msg)
                if not regex.match(entry[1]):
                    err_info['reason'] = "Second path does not pass validation"
                    msg = MOUNT_POINT_ERROR % err_info
                    raise exceptions.SettingError(msg)

            if option == 'srm_endpoint':
                regex = re.compile(r'([A-Za-z]+)://([A-Za-z0-9_\-.]+):([0-9]+)/(.+)')
                match = regex.match(entry)
                if not match or match.groups()[3].find('?SFN=') >= 0:
                    msg = "Given SRM endpoint is not valid! It must be of the form " + \
                          "srm://<hostname>:<port>/<path>.  The hostname, port, and path " + \
                          "must be present.  The path should not contain the string '?SFN='"
                    raise exceptions.SettingError(msg)
            elif option == 'allowed_vos':
                user_vo_map = None
                if config.has_option('Install Locations', 'user_vo_map'):
                    user_vo_map = config.get('Install Locations', 'user_vo_map')
                vo_list = utilities.get_vos(user_vo_map)
                for vo in entry:
                    if vo not in vo_list:
                        msg = "The vo %s is explicitly listed in the allowed_vos list in " % vo
                        msg += "section %s, but is not in the list of allowed VOs." % section
                        if vo_list:
                            msg += "  The list of allowed VOs are: %s." % ', '.join(vo_list)
                        else:
                            msg += "  There are no allowed VOs detected; contact the experts!"
                        raise exceptions.SettingError(msg)
        self.log('GipConfiguration.check_se completed')
        return attributes_ok

    # pylint: disable-msg=W0613
    def configure(self, attributes):
        """
        Configure installation using attributes.
        """
        self.log('GipConfiguration.configure started')

        if not self.enabled:
            self.log('Not enabled, exiting...')
            self.log('GipConfiguration.configure completed')
            return

        try:
            gip_pwent = pwd.getpwnam(self.gip_user)
        except KeyError, e:
            if self.gip_user != 'tomcat':
                self.gip_user = 'tomcat'
                self.log("Couldn't find username %s, trying tomcat" % self.gip_user,
                         exception=True,
                         level=logging.WARNING)
                try:
                    gip_pwent = pwd.getpwnam(self.gip_user)
                except KeyError, e:
                    self.log("Couldn't find username %s" % self.gip_user,
                             exception=True,
                             level=logging.ERROR)
                    raise exceptions.ConfigureError("Couldn't find username %s: %s" % (self.gip_user, e))
            else:
                self.log("Couldn't find username %s" % self.gip_user,
                         exception=True,
                         level=logging.ERROR)
                raise exceptions.ConfigureError("Couldn't find username %s: %s" % (self.gip_user, e))

        (gip_uid, gip_gid) = gip_pwent[2:4]
        gip_tmpdir = os.path.join('/', 'var', 'tmp', 'gip')
        gip_logdir = os.path.join('/', 'var', 'log', 'gip')

        try:
            if not os.path.exists(gip_tmpdir):
                self.log("%s is not present, recreating" % gip_logdir)
                os.mkdir(gip_tmpdir)
            if not os.path.isdir(gip_tmpdir):
                self.log("%s is not a directory, " % gip_tmpdir +
                         "please remove it and recreate it as a directory ",
                         level=logging.ERROR)
                raise exceptions.ConfigureError("GIP tmp directory not setup: %s" % gip_tmpdir)
            os.chown(gip_tmpdir, gip_uid, gip_gid)
        except Exception, e:
            self.log("Can't set permissions on " + gip_tmpdir,
                     exception=True,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Can't set permissions on %s: %s" % (gip_tmpdir, e))

        try:
            if not os.path.exists(gip_logdir) or not os.path.isdir(gip_logdir):
                self.log("%s is not present or is not a directory, " % gip_logdir +
                         "gip did not install correctly",
                         level=logging.ERROR)
                raise exceptions.ConfigureError("GIP log directory not setup: %s" % gip_logdir)
            os.chown(gip_logdir, gip_uid, gip_gid)
        except Exception, e:
            self.log("Can't set permissions on " + gip_logdir,
                     exception=True,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Can't set permissions on %s: %s" % \
                                            (gip_logdir, e))

        self.log('GipConfiguration.configure completed')

    def module_name(self):
        """
        Return a string with the name of the module
        """
        return "GIP"

    def separately_configurable(self):
        """
        Return a boolean that indicates whether this module can be configured
        separately
        """
        return True
