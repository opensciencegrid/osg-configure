from distutils.core import setup
import glob

config_files = glob.glob('config/*.ini')

setup(name='osg-configure',
      version='0.5.5',
      description='Package for configure-osg and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['osg_configure', 'osg_configure.modules', 'osg_configure.configure_modules'],      
      scripts=['scripts/osg-configure'],
      data_files=[('/etc/osg/config.d', config_files),]
      )
