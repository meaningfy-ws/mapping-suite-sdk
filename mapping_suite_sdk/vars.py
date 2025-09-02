from typing import Tuple

MSSDK_LOGGING_STRING_FORMAT = "%(asctime)s | %(levelname)s | %(filename)s | Line: %(lineno)d | %(message)s"
MSSDK_LOGGING_EXTENDED_STRING_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s | %(funcName)s | Line: %(lineno)d | %(message)s"
MSSDK_LOGGING_MESSAGE_FORMAT = "[{package_source}] - {message}"
MSSDK_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# See typer.Typer docs
MSSDK_TYPER_DEFAULT_ARGS = {
    "no_args_is_help": True,
    "pretty_exceptions_enable": True,
    "pretty_exceptions_show_locals": False,
    "pretty_exceptions_short": True,
    "add_completion": False
}

# See typer.main.Typer command function docs
MSSDK_TYPER_COMMANDS_DEFAULT_ARGS = {
    "no_args_is_help": True,
}

SUPPORTED_TEXT_FILE_EXTENSIONS: Tuple = (".html", ".json", ".csv", ".ttl")
SUPPORTED_BYTES_FILE_EXTENSIONS: Tuple = (".zip",)
