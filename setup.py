import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.AssemblyLine',
      version='2.0.12',
      description=('Runtime package that helps rapidly automate court forms, letters, and the like'),
      long_description='# Document Assembly Line - Runtime Code\r\n\r\nA jurisdiction-agnostic runtime package that supports rapidly automating forms\r\nwith a controlled style. Saves time over using just the base docassemble\r\nplatform.\r\n\r\nThis is the run-time code that supports the interviews at https://courtformsonline.org\r\n\r\nThis package supersedes [MAVirtualCourt](https://github.com/SuffolkLITLab/docassemble-MAVirtualCourt).\r\n\r\n# Migration\r\n\r\n* Remove any references to MAVirtualCourt. Add an include block like this at the top\r\n  of your interview YAML file\r\n\r\n```\r\ninclude:\r\n  - docassemble.AssemblyLine:al_package.yml\r\n  - docassemble.MassAccess:massaccess.yml\r\n```\r\n\r\n* Change references to `basic_questions_intro_screen` to `al_intro_screen`\r\n* Change references to `courts[0]` to trial_court',
      long_description_content_type='text/markdown',
      author='Suffolk Legal Innovation and Technology Lab',
      author_email='qsteenhuis@suffolk.edu',
      license='The MIT License (MIT)',
      url='https://courtformsonline.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=[],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/AssemblyLine/', package='docassemble.AssemblyLine'),
     )

