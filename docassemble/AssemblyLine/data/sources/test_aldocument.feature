@aldocument
Feature: ALDocument class

Scenario: No page errors
  Given I start the interview at "test_aldocument"
  And the max seconds for each step is 40
  And I get to "end aldocument tests" with this data:
    | var | value | trigger |
    | as_foo_custom| True |  |
    | as_foo_defaults| True |  |
    | download_list_html_custom_1| True |  |
    | download_list_html_custom_2| True |  |
    | download_list_html_defaults| True |  |
    | email_custom| True |  |
    | email_defaults| True |  |
