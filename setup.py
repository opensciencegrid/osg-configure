from distutils.core import setup
import glob,re, os



def get_version():
  """
  Gets version from osg-configure script file
  """
  buffer = open('scripts/osg-configure').read()
  match = re.search("VERSION\s+=\s+'(.*)'", buffer)
  return match.group(1)
  
def get_data_files():
  """
  Generates a list of data files for packaging and locations where
  they should be placed
  """
  # create a list of test files
  fileList = []
  for root, subFolders, files in os.walk('tests'):
    for name in files:
      fileList.append(os.path.join(root,name))  
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
      version=get_version(),
      description='Package for osg-configure and associated scripts',
      author='Suchandra Thapa',
      author_email='sthapa@ci.uchicago.edu',
      url='http://www.opensciencegrid.org',
      packages=['osg_configure', 'osg_configure.modules', 'osg_configure.configure_modules'],      
      scripts=['scripts/osg-configure'],
      data_files=get_data_files()
      )
