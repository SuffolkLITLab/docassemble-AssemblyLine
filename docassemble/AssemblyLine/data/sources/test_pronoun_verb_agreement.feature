@pronouns
Feature: Pronoun and verb agreement

@pronouns @pronouns1
Scenario: Fixed pronoun and verb agreement checks all pass
  Given the max seconds for each step is 50
  And I start the interview at "test_pronoun_verb_agreement"
  Then I should see the phrase "All 35 checks passed."
  And I should see the phrase "Alex Smith lives in Boston. They live near the park."
  And I should see the phrase "Alex Smith was late. They were sorry."

@pronouns @pronouns2
Scenario: A they/them person agrees with the name or the pronoun
  Given the max seconds for each step is 50
  And I start the interview at "test_pronoun_verb_agreement"
  And I tap to continue
  And I set the variable "subject.name.first" to "Taylor"
  And I set the variable "subject.name.last" to "Brooks"
  And I set the variable "subject_source" to "pronouns"
  And I set the variable "subject.pronouns['they/them/theirs']" to "true"
  And I tap to continue
  Then I should see the phrase "Taylor Brooks lives in Boston."
  And I should see the phrase "Taylor Brooks was at the hearing."
  And I should see the phrase "They live in Boston."
  And I should see the phrase "They were at the hearing."
  And I should see the phrase "Taylor Brooks is the tenant."
  And I should see the phrase "They are the tenant."

@pronouns @pronouns3
Scenario: A person with nothing to go on agrees with the name
  Given the max seconds for each step is 50
  And I start the interview at "test_pronoun_verb_agreement"
  And I tap to continue
  And I set the variable "subject.name.first" to "Riley"
  And I set the variable "subject.name.last" to "Park"
  And I set the variable "subject_source" to "none"
  And I tap to continue
  Then I should see the phrase "Riley Park lives in Boston."
  And I should see the phrase "Riley Park was at the hearing."
  And I should see the phrase "their fish"
  And I should see the phrase "Reflexive: themself"
