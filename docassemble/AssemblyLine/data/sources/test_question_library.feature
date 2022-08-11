@alql
Feature: AL question library

@alql @ql1
Scenario: Can enter all parts of address
  Given the max seconds for each step is 50
  And I start the interview at "test_question_library"
  Then I set the variable "which_to_test" to "address"
  And I tap to continue
  Then I should see the phrase "Street address"
  And I should see the phrase "Apartment"
  And I set the variable "users[0].address.address" to "123 Fake Street"
  And I set the variable "users[0].address.unit" to "Apt 5"
  And I set the variable "users[0].address.city" to "Boston"
  And I set the variable "users[0].address.state" to "MA"
  And I set the variable "users[0].address.zip" to "12345"
  And I tap to continue
  Then I should see the phrase "All done!"

@alql @ql2
Scenario: Can say no address available
  Given the max seconds for each step is 50
  And I start the interview at "test_question_library"
  Then I set the variable "which_to_test" to "address_no_address"
  And I tap to continue
  And I set the variable "users[0].address.has_no_address" to "True"
  And I set the variable "users[0].address.has_no_address_explanation" to "I sometimes sleep at 5th and Yorkshire"
  And I set the variable "users[0].address.city" to "Boston"
  And I set the variable "users[0].address.state" to "MA"
  And I tap to continue
  Then I should see the phrase "All done!"

@alq1 @ql3
Scenario: Can enter all parts of contact info
  Given the max seconds for each step is 50
  And I start the interview at "test_question_library"
  Then I set the variable "which_to_test" to "contact"
  And I tap to continue
  And I tap to continue
  Then I should see the phrase "You need to provide at least one contact method"
  And I set the variable "users[0].mobile_number" to "123-456-7890"
  And I tap to continue
  Then I should see the phrase "All done!"
