import unittest
from docassemble.base.util import DAFile
from .al_document import ALDocument, ALDocumentBundle


class test_dont_assume_pdf(unittest.TestCase):
    def test_upload_pdf(self):
        doc1 = ALDocument(
            "doc1",
            title="PDF 1",
            filename="pdf_doc_1",
            enabled=True,
            has_addendum=False,
        )
        doc1["final"] = DAFile("test_aldocument_pdf_1.pdf")
        doc2 = ALDocument(
            "doc2",
            title="DOCX 2",
            filename="docx_doc_1",
            enabled=True,
            has_addendum=False,
        )
        doc2["final"] = DAFile("test_aldocument_docx_1.docx")
        al_doc_bundle = ALDocumentBundle(
            "al_doc_bundle",
            elements=[doc1, doc2],
            title="Multiple docs",
            filename="multi_bundle_1",
            enabled=True,
        )
        new_list = al_doc_bundle.as_editable_list()
        self.assertEqual(len(new_list), 2)
        pass


if __name__ == "__main__":
    unittest.main()
