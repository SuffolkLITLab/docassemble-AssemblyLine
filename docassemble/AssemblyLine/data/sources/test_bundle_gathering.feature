@aldocument @bundlegathering
Feature: ALDocument bundle gathering

@bundle-gathering
Scenario: Bundle helpers respect gathering state and current membership
  And the max seconds for each step is 200
  Given I start the interview at "test_bundle_gathering"
  And I set the variable "include_second_document" to "True"
  And I tap to continue
  Then I should see the phrase "Automatic gathering needs one more document"
  And I set the variable "auto_gather_complete" to "True"
  And I tap to continue
  Then I should see the phrase "Defined False count: 0"
  And I should see the phrase "Missing marker count: 1"
  And I should see the phrase "Automatic gather count: 2"
  And I should see the phrase "Automatic gather marker: True"
  And I should see the phrase "Membership count: 2"
