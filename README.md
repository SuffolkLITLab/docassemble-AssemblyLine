# Suffolk LIT Lab Document Assembly Line

[![PyPI version](https://badge.fury.io/py/docassemble-AssemblyLine.svg)](https://badge.fury.io/py/docassemble-AssemblyLine)

<img src="https://user-images.githubusercontent.com/7645641/142245862-c2eb02ab-3090-4e97-9653-bb700bf4c54d.png" alt="drawing" width="300" alt="work together" style="align: center;"/>

The Assembly Line Project is a collection of volunteers, students, and institutions who joined together
during the COVID-19 pandemic to help increase access to the court system. Our vision is mobile-friendly,
easy to use **guided** online forms that help empower litigants to access the court remotely.

Our signature project is [CourtFormsOnline.org](https://courtformsonline.org).

We designed a step-by-step, assembly line style process for automating court forms on top of Docassemble
and built several tools along the way that **you** can use in your home jurisdiction.

This package contains **runtime code** and **pre-written questions** to support authoring robust, 
consistent, and attractive Docassemble interviews that help complete court forms.

Read more on our [documentation page](https://suffolklitlab.org/docassemble-AssemblyLine-documentation/).


# Related repositories

* https://github.com/SuffolkLitLab/docassemble-ALWeaver
* https://github.com/SuffolkLitLab/docassemble-ALMassachusetts
* https://github.com/SuffolkLitLab/docassemble-MassAccess
* https://github.com/SuffolkLitLab/docassemble-ALThemeTemplate
* https://github.com/SuffolkLitLab/EfileProxyServer

# Documentation

https://suffolklitlab.org/docassemble-AssemblyLine-documentation/

# Installation

## Menu-driven installation

The recommended installation method is with the [guided installation script](https://assemblyline.suffolklitlab.org/docs/get_started/installation).

## Manual installation

Normally you do not need to manually install the Assembly Line. Use the [installation script](https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/installation)
if you can. The instructions below are for your optional reference.

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


# Answer Set Import Safety Configuration

Answer set JSON imports are intentionally restricted to reduce risk from malformed and malicious payloads.

Default behavior:
- Plain JSON values are imported by default, and object reconstruction is allowed only for allowlisted DAObject classes.
- Top-level variable names must match `^[A-Za-z][A-Za-z0-9_]*$`.
- Internal/protected variable names are blocked.
- If `answer set import allowed variables` is not set, imports allow safe variable names by default, still block protected/internal names, and intersect with the target interview's known variables when AssemblyLine can detect them.
- Object payloads can be imported when classes are allowlisted; by default, known `docassemble.base` and `docassemble.AssemblyLine` DAObject descendants are allowed.

Default import limits (`assembly line: answer set import limits`):
- `max bytes`: `1048576` (1 MB)
- `max depth`: `40`
- `max keys`: `20000`
- `max list items`: `5000`
- `max string length`: `200000`
- `max number abs`: `1000000000000000` (`10**15`)

Final allowlist/config policy:
- Default allowlist: unset (`answer set import allowed variables` omitted), which falls back to safe-name/protected-name checks plus target-interview variable detection when available.
- Recommended production policy: set an explicit allowlist to only shared/reusable variables in your jurisdiction.
- `answer set import allow objects` defaults to `true`; set it to `false` if you want strict plain-JSON-only imports.
- `answer set import allowed object classes` can extend the default DAObject class allowlist with explicit additional class paths.
- Additional classes in `answer set import allowed object classes` apply to object envelopes at any depth (top-level variables and nested descendants).
- `answer set import remap known classes` defaults to `true`; this safely maps known class basenames from other packages (such as playground exports) onto official allowlisted classes.
- `answer set import class remap` can define explicit basename-to-class mappings for additional controlled remaps.

Example hardened configuration:

```yaml
assembly line:
  enable answer sets: true
  enable answer set imports: true
  answer set import require signed: false
  answer set import allow objects: true
  answer set import remap known classes: true
  answer set import limits:
    max bytes: 1048576
    max depth: 40
    max keys: 20000
    max list items: 5000
    max string length: 200000
    max number abs: 1000000000000000
  answer set import allowed variables:
    - users_name
    - users_address
    - users_phone_number
    - users_email
    - household_size
  answer set import allowed object classes:
    - docassemble.AssemblyLine.al_general.ALIndividual
    - docassemble.AssemblyLine.al_general.ALPeopleList
    - docassemble.AssemblyLine.al_general.ALAddress
  answer set import class remap:
    ALIndividual: docassemble.AssemblyLine.al_general.ALIndividual
    ALPeopleList: docassemble.AssemblyLine.al_general.ALPeopleList
```

Notes:
- Keeping `answer set import require signed: false` matches current compatibility-first behavior; unsigned imports still pass strict structural validation.
- If your environment can manage signing keys, set `answer set import require signed: true` to require signed payloads.
- Class allowlisting uses full dotted class names (exact match), not wildcard patterns.
- Playground-authored classes usually need explicit allowlisting, e.g. `docassemble.playground1.al_general.ALIndividual`.
- If a playground package name changes across environments (for example `playground1` to `playground2`), update `answer set import allowed object classes` to match the runtime class path.
- With `answer set import remap known classes: true`, exports that use known class basenames (for example `docassemble.playground1.al_general.ALIndividual`) can be remapped to official allowlisted classes without instantiating the playground class.


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

