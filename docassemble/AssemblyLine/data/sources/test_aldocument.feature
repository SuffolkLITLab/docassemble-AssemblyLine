@aldocument
Feature: ALDocument classes

@aldocs @d1
Scenario: No ALDocument page errors
  And the max seconds for each step is 150
  Given I start the interview at "test_aldocument"
  And I get to "end aldocument tests" with this data:
    | var | value | trigger |
    | as_foo_custom | True |  |
    | as_foo_defaults | True |  |
    | download_list_html_custom_1 | True |  |
    | download_list_html_custom_2 | True |  |
    | download_list_html_defaults | True |  |
    | email_custom | True |  |
    | email_defaults | True |  |

@alexhibits @e1
Scenario: User can upload exhibits
  And the max seconds for each step is 150
  Given I start the interview at "test_alexhibit"
  And I get to "end alexhibit tests" with this data:
    | var | value | trigger |
    | x.has_exhibits | True | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].title | Defaults 1 | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 2 | exhibit_doc_defaults_1.exhibits[0].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_jpg_1.jpg | exhibit_doc_defaults_1.exhibits[0].pages[1] |
    | x.target_number | 2 | exhibit_doc_defaults_1.exhibits.there_is_another |
    | x[i].title | Defaults 2 | exhibit_doc_defaults_1.exhibits[1].title |
    | x[i].pages | test_alexhibit_pdf_1.pdf | exhibit_doc_defaults_1.exhibits[1].title |
    | x[i].pages.target_number | 2 | exhibit_doc_defaults_1.exhibits[1].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_png_1.png | exhibit_doc_defaults_1.exhibits[1].pages[1] |

@alexhibits @e2
Scenario: User adds only a docx exhibit
  And the max seconds for each step is 150
  Given I start the interview at "test_alexhibit"
  And I get to "end alexhibit tests" with this data:
    | var | value | trigger |
    | x.has_exhibits | True | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].title | DOCX only | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 1 | exhibit_doc_defaults_1.exhibits[0].pages.there_is_another |
    | x.target_number | 1 | exhibit_doc_defaults_1.exhibits.there_is_another |
    