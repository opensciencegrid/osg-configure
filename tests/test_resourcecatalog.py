import unittest, os, sys
import configparser

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)
sys.path.insert(0, '.')

try:
    from osg_configure.modules import resourcecatalog
    from osg_configure.modules.resourcecatalog import ResourceCatalog, RCEntry
    from osg_configure.modules import subcluster
except ImportError:
    resourcecatalog = None
    subcluster = None
    print("resourcecatalog and/or subcluster not found -- skipping resourcecatalog tests")
from osg_configure.modules import exceptions
from osg_configure.modules.utilities import get_test_config, split_comma_separated_list


class TestResourceCatalog(unittest.TestCase):
    def assertDoesNotRaise(self, exception, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except exception:
            self.fail('%s called with %r and %r raised %s' % (function.__name__, args, kwargs, exception.__name__))

    def assertLongStringEqual(self, first, second, msg=None):
        self.assertEqual(first.splitlines(), second.splitlines(), msg=msg)

    def setUp(self):
        if not resourcecatalog:
            self.skipTest("No resourcecatalog")
        self.rc = ResourceCatalog()

    def testEmpty(self):
        self.assertEqual(self.rc.compose_text().strip(), "OSG_ResourceCatalog = {}")

    def testSingle(self):
        self.rc.add_rcentry(RCEntry(name='sc1', cpus=1, memory=2000))
        self.assertLongStringEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc1"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testMulti(self):
        (self.rc
         .add_rcentry(RCEntry(name='sc1', cpus=1, memory=2000))
         .add_rcentry(RCEntry(name='sc2', cpus=2, memory=4000))
         .add_rcentry(RCEntry(name='sc3', cpus=4, memory=8000, allowed_vos=split_comma_separated_list('osg   ,,,atlas'))))
        self.assertLongStringEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc1"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ], \
  [ \
    CPUs = 2; \
    Memory = 4000; \
    Name = "sc2"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ], \
  [ \
    AllowedVOs = { "osg", "atlas" }; \
    CPUs = 4; \
    Memory = 8000; \
    Name = "sc3"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && member(TARGET.VO, AllowedVOs); \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testExtraRequirements(self):
        rce = RCEntry(name='sc', cpus=1, memory=2000, extra_requirements='TARGET.WantGPUs =?= 1')
        self.rc.add_rcentry(rce)
        self.assertLongStringEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && TARGET.WantGPUs =?= 1; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testExtraTransforms(self):
        rce = RCEntry(name='sc', cpus=1, memory=2000, extra_transforms='set_WantRHEL6 = 1')
        self.rc.add_rcentry(rce)
        self.assertLongStringEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_WantRHEL6 = 1; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testFull(self):
        config = configparser.SafeConfigParser()
        config_string = r"""
[Subcluster Valid]
name = red.unl.edu
node_count = 60
ram_mb = 4000
cpu_model = Opteron 275
cpu_vendor = AMD
cpu_speed_mhz = 2200
cpu_platform = x86_64
cpus_per_node = 2
cores_per_node = 4
inbound_network = FALSE
outbound_network = TRUE
HEPSPEC = 10
allowed_vos = osg, atlas
"""
        config.read_string(config_string)
        self.assertLongStringEqual(subcluster.resource_catalog_from_config(config).compose_text(),
                                   r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "osg", "atlas" }; \
    CPUs = 4; \
    MaxWallTime = 1440; \
    Memory = 4000; \
    Name = "red.unl.edu"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && member(TARGET.VO, AllowedVOs); \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testResourceEntry(self):
        # Test using the "Resource Entry" section name instead of "Subcluster"
        # and also using some of the attributes ATLAS requested
        config = configparser.SafeConfigParser()
        config_string = r"""
[Resource Entry Valid]
name = red.unl.edu
maxmemory = 4000
cpucount = 4
queue = red
vo_tag = ANALYSIS
allowed_vos = osg, atlas
"""
        config.read_string(config_string)
        self.assertLongStringEqual(subcluster.resource_catalog_from_config(config).compose_text(),
                                   r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "osg", "atlas" }; \
    CPUs = 4; \
    MaxWallTime = 1440; \
    Memory = 4000; \
    Name = "red.unl.edu"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && member(TARGET.VO, AllowedVOs) && TARGET.VOTag == "ANALYSIS"; \
    Transform = [ set_MaxMemory = RequestMemory; set_VOTag = "ANALYSIS"; set_remote_queue = "red"; set_xcount = RequestCPUs; ]; \
    VOTag = "ANALYSIS"; \
  ] \
}""")

    def testResourceEntryWithSubclusters(self):
        config = configparser.SafeConfigParser()
        config_file = get_test_config("subcluster/resourceentry_and_sc.ini")
        config.read(config_file)
        self.assertDoesNotRaise(exceptions.SettingError, subcluster.resource_catalog_from_config, config)
        rc = subcluster.resource_catalog_from_config(config).compose_text()
        self.assertTrue('Subclusters = { "SC1", "Sub Cluster 2" }; \\' in rc,
                        '\'subclusters\' attrib improperly transformed')

    def testResourceEntryBad(self):
        for config_filename in ["subcluster/resourceentry_missing_cpucount.ini",
                                "subcluster/resourceentry_missing_memory.ini",
                                "subcluster/resourceentry_missing_queue.ini",
                                "subcluster/resourceentry_missing_sc.ini"]:
            config = configparser.SafeConfigParser()
            config_file = get_test_config(config_filename)
            config.read(config_file)
            try:
                self.assertRaises(exceptions.SettingError, subcluster.resource_catalog_from_config, config)
            except AssertionError:
                sys.stderr.write("Failed to raise error on " + config_filename)
                raise

    def testFullWithExtraTransforms(self):
        config = configparser.SafeConfigParser()
        config_string = r"""
