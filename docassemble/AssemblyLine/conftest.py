# do not pre-load
# Import plugin hooks before importing DAL stuff that uses it
import docassemble.base.hooks
from docassemble.base.plugin_manager import pm
import pluggy

hookimpl = pluggy.HookimplMarker("docassemble")


class Mocks:
    @hookimpl
    def get_configuration() -> dict:  # type: ignore
        """Get configuration"""
        return {}

    @hookimpl
    def file_finder(file_reference):
        return {"fullpath": file_reference.replace(".", "/").replace(":", "/")}

    @hookimpl
    def get_default_timezone() -> str:  # type: ignore
        """Default timezone"""
        return "America/New_York"


if not pm.is_registered(Mocks):
    pm.register(Mocks)
