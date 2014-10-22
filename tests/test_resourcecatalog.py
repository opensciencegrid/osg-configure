import unittest, os, sys
import cStringIO

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)
sys.path.insert(0, '.')

from osg_configure.modules.resourcecatalog import ResourceCatalog


class TestResourceCatalog(unittest.TestCase):
  def setUp(self):
    self.rc = ResourceCatalog()

  def testEmpty(self):
    self.assertEqual(self.rc.compose_text().strip(), "OSG_ResourceCatalog = {}")

  def testSingle(self):
    self.rc.add_entry('sc1', 1, 2000)
    self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc1"; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ] \
}""")

  def testMulti(self):
    (self.rc
      .add_entry('sc1', 1, 2000)
      .add_entry('sc2', 2, 4000)
      .add_entry('sc3', 4, 8000, 'osg   ,,,atlas'))
    self.assertEqual(self.rc.compose_text().strip(), r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 1; \
    Memory = 2000; \
    Name = "sc1"; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ], \
  [ \
    CPUs = 2; \
    Memory = 4000; \
    Name = "sc2"; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ], \
  [ \
    CPUs = 4; \
    Memory = 8000; \
    Name = "sc3"; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory && (VO == "osg" || VO == "atlas"); \
  ] \
}""")

  def testNoName(self):
    self.assertRaises(ValueError, self.rc.add_entry, '', 1, 1)

  def testOutOfRange(self):
    self.assertRaises(ValueError, self.rc.add_entry, 'sc', -1, 1)
    self.assertRaises(ValueError, self.rc.add_entry, 'sc', 1, 0)

  def testFull(self):
    import ConfigParser
    from osg_configure.modules import subcluster
    config = ConfigParser.SafeConfigParser()
    config_io = cStringIO.StringIO(r"""
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
""")
    config.readfp(config_io)
    self.assertEqual(subcluster.resource_catalog_from_config(config).compose_text(),
                     r"""OSG_ResourceCatalog = { \
  [ \
    CPUs = 4; \
    Memory = 4000; \
    Name = "red.unl.edu"; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ] \
}""")

if __name__ == '__main__':
  unittest.main()