[Subcluster Test]
name = glow.chtc.wisc.edu
node_count = 60
ram_mb = 4000
cpu_model = Opteron 275
cpu_vendor = AMD
cpu_speed_mhz = 2200
cpu_platform = x86_64
cpus_per_node = 2
cores_per_node = 4
inbound_network = FALSE
outbound_network = TRUE
HEPSPEC = 10
queue = blue
extra_transforms = set_WantRHEL6 = 1
max_wall_time = 1440
allowed_vos = osg, atlas
"""
        config.read_string(config_string)
        self.assertLongStringEqual(subcluster.resource_catalog_from_config(config).compose_text(),
                                   r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "osg", "atlas" }; \
    CPUs = 4; \
    MaxWallTime = 1440; \
    Memory = 4000; \
    Name = "glow.chtc.wisc.edu"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && member(TARGET.VO, AllowedVOs); \
    Transform = [ set_MaxMemory = RequestMemory; set_WantRHEL6 = 1; set_remote_queue = "blue"; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testResourceEntryWithPilot(self):
        rce = RCEntry(name='glow.chtc.wisc.edu',
                      cpus=1,
                      memory=2500,
                      max_wall_time=1440,
                      allowed_vos=["glow"],
                      gpus=1,
                      max_pilots=1000,
                      whole_node=False,
                      queue="",
                      require_singularity=True,
                      os="rhel8",
                      send_tests=True,
                      is_pilot=True)
        expected_string = r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "glow" }; \
    CPUs = 1; \
    GPUs = 1; \
    IsPilotEntry = True; \
    MaxPilots = 1000; \
    MaxWallTime = 1440; \
    Memory = 2500; \
    Name = "glow.chtc.wisc.edu"; \
    OS = "rhel8"; \
    RequireSingularity = True; \
    SendTests = True; \
    WholeNode = False; \
  ] \
}"""
        rc = ResourceCatalog()
        rc.add_rcentry(rce)
        actual_string = rc.compose_text()
        self.assertLongStringEqual(actual_string, expected_string)

    def testPilot(self):
        config = configparser.SafeConfigParser()
        config_string = r"""
[Pilot glow.chtc.wisc.edu]
name = glow.chtc.wisc.edu
#ram_mb = 2500
#cpucount = 1
#max_wall_time = 1440
allowed_vos = glow
gpucount = 1
max_pilots = 1000
#whole_node = false
#queue =
#require_singularity = true
os = rhel8
#send_tests = true
"""
        config.read_string(config_string)
        expected_string = r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "glow" }; \
    CPUs = 1; \
    GPUs = 1; \
    IsPilotEntry = True; \
    MaxPilots = 1000; \
    MaxWallTime = 1440; \
    Memory = 2500; \
    Name = "glow.chtc.wisc.edu"; \
    OS = "rhel8"; \
    RequireSingularity = True; \
    SendTests = True; \
    WholeNode = False; \
  ] \
}"""
        actual_string = subcluster.resource_catalog_from_config(config).compose_text()
        self.assertLongStringEqual(actual_string, expected_string)

    def testPilotExample(self):
        config_parser = configparser.SafeConfigParser()
        config_file = get_test_config("subcluster/pilots_example.ini")
        config_parser.read(config_file)
        expected_string = r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "icecube" }; \
    CPUs = 1; \
    GPUs = 2; \
    IsPilotEntry = True; \
    MaxPilots = 1000; \
    MaxWallTime = 2880; \
    Memory = 8192; \
    Name = "GPU"; \
    RequireSingularity = True; \
    SendTests = True; \
    WholeNode = False; \
  ], \
  [ \
    AllowedVOs = { "atlas" }; \
    IsPilotEntry = True; \
    MaxPilots = 1000; \
    MaxWallTime = 1440; \
    Name = "WholeNode"; \
    RequireSingularity = True; \
    SendTests = True; \
    WholeNode = True; \
  ], \
  [ \
    AllowedVOs = { "osg", "cms" }; \
    CPUs = 8; \
    IsPilotEntry = True; \
    MaxPilots = 1000; \
    MaxWallTime = 1440; \
    Memory = 32768; \
    Name = "default"; \
    OS = "rhel6"; \
    RequireSingularity = False; \
    SendTests = True; \
    WholeNode = False; \
  ] \
}
"""
        actual_string = subcluster.resource_catalog_from_config(config_parser).compose_text()
        self.assertLongStringEqual(actual_string, expected_string)


if __name__ == '__main__':
    unittest.main()
