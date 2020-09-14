import unittest, os, sys
from io import StringIO
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
from osg_configure.modules.utilities import get_test_config


class TestResourceCatalog(unittest.TestCase):
    def assertDoesNotRaise(self, exception, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except exception:
            self.fail('%s called with %r and %r raised %s' % (function.__name__, args, kwargs, exception.__name__))

    def setUp(self):
        if not resourcecatalog: return
        self.rc = ResourceCatalog()

    def testEmpty(self):
        if not resourcecatalog: return
        self.assertEqual(self.rc.compose_text().strip(), "OSG_ResourceCatalog = {}")

    def testSingle(self):
        if not resourcecatalog: return
        self.rc.add_rcentry(RCEntry(name='sc1', cpus=1, memory=2000))
        self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc1"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testMulti(self):
        if not resourcecatalog: return
        (self.rc
         .add_rcentry(RCEntry(name='sc1', cpus=1, memory=2000))
         .add_rcentry(RCEntry(name='sc2', cpus=2, memory=4000))
         .add_rcentry(RCEntry(name='sc3', cpus=4, memory=8000, allowed_vos='osg   ,,,atlas')))
        self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
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

    def testNoName(self):
        if not resourcecatalog: return
        rce = RCEntry(name='', cpus=1, memory=1)
        self.assertRaises(ValueError, self.rc.add_rcentry, rce)

    def testOutOfRange(self):
        if not resourcecatalog: return
        rce = RCEntry(name='sc', cpus=-1, memory=1)
        self.assertRaises(ValueError, self.rc.add_rcentry, rce)
        rce.cpus = 1
        rce.memory = 0
        self.assertRaises(ValueError, self.rc.add_rcentry, rce)

    def testZeroMaxWallTime(self):
        if not resourcecatalog: return
        rce = RCEntry(name='sc', cpus=1, memory=1, max_wall_time=0)
        self.assertDoesNotRaise(ValueError, self.rc.add_rcentry, rce)

    def testExtraRequirements(self):
        if not resourcecatalog: return
        rce = RCEntry(name='sc', cpus=1, memory=2000, extra_requirements='TARGET.WantGPUs =?= 1')
        self.rc.add_rcentry(rce)
        self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && TARGET.WantGPUs =?= 1; \
    Transform = [ set_MaxMemory = RequestMemory; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testExtraTransforms(self):
        if not resourcecatalog: return
        rce = RCEntry(name='sc', cpus=1, memory=2000, extra_transforms='set_WantRHEL6 = 1')
        self.rc.add_rcentry(rce)
        self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory; \
    Transform = [ set_MaxMemory = RequestMemory; set_WantRHEL6 = 1; set_xcount = RequestCPUs; ]; \
  ] \
}""")

    def testFull(self):
        if not resourcecatalog: return
        config = configparser.SafeConfigParser()
        config_io = StringIO(r"""
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
""")
        config.readfp(config_io)
        self.assertEqual(subcluster.resource_catalog_from_config(config).compose_text(),
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
        if not resourcecatalog: return
        # Test using the "Resource Entry" section name instead of "Subcluster"
        # and also using some of the attributes ATLAS requested
        config = configparser.SafeConfigParser()
        config_io = StringIO(r"""
[Resource Entry Valid]
name = red.unl.edu
maxmemory = 4000
cpucount = 4
queue = red
vo_tag = ANALYSIS
allowed_vos = osg, atlas
""")
        config.readfp(config_io)
        self.assertEqual(subcluster.resource_catalog_from_config(config).compose_text(),
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
        if not resourcecatalog: return
        config = configparser.SafeConfigParser()
        config_file = get_test_config("subcluster/resourceentry_and_sc.ini")
        config.read(config_file)
        self.assertDoesNotRaise(exceptions.SettingError, subcluster.resource_catalog_from_config, config)
        rc = subcluster.resource_catalog_from_config(config).compose_text()
        self.assertTrue('Subclusters = { "SC1", "Sub Cluster 2" }; \\' in rc,
                        '\'subclusters\' attrib improperly transformed')

    def testResourceEntryBad(self):
        if not resourcecatalog: return
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
        if not resourcecatalog: return
        config = configparser.SafeConfigParser()
        config_io = StringIO(r"""
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
""")
        config.readfp(config_io)
        self.assertEqual(subcluster.resource_catalog_from_config(config).compose_text(),
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

    def testFullWithExtras(self):
        # Disable this test because the feature is disabled for now
        return
        if not resourcecatalog: return
        config = configparser.SafeConfigParser()
        config_io = cStringIO.StringIO(r"""
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
extra_requirements = WantGPUs =?= 1
extra_transforms = set_WantRHEL6 = 1
max_wall_time = 1440
allowed_vos = osg, atlas
""")
        config.readfp(config_io)
        self.assertEqual(subcluster.resource_catalog_from_config(config).compose_text(),
                         r"""OSG_ResourceCatalog = { \
  [ \
    AllowedVOs = { "osg", "atlas" }; \
    CPUs = 4; \
    MaxWallTime = 1440; \
    Memory = 4000; \
    Name = "glow.chtc.wisc.edu"; \
    Requirements = TARGET.RequestCPUs <= CPUs && TARGET.RequestMemory <= Memory && member(TARGET.VO, AllowedVOs) && WantGPUs =?= 1; \
    Transform = [ set_MaxMemory = RequestMemory; set_WantRHEL6 = 1; set_remote_queue = "blue"; set_xcount = RequestCPUs; ]; \
  ] \
}""")


if __name__ == '__main__':
    unittest.main()
