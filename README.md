# Document Assembly Line - Runtime Code

A jurisdiction-agnostic runtime package that supports rapidly automating forms
with a controlled style. Saves time over using just the base docassemble
platform.

This is the run-time code that supports the interviews at https://courtformsonline.org

This package supersedes [MAVirtualCourt](https://github.com/SuffolkLITLab/docassemble-MAVirtualCourt).

# Migration

* Remove any references to MAVirtualCourt. Add an include block like this at the top
  of your interview YAML file

```
include:
  - docassemble.AssemblyLine:al_package.yml
  - docassemble.MassAccess:massaccess.yml
```

* Change references to `basic_questions_intro_screen` to `al_intro_screen`
* Change references to `courts[0]` to trial_court


# Example usage of ALDocument class

Here is a small snippet that you can copy and modify that shows how to use the most important features of the ALDocument class.

```
---
objects:
  - CRA_Motion_to_Dismiss_attachment: ALDocument.using(filename="CRA_Motion_to_Dismiss", title="Motion to Dismiss CRA", enabled=True, has_addendum=True, default_overflow_message="[See addendum]")  
---
objects:
  - al_user_bundle: ALDocumentBundle.using(elements=[CRA_Motion_to_Dismiss_attachment], title="Forms to download and deliver to court", filename="motion_to_dismiss_CRA.pdf")
  - al_court_bundle: ALDocumentBundle.using(elements=[CRA_Motion_to_Dismiss_attachment], title="Forms to download and deliver to court", filename="motion_to_dismiss_CRA.pdf")
---
generic object: ALDocument
attachment:
  variable name: x.addendum
  docx template file: docx_addendum.docx
---
code: |
  CRA_Motion_to_Dismiss_attachment.overflow_fields['reasons_for_request'].overflow_trigger = 640
  CRA_Motion_to_Dismiss_attachment.overflow_fields.gathered = True
---
attachment:
    variable name: CRA_Motion_to_Dismiss_attachment[i]
    name: CRA Motion to Dismiss
    filename: CRA_Motion_to_Dismiss
    skip undefined: True
    pdf template file: CRA_Motion_to_Dismiss.pdf
    fields: 
      - "court_county": ${ trial_court.address.county }
      - "docket_number": ${ docket_number }
      - "user_signature": ${ users[0].signature_if_final(i) }
      - "signature_date": ${ signature_date }
```
