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
      version='2.4.1',
      description=('Runtime package that helps rapidly automate court forms, letters, and the like'),
      long_description='# Document Assembly Line - Runtime Code\r\n\r\nA jurisdiction-agnostic runtime package that supports rapidly automating forms\r\nwith a controlled style. Saves time over using just the base docassemble\r\nplatform.\r\n\r\nThis is the run-time code that supports the interviews at https://courtformsonline.org\r\n\r\nThis package supersedes [MAVirtualCourt](https://github.com/SuffolkLITLab/docassemble-MAVirtualCourt).\r\n\r\n# Documentation\r\n\r\nhttps://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/\r\n\r\n# Installation\r\n\r\nThis package depends on the following configuration changes on your Docassemble server:\r\n\r\n* Ensure that [font-awesome](https://docassemble.org/docs/config.html#default%20icons) is enabled (this may be on by default:\r\n```yaml\r\ndefault icons: font awesome\r\n```\r\n* Add a [Google API key](https://docassemble.org/docs/config.html#google) that has access to:\r\n    * Google Places API\r\n    * Google Geocoding API\r\n* Add a [VoiceRSS API key](https://docassemble.org/docs/config.html#voicerss)\r\n* Add a [Twilio API key](https://docassemble.org/docs/config.html#twilio) for SMS support\r\n* Add an email account: [Mailgun](https://docassemble.org/docs/config.html#mailgun%20api) or [SendGrid](https://docassemble.org/docs/config.html#sendgrid%20api) recommended for email support\r\n* To show package update time and to enable the feedback form, add a GitHub Private Access token to your config.yml file, like this:\r\n```yaml\r\n# Needs access to create new issues on repositories\r\ngithub issues:\r\n  username: "suffolklitlab-issues"\r\n  token: "12345"\r\n# Does not need any special access to public repositories  \r\ngithub readonly:\r\n  username: "suffolklitlab-issues"\r\n  password: "45678"\r\n  type: "basic"\r\n```\r\n* If you are also using the [Assembly Line Weaver](https://github.com/SuffolkLITLab/docassemble-assemblylinewizard), you may want to set up a [Docassemble API key](https://docassemble.org/docs/api.html#manage_api) in your config.yml file to allow you to install packages automatically, like this:\r\n```yaml\r\ninstall packages api key: 12345\r\n```\r\n\r\n# Migration\r\n\r\nSee [discussion here](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/issues/69)\r\n\r\n\r\n# ALDocument class\r\n\r\n## Purpose\r\n\r\nThe ALDocument class is a small utility library that makes it simpler to use the following features in an interview:\r\n\r\n* Conditional assembly of multiple, optional documents that are triggered in different ways in your interview\r\n* An addendum for PDF files that makes it simple to deal with overflow text\r\n* A customizable download screen that lists the documents in a neat table\r\n* A customizable "send" button that allows the user to email the final forms to a location of their choice\r\n\r\nHere is a small snippet that you can copy and modify that shows how to use the most important features of the ALDocument class.\r\n\r\n```\r\n---\r\nobjects:\r\n  - CRA_Motion_to_Dismiss_attachment: ALDocument.using(filename="CRA_Motion_to_Dismiss", title="Motion to Dismiss CRA", enabled=True, has_addendum=True, default_overflow_message="[See addendum]")  \r\n---\r\nobjects:\r\n  - al_user_bundle: ALDocumentBundle.using(elements=[CRA_Motion_to_Dismiss_attachment], title="Forms to download and deliver to court", filename="motion_to_dismiss_CRA.pdf")\r\n  - al_court_bundle: ALDocumentBundle.using(elements=[CRA_Motion_to_Dismiss_attachment], title="Forms to download and deliver to court", filename="motion_to_dismiss_CRA.pdf")\r\n---\r\ngeneric object: ALDocument\r\nattachment:\r\n  variable name: x.addendum\r\n  docx template file: docx_addendum.docx\r\n---\r\ncode: |\r\n  CRA_Motion_to_Dismiss_attachment.overflow_fields[\'reasons_for_request\'].overflow_trigger = 640\r\n  CRA_Motion_to_Dismiss_attachment.overflow_fields[\'reasons_for_request\'].label = "Reasons for request"\r\n  CRA_Motion_to_Dismiss_attachment.overflow_fields.gathered = True\r\n  \r\n---\r\nattachment:\r\n    variable name: CRA_Motion_to_Dismiss_attachment[i]\r\n    name: CRA Motion to Dismiss\r\n    filename: CRA_Motion_to_Dismiss\r\n    skip undefined: True\r\n    pdf template file: CRA_Motion_to_Dismiss.pdf\r\n    fields: \r\n      - "court_county": ${ trial_court.address.county }\r\n      - "docket_number": ${ docket_number }\r\n      - "user_signature": ${ users[0].signature_if_final(i) }\r\n      - "signature_date": ${ signature_date }\r\n```\r\n\r\nIt is very common to have a *contingent* document in ALDocument. If your document is contingent, remove the `enabled=True` from the object declaration, and use\r\nsome other method to "turn on" the attachment.\r\n\r\nE.g.,\r\n\r\n```\r\ncode: |\r\n  CRA_Motion_to_Dismiss_attachment.enabled = condition1 and condition2\r\n```\r\n\r\n# Changelog\r\n\r\nSee [CHANGELOG.MD](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/blob/main/CHANGELOG.md)\r\n',
      long_description_content_type='text/markdown',
      author='Suffolk Legal Innovation and Technology Lab',
      author_email='qsteenhuis@suffolk.edu',
      license='The MIT License (MIT)',
      url='https://courtformsonline.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=['docassemble.ALToolbox>=0.0.11', 'docassemble.GithubFeedbackForm>=0.1.2'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/AssemblyLine/', package='docassemble.AssemblyLine'),
     )

