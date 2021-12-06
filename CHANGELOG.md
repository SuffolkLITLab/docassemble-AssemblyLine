# Version v2.7.1

Use metadata title, not the action title in navigation bar

# Version v2.7.0

* Add form title to the navigation bar per Theory & Principle UX audit
* Limit upload size
* Misc. accessibility fixes
* Fix bug with signature screen
* Make the "courtformsonline" a variable

# Version v2.6.2

* Add "Start over" menu option
* Merge and deprecate docassemble.LanguagePack - features are now part of AL Core

# Version v2.6.1

Increased caching for some translated strings

# Version v2.6.0

* Added new short_list method on ALPeopleList, to display abbreviated list of people
* Remove some uses of question help button
* send_button_html now triggers sending separate PDFs for each bundled item. Editable checkbox still sends Word DOCX files as appropriate
* Improved bumpversion script link to changelog

# Version v2.5.0

* Use separate PDFs in send_button_html
* Remove some question help buttons, per usability feedback
* Fix bumpversion script

# Version v2.4.1

Add back in mistakenly removed AL_DEFAULT_OVERFLOW_MESSAGE

# Version v2.4.0

Allow ALDocumentBundles to set the value of auto_gather and gathered in object declaration

# Version v2.3.8

Correct usage of include_table_of_contents in ALExhibitDocument class

# Version v2.3.7

Fixed bug in name_fields

# Version v2.3.6

Make suffix an optional field to display in name_fields() method

# Version v2.3.5

Hotfix error in country attribute of address_fields() method

# Version v2.3.4

Fix #269 - make the ALExhibitDocument class idempotent

# Version v2.3.3

Sort session names in Fast Forward (dev only feature)

# Version v2.3.1

Safer string handling in send_button_html

# Version v2.3.0

Add the ability for a developer to snapshot and fastforward sessions. This adds a HUD along with the question id

# Version v2.2.1

Important data leakage fix (#263)

# Version v2.2.0

* Added ALExhibitDocument class
* Added automated tests
* Improvements to handling of refreshed document state
* Improvements to docstrings

# v2.1.4
* Added ALStaticDocument class
* Respect filename provided on download screens
* Make submit buttons minimum of 8em wide
* Added appeals_court placeholder question

# v2.1.2
Added internationalization support to address fields methods, together with new constants `AL_DEFAULT_COUNTRY`, `AL_DEFAULT_STATE`, and `AL_DEFAULT_LANGUAGE` (use ISO 2 letter codes for all 3 parameters).

# v2.0.18

The first tagged release of Assembly Line

# v2.0.0

The first version of Assembly Line. Started at version 2, since this is a continuation of [MAVirtualCourt](https://github.com/SuffolkLITLab/MAVirtualCourt).
