# Document Assembly Line - Runtime Code

A jurisdiction-agnostic runtime package that supports rapidly automating forms
with a controlled style. Saves time over using just the base docassemble
platform.

This is the run-time code that supports the interviews at https://courtformsonline.org

This package supersedes [MAVirtualCourt](https://github.com/SuffolkLITLab/docassemble-MAVirtualCourt).

# Documentation

https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/

# Installation

This package depends on the following configuration changes on your Docassemble server:

* Ensure that [font-awesome](https://docassemble.org/docs/config.html#default%20icons) is enabled (this may be on by default:
```yaml
default icons: font awesome
```
* Add a [Google API key](https://docassemble.org/docs/config.html#google) that has access to:
    * Google Places API
    * Google Geocoding API
* Add a [VoiceRSS API key](https://docassemble.org/docs/config.html#voicerss)
* Add a [Twilio API key](https://docassemble.org/docs/config.html#twilio) for SMS support
* Add an email account: [Mailgun](https://docassemble.org/docs/config.html#mailgun%20api) or [SendGrid](https://docassemble.org/docs/config.html#sendgrid%20api) recommended for email support
* To show package update time and to enable the feedback form, add a GitHub Private Access token to your config.yml file, like this:
```yaml
# Needs access to create new issues on repositories
github issues:
  username: "suffolklitlab-issues"
  token: "12345"
# Does not need any special access to public repositories  
github readonly:
  username: "suffolklitlab-issues"
  password: "45678"
  type: "basic"
```
* If you are also using the [Assembly Line Weaver](https://github.com/SuffolkLITLab/docassemble-assemblylinewizard), you may want to set up a [Docassemble API key](https://docassemble.org/docs/api.html#manage_api) in your config.yml file to allow you to install packages automatically, like this:
```yaml
install packages api key: 12345
```

# Migration

See [discussion here](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/issues/69)


# ALDocument class

## Purpose

The ALDocument class is a small utility library that makes it simpler to use the following features in an interview:

* Conditional assembly of multiple, optional documents that are triggered in different ways in your interview
* An addendum for PDF files that makes it simple to deal with overflow text
* A customizable download screen that lists the documents in a neat table
* A customizable "send" button that allows the user to email the final forms to a location of their choice

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
  CRA_Motion_to_Dismiss_attachment.overflow_fields['reasons_for_request'].label = "Reasons for request"
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

It is very common to have a *contingent* document in ALDocument. If your document is contingent, remove the `enabled=True` from the object declaration, and use
some other method to "turn on" the attachment.

E.g.,

```
code: |
  CRA_Motion_to_Dismiss_attachment.enabled = condition1 and condition2
```

# Changelog

See [CHANGELOG.MD](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/blob/main/CHANGELOG.md)
