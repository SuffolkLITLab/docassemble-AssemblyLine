# do not pre-load
"""Fixtures for test_accessibility_translation.yml; never sends email."""

from docassemble.AssemblyLine.al_document import ALDocumentBundle


class TranslationTestBundle(ALDocumentBundle):
    """Use real bundle controls with predictable warning and email outcomes."""

    def broken_exhibit_titles(self):
        return self.attr("test_broken_titles") or []

    def send_email(self, **kwargs):
        return self.attr("test_email_success")
