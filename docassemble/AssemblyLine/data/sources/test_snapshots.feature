@snapshots
Feature: Test saving snapshots

Scenario: User can save an answer snapshot
  Given I log in with "DA_ADMIN_EMAIL" and "DA_ADMIN_PASSWORD"
  And I start the interview at "test_saving_snapshots"
  And I should see the phrase "Save an answer set"
  And I set the var "al_sessions_snapshot_label" to "My test snapshot"
  And I tap to continue
  And I should see the phrase "Your answer set was successfully saved"
