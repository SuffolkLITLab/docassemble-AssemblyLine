# coding=utf-8
import os
from typing import List, Optional, Tuple
from docassemble.base.util import url_action, path_and_mimetype
import yaml
import pycountry

__all__ = [
    "get_tuples",
    "get_language_list_dropdown",
    "get_language_list_dropdown_item",
    "get_language_list",
    "get_language_list_item",
]


def _package_name(package_name: Optional[str] = None) -> str:
    """Get package name without the name of the given module. By default this is `docassemble.AssemblyLine.language`

    Args:
        package_name: the name of the package to get the package name from (defaults to `docassemble.AssemblyLine.language`)

    Returns:
        str: the package name without the name of the given module
    """
    if not package_name:
        package_name = __name__
    try:
        return ".".join(package_name.split(".")[:-1])
    except:
        return package_name


def get_local_languages_yaml() -> str:
    """
    Get the path to the local languages.yml file. If it does not exist, it will return the path to the languages.yml

    Returns:
        str: the path to the local languages.yml file if it exists, otherwise the path to the languages.yml file
    """
    try:
        local_yaml = path_and_mimetype("data/sources/languages.yml")[0]
    except:
        local_yaml = None

    if local_yaml and os.path.isfile(local_yaml):
        return local_yaml

    al_package_name = _package_name()
    this_yaml = path_and_mimetype(f"{al_package_name}:data/sources/languages.yml")[0]
    return this_yaml


def get_tuples(
    lang_codes: List[str], languages_path: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Returns a list of tuples representing the language name, followed by language ISO 639-1 code.

    It will use the native_name value from the languages.yml file if available, otherwise it will use the
    English name from pycountry. If neither is present, it will use the language code itself.

    Args:
        lang_codes: a list of ISO 639-1 language codes (e.g. ['en', 'es'])
        languages_path: the path to the languages.yml file (defaults to data/sources/languages.yml)

    Returns:
        A list of tuples representing the language name, followed by language ISO 639-1 code.

    """
    if not languages_path:
        languages_path = get_local_languages_yaml()

    if languages_path is not None:
        with open(languages_path, "r", encoding="utf-8") as stream:
            # use our hand-built dictionary matching languages to native name for languages
            # if it is available
            languages = yaml.safe_load(stream)
        tuples = []
        for lang in lang_codes:
            # English name
            try:
                english_name = pycountry.languages.get(alpha_2=lang).name
            except:
                english_name = lang
            tuples.append((languages[lang].get("native_name", english_name), lang))
        return tuples
    else:
        # Get the english name for the language code from pycountry as a fallback
        return [
            (
                (
                    pycountry.languages.get(alpha_2=lang).name
                    if pycountry.languages.get(alpha_2=lang)
                    else lang
                ),
                lang,
            )
            for lang in lang_codes
        ]


def get_language_list_dropdown(
    lang_codes: List[str],
    current: str = "",
    languages_path: Optional[str] = None,
    event_name="al_change_language",
    icon="fa-solid fa-language fa-xl",
    extra_class: str = "text-light",
) -> str:
    """
    Get a Bootstrap 5 dropdown menu for language selection that can be added to navigation bar.

    Args:
        lang_codes: a list of ISO 639-1 language codes (e.g. ['en', 'es'])
        current: the current language code
        languages_path: the path to the languages.yml file (defaults to data/sources/languages.yml)
        event_name: the name of the event to trigger when the language is changed
        icon: the name of the icon to use for the dropdown menu (defaults to fa-solid fa-language fa-xl)
        extra_class: additional classes to add to the link
    Returns:
      A string containing the HTML for a dropdown menu for language selection.
    """
    list_start = f"""<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle { extra_class }" href="#" id="languageSelector" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false" aria-label="Language selection">
      <i class="{ icon }"></i>
    </a>
    <div class="dropdown-menu" aria-labelledby="languageSelector">
  """
    list_end = """
    </div>
  </li>
  """
    if not languages_path:
        languages_path = get_local_languages_yaml()
    languages = get_tuples(lang_codes, languages_path=languages_path)

    for language in languages:
        if language[1] == current:
            list_start += get_language_list_dropdown_item(
                language, link=False, event_name=event_name
            )
        else:
            list_start += get_language_list_dropdown_item(
                language, event_name=event_name
            )
    return list_start + list_end


def get_language_list_dropdown_item(
    language: Tuple[str, str], link: bool = True, event_name="al_change_language"
) -> str:
    """Given an ordered tuple, returns a link to the current interview with lang=language code and the link title
    given in the first part of the tuple.

    Args:
        language: a tuple containing the language name and language code
        link: whether to return a link or just the text
        event_name: the name of the event to trigger when the language is changed

    Returns:
        str: A string containing the HTML for a dropdown menu item for language selection.
    """

    if link:
        return f"""<a class="dropdown-item" href="{ url_action(event_name, lang = language[1]) }">{ language[0] }</a>"""
    else:
        return f'<span class="dropdown-item-text">{ language[0] }</span>'


def get_language_list(
    languages: Optional[List[Tuple[str, str]]] = None,
    current="",
    lang_codes: Optional[List[str]] = None,
    languages_path: Optional[str] = None,
    event_name="al_change_language",
) -> str:
    """
    Given a list of language codes, returns
    a Bootstrap-formatted unordered inline list. The current language will not be a link.

    Deprecated behavior: instead of a list of language codes, you can provide list of
    tuples containing the language name and language code. This is deprecated and may be removed in a future version.

    Args:
        languages: a list of tuples containing the language name and language code (deprecated)
        current: the current language code
        lang_codes: a list of ISO 639-1 language codes (e.g. ['en', 'es'])
        languages_path: the path to the languages.yml file (defaults to data/sources/languages.yml)
        event_name: the name of the event to trigger when the language is changed

    Returns:
        A string containing the HTML for an unordered inline list of language selection.
    """
    if not languages_path:
        languages_path = get_local_languages_yaml()
    if not languages:
        if not lang_codes:
            raise ValueError("Either languages or lang_codes must be provided")
        languages = get_tuples(lang_codes, languages_path=languages_path)

    list_start = '<ul class="list-inline">'
    list_start += '<li class="list-inline-item"><b>Language</b>:</li>'
    list_end = "</ul>"
    for language in languages:
        if language[1] == current:
            list_start += get_language_list_item(
                language, link=False, event_name=event_name
            )
        else:
            list_start += get_language_list_item(language, event_name=event_name)
    return list_start + list_end


def get_language_list_item(language, link=True, event_name="al_change_language") -> str:
    """Given an ordered tuple, returns a link to the current interview with lang=language code and the link title
    given in the first part of the tuple.

    Args:
        language: a tuple containing the language name and language code
        link: whether to return a link or just the text
        event_name: the name of the event to trigger when the language is changed

    Returns:
        str: A string containing the HTML for an unordered inline list item for language selection.
    """
    li_start = '<li class="list-inline-item">'
    li_end = "</li>"

    if link:
        iurl = url_action(event_name, lang=language[1])
        return (
            li_start
            + '<a target="_self" href="'
            + iurl
            + '">'
            + language[0]
            + "</a>"
            + li_end
        )
    else:
        return li_start + language[0] + li_end
