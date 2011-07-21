from distutils.core import setup

setup(name='osg-configure',
      version='0.0.2',
      description='Package for configure-osg and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['configure-osg'],
      scripts=['scripts/configure-osg'],
      data_files=['config', 'etc/osg']
      )