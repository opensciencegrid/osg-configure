from distutils.core import setup
import glob

config_files = ['config/ce.ini',
                'config/gums.ini',
                'config/pigeon.ini',
                'config/rsv.ini',
                'config/storage.ini']

setup(name='osg-configure',
      version='0.0.2',
      description='Package for configure-osg and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['configure_osg', 'configure_osg.modules', 'configure_osg.configure_modules'],      
      scripts=['scripts/configure-osg'],
      data_files=[('/etc/osg', config_files),]
      )
