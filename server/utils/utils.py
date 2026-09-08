import logging
from datetime import datetime


def get_now_iso():
    return datetime.now(timezone.utc).isoformat()


def gen_diag(component: str):
    """
    Generate a diagnostics function with component prefixed to it.
    """
    component_fmt = f"{component}:"
    class diag:
        @staticmethod
        def debug(msg: str):
            logging.debug(f"{component_fmt} {msg}")
        @staticmethod
        def info(msg: str):
            logging.info(f"{component_fmt} {msg}")
        @staticmethod
        def warning(msg: str):
            logging.warning(f"{component_fmt} {msg}")
        @staticmethod
        def error(msg: str):
            logging.error(f"{component_fmt} {msg}")
        @staticmethod
        def critical(msg: str):
            logging.critical(f"{component_fmt} {msg}")

    return diag()


def enforce_enum(enum_cls, value, caller=""):
    """Make sure enums are known values."""
    try:
        return enum_cls(value)
    except ValueError:
        if caller != "":
            caller = f"{caller}:"
        diag.error(f"{caller} Invalid {enum_cls.__name__} '{value}'")
        raise
