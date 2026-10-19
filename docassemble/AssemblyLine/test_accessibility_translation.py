# do not pre-load
"""Translation and escaping regressions that do not require a web server."""

from pathlib import Path
import json
import re
from html.parser import HTMLParser
from types import SimpleNamespace

from jinja2 import Environment
import pytest
from docassemble.AssemblyLine import al_document


class Tags(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def test_page_translates_and_serializes_confirmation():
    source = (
        Path(__file__).parent / "data/templates/al_interview_list_page.html"
    ).read_text()
    source = re.sub(r"^\{%-?\s*extends.*?%\}\n?", "", source, flags=re.M)
    translated = "Traduit \" <script> & l'article"
    seen = []

    def word(text):
        seen.append(text)
        return translated + text

    env = Environment(autoescape=True)
    html = env.from_string(source).render(
        word=word,
        package_name="docassemble.AssemblyLine",
        loading_message=word("Loading…"),
        url_for=lambda *a, **kw: "#",
        cfg={"enable_answer_sets": True},
        active_tab="in_progress",
        sessions=[dict(session_key="abc", filename="form.yml")],
        page=1,
        page_size=1,
    )
    tags = Tags(html).tags
    # PR #1117 adds this external script. Continue rejecting injected scripts.
    scripts = [attrs for tag, attrs in tags if tag == "script"]
    assert all(
        attrs
        == {
            "src": "/packagestatic/docassemble.AssemblyLine/interview_list.js",
            "defer": None,
        }
        for attrs in scripts
    )
    for tag, attrs in tags:
        if "data-loading-message" in attrs:
            assert attrs["data-loading-message"] == translated + "Loading…"
    assert all(
        attrs["aria-label"].startswith(translated)
        for tag, attrs in tags
        if "aria-label" in attrs
    )
    copy = next(
        attrs
        for tag, attrs in tags
        if attrs.get("aria-label") == translated + "Copy to answer set"
    )
    assert (
        copy["title"]
        == translated
        + "Saves these answers so you can reuse them to start a different form later."
    )
    for tag, attrs in tags:
        if "onsubmit" in attrs:
            js = attrs["onsubmit"]
            assert json.loads(js[len("return confirm(") : -1]).startswith(translated)
    assert {"Saved form views", "Delete", "Rename", "Previous", "Next", "Save"} <= set(
        seen
    )


@pytest.mark.parametrize("titles", [["<One>"], ["<One>", 'Two " &']])
def test_warning_translates_complete_phrase_and_escapes(monkeypatch, titles):
    seen = []

    def translate(text):
        seen.append(text)
        return "Attention < & {documents}"

    monkeypatch.setattr(al_document, "word", translate)
    monkeypatch.setattr(al_document, "comma_and_list", lambda items: " et ".join(items))
    bundle = SimpleNamespace(broken_exhibit_titles=lambda: titles)
    html = al_document.ALDocumentBundle.broken_documents_warning_html(bundle)
    assert len(seen) == 1 and "{documents}" in seen[0]
    assert "Attention &lt; &amp;" in html
    assert "&lt;One&gt;" in html
    assert [tag for tag, attrs in Tags(html).tags] == ["div"]
    if len(titles) > 1:
        assert " et " in html


def test_signature_alt_text_uses_current_language(monkeypatch):
    import pickle
    import yaml
    from docassemble.base import functions
    from docassemble.base.util import DAFile
    from docassemble.AssemblyLine.al_general import ALIndividual

    blocks = list(
        yaml.safe_load_all(
            (Path(__file__).parent / "data/questions/ql_baseline.yml").read_text()
        )
    )
    question = next(b for b in blocks if b and b.get("id") == "persons signature")
    catalog = yaml.safe_load(
        (Path(__file__).parent / "data/sources/es-words.yml").read_text()
    )["es"]
    monkeypatch.setitem(functions.word_collection, "es", catalog)
    person = ALIndividual("person")
    person.name.first = 'Ana " &'
    person.name.last = "García"
    # The browser renders the question, saves the session, then submits it.
    person = pickle.loads(pickle.dumps(person))
    person.signature = DAFile("person.signature")
    exec(question["validation code"], {"x": person})
    person = pickle.loads(pickle.dumps(person))
    for language, prefix in [
        ("en", "Signature of"),
        ("es", "Firma de"),
        ("en", "Signature of"),
    ]:
        monkeypatch.setattr(functions.this_thread, "language", language)
        from docassemble.base import filter as da_filter
        from importlib import import_module

        # Newer Docassemble versions split filter into submodules. Patch the
        # function's defining module, where its image_url global is resolved.
        image_url_string = getattr(da_filter, "image_url_string", None)
        if image_url_string is None:
            image_url_string = import_module(
                "docassemble.base.filter.html"
            ).image_url_string
        image_filter = import_module(image_url_string.__module__)
        monkeypatch.setattr(
            image_filter,
            "image_url",
            lambda reference, alt, width, **kwargs: f"<img {alt}>",
        )
        markup = f"[FILE 1, 300px, {person.signature.get_alt_text()}]"
        match = re.match(r"\[FILE ([^,\]]+), *([0-9A-Za-z.%]+), *([^\]]*)\]", markup)
        rendered = image_url_string(match)
        assert Tags(rendered).tags == [("img", {"alt": prefix + ' Ana " & García'})]


def test_language_selector_escapes_translated_accessible_name(monkeypatch):
    from docassemble.AssemblyLine import language

    label = 'Langue " < &'
    monkeypatch.setattr(language, "word", lambda text: label)
    monkeypatch.setattr(language, "get_tuples", lambda *a, **kw: [("en", "English")])
    monkeypatch.setattr(language, "url_action", lambda *a, **kw: "#")
    html = language.get_language_list_dropdown(["en"])
    toggle = next(
        attrs for tag, attrs in Tags(html).tags if attrs.get("id") == "languageSelector"
    )
    assert toggle["aria-label"] == label


def test_catalogs_cover_runtime_phrases_and_preserve_placeholders(monkeypatch):
    import ast
    from string import Formatter
    from docassemble.base.functions import safeyaml
    from jinja2 import nodes

    root = Path(__file__).parent
    keys = {
        "Loading…",
        "Sending...",
        "Sent",
        "Signature of {name}",
        "and",
        "{title} documents",
        "Email address for document",
    }
    for filename in [
        "sessions.py",
        "language.py",
        "al_document.py",
        "interview_list_endpoint.py",
    ]:
        for node in ast.walk(ast.parse((root / filename).read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                index = {"word": 0, "_translated_label": 1}.get(node.func.id)
                if index is not None and len(node.args) > index:
                    arg = node.args[index]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        keys.add(arg.value)
    template = Environment(autoescape=True).parse(
        (root / "data/templates/al_interview_list_page.html").read_text()
    )
    for call in template.find_all(nodes.Call):
        if isinstance(call.node, nodes.Name) and call.node.name == "word":
            keys.add(call.args[0].value)
    # Keep the interactive review gallery in sync with runtime phrase discovery.
    import yaml

    blocks = yaml.safe_load_all(
        (root / "data/questions/test_accessibility_translation.yml").read_text()
    )
    gallery_block = next(
        block
        for block in blocks
        if block and "translation_test_phrases =" in block.get("code", "")
    )
    gallery = ast.literal_eval(ast.parse(gallery_block["code"]).body[0].value)
    assert keys <= set(gallery), keys - set(gallery)
    fields = lambda text: sorted(
        field for _, field, _, _ in Formatter().parse(text) if field is not None
    )
    for path in (root / "data/sources").glob("*-words.yml"):
        catalogs = safeyaml.load(path.read_text())  # Rejects duplicate YAML keys.
        for language, catalog in catalogs.items():
            from docassemble.base import functions

            monkeypatch.setitem(functions.word_collection, language, catalog)
            monkeypatch.setattr(functions.this_thread, "language", language)
            bundle = SimpleNamespace(broken_exhibit_titles=lambda: ["First", "Second"])
            warning = al_document.ALDocumentBundle.broken_documents_warning_html(bundle)
            assert " and " not in warning
            assert catalog["and"] in warning
            for key in keys:
                assert key in catalog, (language, key)
                assert isinstance(catalog[key], str) and catalog[key].strip(), (
                    language,
                    key,
                )
                assert fields(key) == fields(catalog[key]), (language, key)
        if len(catalogs) == 2:
            assert list(catalogs.values())[0] == list(catalogs.values())[1]


def test_email_status_translations_and_duplicate_submit():
    import shutil
    import subprocess

    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is needed for the email status regression")
    script = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
let callback, event, value = '<i></i>Custom label', calls = 0;
const attrs = {};
const button = {
  html(v) { if (v === undefined) return value; value = v; return this; },
  text(v) { value = v; return this; },
  attr(k, v) { if (v === undefined) return attrs[k]; attrs[k] = v; return this; },
  removeAttr(k) { delete attrs[k]; return this; },
  addClass() {}, removeClass() {}, prop() {}, each(fn) { fn.call(this); }
};
const context = {
  $: () => button, window: { addEventListener: (name, fn) => event = fn }, console,
  da_action_call: (a, b, fn) => { callback = fn; calls++; }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), context);
const send = () => context.aldocument_send_to_action('event', false, 'a@b.c', 'button');
send(); assert.equal(value, 'Sending...');
assert.equal(attrs['aria-disabled'], 'true');
send(); assert.equal(calls, 1);
context.alTranslate = s => 'Traduit " < & ' + s;
event(); assert.equal(value, 'Traduit " < & Sending...');
callback({success: false}); assert.equal(value, '<i></i>Custom label');
assert.equal(attrs['aria-disabled'], undefined);
send(); callback({success: true}); assert.equal(value, 'Traduit " < & Sent');
send(); assert.equal(calls, 2);
"""
    subprocess.run(
        [node, "-e", script, str(Path(__file__).parent / "data/static/aldocument.js")],
        check=True,
        capture_output=True,
        text=True,
    )
