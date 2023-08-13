import unittest
from docassemble.base.util import DAFile
from .al_document import ALDocument, ALDocumentBundle, ALAddendumField


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


class test_aladdendum(unittest.TestCase):
    def test_safe_value(self):
        text_testcase1 = """Charged by my father with a very delicate mission, I repaired, towards the end of May, 1788, to the château of Ionis, situated a dozen leagues distant, in the lands lying between Angers and Saumur. I was twenty-two, and already practising the profession of lawyer, for which I experienced but slight inclination, although neither the study of business nor of argument had presented serious difficulties to me. Taking my youth into consideration, I was not esteemed without talent, and the standing of my father, a lawyer renowned in the locality, assured me a brilliant patronage in the future, in return for any paltry efforts I might make to be worthy of replacing him. But I would have preferred literature, a more dreamy life, a more independent and more individual use of my faculties, a responsibility less submissive to the passions and interests of others. As my family was well off, and I an only son, greatly spoiled and petted, I might have chosen my own career, but I would have thus afflicted my father, who took pride in his ability to direct me 4in the road which he had cleared in advance, and I loved him too tenderly to permit my instinct to outweigh his wishes.

It was a delightful evening in which I was finishing my ride on horseback through the woods that surrounded the ancient and magnificent castle of Ionis. I was well mounted, dressed en cavalier, with a species of elegance, and accompanied by a servant of whom I had not the slightest need, but whom my mother had conceived the innocent idea of giving me for the occasion, desiring that her son should present a proper appearance at the house of one of the most brilliant personages of our patronage.

The night was illuminated by the soft fire of its largest stars. A slight mist veiled the scintillations of those myriads of satellites that gleam like brilliant eyes on clear, cold evenings. This was a true summer sky, pure enough to be luminous and transparent, still sufficiently softened not to overwhelm one by its immeasurable wealth. It was, if I may so speak, one of those soft firmaments that permit one to think of earth, to admire the vaporous lines of narrow horizons, to breathe without disdain its atmosphere of flowers and herbage—in fine, to consider oneself as something in this immensity, and to forget that one is but an atom in the infinite.

In proportion as I approached the seigneurial park the wild perfumes of the forest were mingled with those of the lilacs and acacias, whose blooming heads leaned over the wall. Soon through the shrubbery I saw the windows of the manor gleaming behind their curtains of purple moire, divided by the dark crossbars of the frame work. It was a magnificent castle 5of the renaissance, a chef-d’œuvre of taste mingled with caprice, one of those dwellings where one is impressed by something indescribably ingenious and bold, which from the imagination of the architect seems to pass into one’s own, and take possession of it, raising it above the usages and preoccupations of a positive world.

I confess that my heart beat fast in giving my name to the lackey commissioned to announce me. I had never seen Madame d’Ionis; she passed for one of the prettiest women in the country, was twenty-two, and had a husband who was neither handsome nor amiable, and who neglected her in order to travel. Her writing was charming, and she found means to show not only a great deal of sense, but still more cleverness in her business letters. Altogether she was a very fine character. This was all that I knew of her, and it was sufficient for me to dread appearing awkward or provincial. I grew pale on entering the salon. My first impression then was one of relief and pleasure, when I found myself in the presence of two stout and very ugly old women, one of whom, Madame the Dowager d’Ionis informed me that her daughter-in-law was at the house of her friends in the neighborhood, and probably would not return before the next day.

“You are welcome, all the same,” added this matron. “We have a very friendly and grateful feeling for your father, and it appears that we stand in great need of his counsel, which you are without doubt charged to communicate to us.”

“I came from him,” I replied, “to talk over the affair with Madame d’Ionis.”
        """
        testcase1 = text_testcase1
        myfield = ALAddendumField(field_name="testcase1")
        myfield.overflow_trigger = 160
        self.assertLessEqual(
            len(myfield.safe_value(overflow_message=" [See addendum]")),
            160,
        )
        # print(myfield.safe_value(overflow_message=""))
        safe_value = myfield.safe_value(overflow_message="")
        self.assertTrue(safe_value.endswith("in the"))
        overflow_value = myfield.overflow_value(overflow_message="")
        self.assertTrue(overflow_value.startswith("lands"))
        self.assertEqual(len(myfield.safe_value(overflow_message="")), 158)

        with_weird_spaces = """Testing here


with some very short words, but a whole lot of them, so it'll be over the overflow, over the flow yah know?"""

        field_with_weird_spaces = ALAddendumField(
            field_name="with_weird_spaces", overflow_trigger=23
        )
        safe_value = field_with_weird_spaces.safe_value(overflow_message="")
        self.assertTrue(safe_value.endswith("some"), msg=f"{ safe_value }")
        overflow_value = field_with_weird_spaces.overflow_value(overflow_message="")
        self.assertTrue(overflow_value.startswith("very"), msg=f"{ overflow_value }")


class TestOriginalOrOverflowMessage(unittest.TestCase):
    def test_original_value_shorter_than_trigger(self):
        testcase2 = "Short text"
        test_instance = ALAddendumField(field_name="testcase2")
        test_instance.overflow_trigger = 10

        result = test_instance.original_or_overflow_message(
            overflow_message="Overflow occurred.",
        )
        self.assertEqual(
            result, "Short text"
        )  # Original value shorter than overflow_trigger

    def test_original_value_exceeds_trigger(self):
        testcase3 = "A very long text that exceeds the overflow trigger"
        test_instance = ALAddendumField(field_name="testcase3")
        test_instance.overflow_trigger = 10

        result = test_instance.original_or_overflow_message(
            overflow_message="Overflow occurred.",
            preserve_newlines=True,
        )
        self.assertEqual(
            result, "Overflow occurred."
        )  # Original value exceeds the overflow_trigger

    def test_original_value_exceeds_trigger_with_newlines(self):
        testcase4 = (
            "A medium\n length text\nthat exceeds\nthe overflow trigger with newlines"
        )
        test_instance = ALAddendumField(field_name="testcase4")
        test_instance.overflow_trigger = 80

        result = test_instance.original_or_overflow_message(
            overflow_message="Overflow occurred.",
            preserve_newlines=True,
            preserve_words=True,
        )
        self.assertEqual(
            result, "Overflow occurred."
        )  # Original value exceeds the overflow_trigger, but preserve_newlines is True


if __name__ == "__main__":
    unittest.main()
