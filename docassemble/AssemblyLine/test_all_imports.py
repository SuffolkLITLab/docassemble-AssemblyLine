# Makes sure that loading each module file works.
# Includes all imports not covered by other test files.

from .al_courts import *
from .custom_jinja_filters import *
from .language import *
from .sign import *

try:
    from .sessions import *
except SystemExit as ex:
    print(f"Ignoring SystemExit error (expected from config.py: {ex})")
