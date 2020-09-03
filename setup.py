from distutils.core import setup
import glob, os

from osg_configure.version import __version__


def get_data_files():
    """
    Generates a list of data files for packaging and locations where
    they should be placed
    """
    # create a list of test files
    fileList = []
    for root, subFolders, files in os.walk('tests'):
        for name in files:
            fileList.append(os.path.join(root, name))
    temp = filter(lambda x: '.svn' not in x, fileList)
    temp = filter(lambda x: not os.path.isdir(x), temp)
    temp = map(lambda x: (x.replace('tests', '/usr/share/osg-configure/tests', 1), x),
               temp)
    file_mappings = {}
    for (dest, source) in temp:
        dest_dir = os.path.dirname(dest)
        if dest_dir in file_mappings:
            file_mappings[dest_dir].append(source)
        else:
            file_mappings[dest_dir] = [source]
    data_file_list = []
    for key in file_mappings:
        data_file_list.append((key, file_mappings[key]))

    # generate config file entries
    data_file_list.append(('/etc/osg/config.d', glob.glob('config/*.ini')))
    # add grid3-locations file
    data_file_list.append(('/etc/osg/', ['data_files/grid3-locations.txt']))
    return data_file_list


setup(name='osg-configure',
      version=__version__,
      description='Package for osg-configure and associated scripts',
      author='Suchandra Thapa',
      maintainer='Matyas Selmeci',
      maintainer_email='matyas@cs.wisc.edu',
      url='http://www.opensciencegrid.org',
      packages=['osg_configure', 'osg_configure.modules', 'osg_configure.configure_modules'],
      scripts=['scripts/osg-configure'],
      data_files=get_data_files(),
      classifiers=[
          "Development Status :: 6 - Mature",
          "Environment :: Console",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.6",
      ],
      platforms=["Linux"],
      license="Apache Software License 2.0"
)
