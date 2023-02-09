# Changelog

## v2.21.0

### Added

* Add a parameter to always write out the full name of the state, instead of abbreviation: [#646](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/646)

### Fixed

* Stop `al_sessions_to_exclude` from growing; excluded interviews that remained on the interview list: [#650](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/650)
* Updated SQL Alchemy code to work with v1.4 - v2.0 (docassemble versions 1.2.68 - 1.4.33 (and on)): [#659](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/659)
* Cleanup appearance of error action page: [#659](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/659)


## v2.20.1

Duplicate of v2.20.0 due to workflow issues, nothing has changed.

## v2.20.0

### New
* Custom error page to replace Docassemble's stock error page by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/622
* Add visible trigger variable to the developer-only heads up display by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/617
* Optional library of fallback questions to use for undefined variables @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/619
* Add marriage questions by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/641
* Add simple service of process questions by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/640
* Add a link to "original form" on the default about page, if it exists and looks like a valid link by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/647
* Better API for searching courts by county by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/644

### Changed
* Change OCR to use ocrmypdf in the background (seems to have significant performance improvements for OCR) by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/613
* Add focus shadow for back button by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/624
* `will_send_to_real_court` false if debug == True by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/627
* Make answer sets unencrypted to match interview state by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/628
* Don't force gathering users[0].address to gather users[1].address or users[0].mailing_address by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/639

### Fixed
* Fix unittest action by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/634
* Move unittest action externally by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/635
* Add "Home" label to alt text for logo by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/632
* Readd newlines between each step on intro screen by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/648

[Full changelog](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/releases/tag/v2.20.1)

## Version v2.19.0

### Changed

* Addendum code no longer cuts off text mid-word [#607](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/607)
* Remove words 'the' and 'project' from opening screen [#612](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/612)

## Version v2.18.0

## Added

* Misc. session list cleanups, including ability to exclude interviews from the session list: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/593
* Improve usability of signature question, adding the option to print then sign: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/591
* Added a max size feature to the ALExhibitDocument: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/604

## Fixed

* Show answer sets even if they are on "step 1" (as answer sets don't usually have more than 1 step): https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/599
* Use `user_started_case` over users == plaintiff:  https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/596
* Decrease the size of images in tables: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/603
* If address is empty, `on_one_line()` will be empty: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/605

## Internal

* Added black example hook + black opts to pyproject.toml: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/601
* Teams bump hook, in a github action: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/602
* Better internal typing: https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/606


Contributors: @BryceStevenWilley and @nonprofittechy

## Version v2.17.0

New:
* Address improvements by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/554
* Add question for your birthdate by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/557
* Save progress and form title at regular intervals, small interview list cleanups by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/559
* Switch back to the clickable link being form title, not subtitle by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/561

Changed:
* Rename "docket number" to case number by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/566
* Initials shouldn't trigger last name for a business by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/570

Fixed:
* DA 1.4.0 compatibility by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/549
* Fix no address by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/555
* Don't add left-padding to the first footer child by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/556
* Fix session list on small screens by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/569
* Don't turn on address autocomplete if not enabled by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/576
* Check if the `suffix_to_append` attribute exists by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/583

Cleanup:
* Remove manage_sessions.yml - it's not used by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/553

## Version v2.15.0

Fixed
* DA 1.4.x compatibility by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/549
* Fix spacing so all elements are visible in mobile footer by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/556

New
* Address improvements by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/554
    * Developer feature to help work with "normalized" address
    * Make "county" optional field
    * Feature to let unhoused people provide narrative address

Changed
* Add question for "your" birthdate by @BryceStevenWilley in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/557
* [Revised interview list](https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/framework/magic_variables#use-the-assemblyline-interview-list-replacement) adds a progress icon and automatically updated title by @nonprofittechy in https://github.com/SuffolkLITLab/docassemble-AssemblyLine/pull/559

## Version v2.14.0

Added:
* the `reserved_words.yml` interview, which returns a JSON list of all reserved python and
  docassemble keywords and variable / function names
* the `interview_list.yml`, a replacement interview for the "My interviews" page, which has
  some useability fixes implemented, is faster than the builtin "My interviews" page, and lets
  users navigation between Answer sets and ordinary sessions.
  You can use this interview to replace the builtin "My interviews" by adding the following line
  in the configuration:

  ```yaml
  session list interview: docassemble.AssemblyLine:data/questions/interview_list.yml
  ```

Fixed:
* Added `ALDocumentBundle.is_enabled`, which was assumed to exist in the previous release.
  It will only enable the document bundle if `enabled = True` and there is at least one
  enabled subdocument in the bundle.
  This will fix errors like the below:

  ```txt
  Interview has an error. There was a reference to a variable 'al_user_bundle.is_enabled' that
  could not be looked up in the question file (for language 'en') or in any of the files
  incorporated by reference into the question file.
  ```

## Version v2.13.0

Added
* Export to JSON button on "share" screen
* Offer the user's address as default for second, third, etc user
* New baseline questions for probate matters
* new `show_if` parameter for all `*_fields()` methods on ALIndividuals
* Added include reference to new ALToolbox InterviewStats module

Changed
* Better contrast for accessibility
* "terms" now have a dotted underline instead of solid
* Improvements to exhibit code (OCR, etc)
* `send_button_html()` is no longer displayed if the bundle has no enabled documents
* default value of `github_user` comes from configuration instead of defaulting to `suffolklitlab`
* when the key is equal to `preview`, `_preview` is appended to filenames (to generate unique filenames in tests)
* improvements to typing (mypy)

Fixed
* the default feedback form title had literal mako tags

## Version v2.11.3

* Move the "answer set" feature behind a global configuration option (opt-in)
* Accessibility improvements
* Add PDF/A support to ALDocument class

## Version v2.11.2

Incorrect reference to save session location in the new "Answer set" feature

## Version v2.11.1

Correct the priority of the new default gender for a business; it was taking priority over the gender question

## Version v2.11.0

New:

* Added "answer set" feature that is available on production forms
* Accessibility improvements
* Minor API additions to improve developer experience with ALDocument class
* `language_fields()` method
* ALDocumentUpload class

Fixed:

* businesses have a default gender of "other" (helps language methods work correctly)
* Added some missing objects for nouns created by the Weaver
* Fixed label for "fax number" field
* return proper value when `key` function called in an addendum file

Changed:
* Types are now checked for safe usage with mypy on commit

## Version v2.10.2

Fixed:
* More protection when using snapshot feature to avoid snapshotting files/file-like objects that can't be restored
* fix some bad assumptions in the `as_editable_list()` method of ALDocumentBundle. Will work with all ALDocument subclasses now, including uploaded files

## Version v2.10.1

New features:

* added `full_names` method to ALPeopleList class (always uses full middle name, not middle initial in list)

Bug fixes:

* ensure definition of `AL_ORGANIZATION_TITLE` for feedback page
* Fix issue where you are not prompted to add additional pages to the second or more exhibit with default questions

## Version v2.10.0

Add questions for `previous_addresses` and `other_addresses`
Fix preexisting bug with address methods--missing imports

## Version v2.9.0

As of AssemblyLine v2.9.0, you can now include AssemblyLine code in your interview by
referencing `docassemble.AssemblyLine:assembly_line.yml` instead of `docassemble.AssemblyLine:al_package.yml`.
The old reference is deprecated but there are no current plans to remove it.

* Bugfixes
* Added additional comments and documentation of classes and variables
* Slightly improved phrasing of some questions
* .zip file includes DOCX files (configurable)
* Better typing
* Starting using the black autoreformatter to have more consistent Python coding style
* Remove some debugging strings

## Version v2.8.0

Bug fixes:
* email template does not trigger any extra screens, making it safer to use outside of AssemblyLine interviews
* Improvements to address question + mailing address defaults to home address
* Moved the help template for user role into the subquestion part to improve readability
* new version of ALKiln
* Remove some instances of CourtFormsOnline.org and add new variables to allow this to be customized for different jurisdictions (AL_ORGANIZATION_TITLE and AL_ORGANIZATION_HOMEPAGE)
* Small cleanups in ql_baseline.yml

## Version v2.7.1

Use metadata title, not the action title in navigation bar

## Version v2.7.0

* Add form title to the navigation bar per Theory & Principle UX audit
* Limit upload size
* Misc. accessibility fixes
* Fix bug with signature screen
* Make the "courtformsonline" a variable

## Version v2.6.2

* Add "Start over" menu option
* Merge and deprecate docassemble.LanguagePack - features are now part of AL Core

## Version v2.6.1

Increased caching for some translated strings

## Version v2.6.0

* Added new short_list method on ALPeopleList, to display abbreviated list of people
* Remove some uses of question help button
* send_button_html now triggers sending separate PDFs for each bundled item. Editable checkbox still sends Word DOCX files as appropriate
* Improved bumpversion script link to changelog

## Version v2.5.0

* Use separate PDFs in send_button_html
* Remove some question help buttons, per usability feedback
* Fix bumpversion script

## Version v2.4.1

Add back in mistakenly removed AL_DEFAULT_OVERFLOW_MESSAGE

## Version v2.4.0

Allow ALDocumentBundles to set the value of auto_gather and gathered in object declaration

## Version v2.3.8

Correct usage of include_table_of_contents in ALExhibitDocument class

## Version v2.3.7

Fixed bug in name_fields

## Version v2.3.6

Make suffix an optional field to display in name_fields() method

## Version v2.3.5

Hotfix error in country attribute of address_fields() method

## Version v2.3.4

Fix #269 - make the ALExhibitDocument class idempotent

## Version v2.3.3

Sort session names in Fast Forward (dev only feature)

## Version v2.3.1

Safer string handling in send_button_html

## Version v2.3.0

Add the ability for a developer to snapshot and fastforward sessions. This adds a HUD along with the question id

## Version v2.2.1

Important data leakage fix (#263)

## Version v2.2.0

* Added ALExhibitDocument class
* Added automated tests
* Improvements to handling of refreshed document state
* Improvements to docstrings

## v2.1.4
* Added ALStaticDocument class
* Respect filename provided on download screens
* Make submit buttons minimum of 8em wide
* Added appeals_court placeholder question

## v2.1.2
Added internationalization support to address fields methods, together with new constants `AL_DEFAULT_COUNTRY`, `AL_DEFAULT_STATE`, and `AL_DEFAULT_LANGUAGE` (use ISO 2 letter codes for all 3 parameters).

## v2.0.18

The first tagged release of Assembly Line

## v2.0.0

The first version of Assembly Line. Started at version 2, since this is a continuation of [MAVirtualCourt](https://github.com/SuffolkLITLab/MAVirtualCourt).
