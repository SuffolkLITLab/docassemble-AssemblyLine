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
