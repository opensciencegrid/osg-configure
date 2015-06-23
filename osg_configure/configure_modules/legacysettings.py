""" Module to handle legacy attributes """

from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import configfile

__all__ = ['LegacyConfiguration']


class LegacyConfiguration(BaseConfiguration):
    """Class to handle attributes related to installation locations"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(LegacyConfiguration, self).__init__(*args, **kwargs)
        self.log('LegacyConfiguration.__init__ started')
        self.options = {'osg_site_name':
                            configfile.Option(name='osg_site_name',
                                              mapping='GRID3_SITE_NAME'),
                        'osg_app':
                            configfile.Option(name='osg_app',
                                              mapping='GRID3_APP_DIR'),
                        'osg_data':
                            configfile.Option(name='osg_data',
                                              mapping='GRID3_DATA_DIR'),
                        'osg_data_tmp':
                            configfile.Option(name='osg_data_tmp',
                                              mapping='GRID3_TMP_DIR'),
                        'osg_wn_tmp':
                            configfile.Option(name='osg_wn_tmp',
                                              mapping='GRID3_TMP_WN_DIR'),
                        'osg_sponsor':
                            configfile.Option(name='osg_sponsor',
                                              mapping='GRID3_SPONSOR'),
                        'osg_site_info':
                            configfile.Option(name='osg_site_info',
                                              mapping='GRID3_SITE_INFO'),
                        'osg_util_contact':
                            configfile.Option(name='osg_util_contact',
                                              mapping='GRID3_UTIL_CONTACT'),
                        'osg_job_contact':
                            configfile.Option(name='osg_job_contact',
                                              mapping='GRID3_JOB_CONTACT'),
                        'osg_user_vo_map':
                            configfile.Option(name='osg_user_vo_map',
                                              mapping='GRID3_USR_VO_MAP'),
                        'osg_gridftp_log':
                            configfile.Option(name='osg_gridftp_log',
                                              mapping='GRID3_GRIDFTP_LOG'),
                        'osg_transfer_contact':
                            configfile.Option(name='osg_transfer_contact',
                                              mapping='GRID3_TRANSFER_CONTACT')}

        self.log('LegacyConfiguration.__init__ completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('LegacyConfiguration.check_attributes started')
        attributes_ok = True
        self.log('LegacyConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('LegacyConfiguration.configure started')
        for option in self.options.values():
            self.log("Checking for %s" % option.name)

            if option.name == 'osg_transfer_contact':
                # mapped from different osg attribute
                cap_name = 'OSG_UTIL_CONTACT'
            elif option.name == 'osg_data_tmp':
                # mapped from different osg attribute
                cap_name = 'OSG_DATA'
            else:
                cap_name = option.name.upper()

            if cap_name in attributes:
                self.log("Found %s for %s" % (attributes[cap_name],
                                              option.name))
                option.value = attributes[cap_name]
            else:
                self.log("%s not found" % option.name)
        self.log('LegacyConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Legacy"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return False
