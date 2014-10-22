import unittest, os, sys

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
    Name = "sc1"; \
    CPUs = 1; \
    Memory = 2000; \
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
    Name = "sc1"; \
    CPUs = 1; \
    Memory = 2000; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ], \
  [ \
    Name = "sc2"; \
    CPUs = 2; \
    Memory = 4000; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory; \
  ], \
  [ \
    Name = "sc3"; \
    CPUs = 4; \
    Memory = 8000; \
    Requirements = RequestCPUs <= CPUs && RequestMemory <= Memory && (VO == "osg" || VO == "atlas"); \
  ] \
}""")

  def testNoName(self):
    self.assertRaises(ValueError, self.rc.add_entry, '', 1, 1)

  def testOutOfRange(self):
    self.assertRaises(ValueError, self.rc.add_entry, 'sc', -1, 1)
    self.assertRaises(ValueError, self.rc.add_entry, 'sc', 1, 0)


if __name__ == '__main__':
  unittest.main()
