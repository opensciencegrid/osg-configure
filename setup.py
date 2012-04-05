from distutils.core import setup
import glob,re, os

config_files = glob.glob('config/*.ini')


def get_version():
  """
  Gets version from osg-configure script file
  """
  buffer = open('scripts/osg-configure').read()
  match = re.search("VERSION\s+=\s+'(.*)'", buffer)
  return match.group(1)
  
def get_test_files():
  """
  Gets the unit tests and configs for them
  """
  fileList = []
  for root, subFolders, files in os.walk('tests'):
    for name in files:
      fileList.append(os.path.join(root,name))  
  return filter(lambda x: '.svn' not in x, fileList)

setup(name='osg-configure',
      version=get_version(),
      description='Package for osg-configure and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['osg_configure', 'osg_configure.modules', 'osg_configure.configure_modules'],      
      scripts=['scripts/osg-configure'],
      data_files=[('/etc/osg/config.d', config_files),
                  ('/etc/osg/', ['data_files/grid3-locations.txt']),
                  ('/usr/share/osg-configure', get_test_files())]
      )
