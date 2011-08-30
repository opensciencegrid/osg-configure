from distutils.core import setup
import glob

config_files = glob.glob('config/*.ini')

setup(name='osg-configure',
      version='0.5.3',
      description='Package for configure-osg and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['configure_osg', 'configure_osg.modules', 'configure_osg.configure_modules'],      
      scripts=['scripts/configure-osg'],
      data_files=[('/etc/osg/config.d', config_files),]
      )
