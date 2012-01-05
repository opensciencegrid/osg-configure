from distutils.core import setup
import glob,re

config_files = glob.glob('config/*.ini')


def get_version():
  """
  Gets version from osg-configure script file
  """
  buffer = open('scripts/osg-configure').read()
  match = re.search("VERSION\s+=\s+'(.*)'", buffer)
  return match.group(1)
  
setup(name='osg-configure',
      version=get_version(),
      description='Package for configure-osg and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['osg_configure', 'osg_configure.modules', 'osg_configure.configure_modules'],      
      scripts=['scripts/osg-configure'],
      data_files=[('/etc/osg/config.d', config_files),]
      )
