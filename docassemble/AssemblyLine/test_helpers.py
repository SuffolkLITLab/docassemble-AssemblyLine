# do not pre-load
import os
import tempfile
from types import SimpleNamespace

# Importing anything in docassemble webapp initializes docassemble's database
# configuration. Supply an isolated empty config when the test runner has
# not provided one.
_test_config_dir = None
if not os.environ.get("DA_CONFIG_FILE"):
    _test_config_dir = tempfile.TemporaryDirectory(prefix="assemblyline-test-config-")
    os.environ["DA_CONFIG_FILE"] = os.path.join(_test_config_dir.name, "config.yml")
    with open(os.environ["DA_CONFIG_FILE"], "w", encoding="utf-8") as config:
        config.write(f'{{ "log": {_test_config_dir.name} }}\n')
import docassemble.base.config

if not docassemble.base.config.loaded:
    docassemble.base.config.load()

from contextlib import ExitStack
from docassemble.base.thread_context import (
    this_thread,
    global_context,
    user_dict_context,
    empty_globals,
)


class ContextForTests:

    def __init__(self, package):
        self.package = package
        self.stack = ExitStack()

    def __enter__(self):
        # url_root = daconfig.get('url root', 'http://localhost') + daconfig.get('root', '/')
        # url = url_root + 'interview'
        # self.app_context = self.stack.enter_context(app.app_context())
        # self.test_context = self.stack.enter_context(app.test_request_context(base_url=url_root, path=url))
        # app.preprocess_request()
        # login_as_admin(url, url_root)
        set_empty_thread(self.stack)
        # self.stack.enter_context(user_dict_context(fresh_dictionary()))
        this_thread.current_package = self.package
        this_thread.current_info.update(
            {"yaml_filename": self.package + ":data/questions/test.yml"}
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # app.login_manager._update_request_context_with_user()  # pylint: disable=no-member
        self.stack.close()


def set_empty_thread(stack):
    stack.enter_context(global_context(empty_globals()))


def set_thread_lang(stack, language):
    the_new_globals = empty_globals()
    the_new_globals.language = language
    stack.enter_context(global_context(the_new_globals))


def set_thread_package(stack, package):
    the_new_globals = empty_globals()
    the_new_globals.current_question = SimpleNamespace(package=package)
    stack.enter_context(global_context(the_new_globals))


def set_user_dict(stack, user_dict):
    stack.enter_context(user_dict_context(user_dict))
