import logging
from datetime import datetime, timezone
import re
from urllib.parse import parse_qs, urlparse


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


def extract_youtube_id(url: str) -> str:
  # Parse the URL
  parsed_url = urlparse(url)

  # Handle youtu.be short links
  if parsed_url.hostname in ["youtu.be", "www.youtu.be"]:
    return parsed_url.path.lstrip("/")

  # Handle youtube.com links
  if parsed_url.hostname in [
      "youtube.com",
      "www.youtube.com",
      "m.youtube.com",
  ]:
    # Handle /embed/ and /v/ URLs
    if parsed_url.path.startswith(("/embed/", "/v/")):
      return parsed_url.path.split("/")[2]

    # Handle /watch?v= URLs
    if parsed_url.path == "/watch":
      query_params = parse_qs(parsed_url.query)
      return query_params.get("v", [None])[0]

    # Handle /shorts/ URLs
    if parsed_url.path.startswith("/shorts/"):
      return parsed_url.path.split("/")[2]

  # Fallback regex for edge cases
  match = re.search(
      r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
      url,
  )
  return match.group(1) if match else None

