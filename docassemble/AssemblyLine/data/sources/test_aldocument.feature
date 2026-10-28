@aldocument
Feature: ALDocument classes

@aldocs @d1
Scenario: No ALDocument page errors
  And the max seconds for each step is 200
  Given I start the interview at "test_aldocument"
  And I get to "end aldocument tests" with this data:
    | var | value | trigger |
    | intro_screen | True |  |
    | as_foo_custom | True |  |
    | as_foo_defaults | True |  |
    | download_list_html_custom_1 | True |  |
    | download_list_html_custom_2 | True |  |
    | download_list_html_custom_3 | True |  |    
    | download_list_html_defaults | True |  |
    | email_custom | True |  |
    | email_defaults | True |  |
    | x.has_no_file | True | notice_to_quit.has_no_file |

@alexhibits @e1
Scenario: User can upload exhibits
  And the max seconds for each step is 200
  Given I start the interview at "test_alexhibit"
  And I get to "exhibit i" with this data:
    | var | value | trigger |
    | x.has_exhibits | True | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].title | Defaults 1 | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 2 | exhibit_doc_defaults_1.exhibits[0].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_jpg_1.jpg | exhibit_doc_defaults_1.exhibits[0].pages[1].initialized |
    | x.target_number | 2 | exhibit_doc_defaults_1.exhibits.there_is_another |
  # ALKiln's upload step returns on change, before the file-input widget
  # finishes preparing the PDF on docassemble 1.9.8. Let it finish before Next.
  And I set the variable "x[i].title" to "Defaults 2"
  And I set the variable "x[i].pages" to "test_alexhibit_pdf_1.pdf"
  And I wait 1 second
  And I tap to continue
  And I get to "exhibit i" with this data:
    | var | value | trigger |
    | x[i].pages.target_number | 2 | exhibit_doc_defaults_1.exhibits[1].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_png_1.png | exhibit_doc_defaults_1.exhibits[1].pages[1].initialized |
    | x.there_is_another | False | exhibit_doc_defaults_1.exhibits.there_is_another |
    | x.has_exhibits | True | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[0].title | Defaults 1 | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 2 | exhibit_doc_custom_1.exhibits[0].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_jpg_1.jpg | exhibit_doc_custom_1.exhibits[0].pages[1].initialized |
    | x.target_number | 2 | exhibit_doc_custom_1.exhibits.there_is_another |
  # Wait for the custom exhibit's PDF widget as well.
  And I set the variable "x[i].title" to "Defaults 2"
  And I set the variable "x[i].pages" to "test_alexhibit_pdf_1.pdf"
  And I wait 1 second
  And I tap to continue
  And I get to "end alexhibit tests" with this data:
    | var | value | trigger |
    | x[i].pages.target_number | 2 | exhibit_doc_custom_1.exhibits[1].pages.there_is_another |
    | x[i].pages[j] | test_alexhibit_png_1.png | exhibit_doc_custom_1.exhibits[1].pages[1].initialized |
    | x.there_is_another | False | exhibit_doc_custom_1.exhibits.there_is_another |

@alexhibits @e2
Scenario: User adds only a docx exhibit
  And the max seconds for each step is 200
  Given I start the interview at "test_alexhibit"
  And I get to "end alexhibit tests" with this data:
    | var | value | trigger |
    | x.has_exhibits | True | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].title | DOCX only | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 1 | exhibit_doc_defaults_1.exhibits[0].pages.there_is_another |
    | x.target_number | 1 | exhibit_doc_defaults_1.exhibits.there_is_another |
    | x.has_exhibits | True | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[0].title | DOCX only | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[0].pages | test_alexhibit_docx_1.docx | exhibit_doc_custom_1.exhibits.has_exhibits |
    | x[i].pages.target_number | 1 | exhibit_doc_custom_1.exhibits[0].pages.there_is_another |
    | x.target_number | 1 | exhibit_doc_custom_1.exhibits.there_is_another |

@alexhibits @e3
Scenario: User uploads 0 files
  And the max seconds for each step is 200
  Given I start the interview at "test_alexhibit"
  And I get to "end alexhibit tests" with this data:
    | var | value | trigger |
    | x.has_exhibits | False | exhibit_doc_defaults_1.exhibits.has_exhibits |
    | x.has_exhibits | False | exhibit_doc_custom_1.exhibits.has_exhibits |
    
