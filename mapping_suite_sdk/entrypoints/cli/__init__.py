import logging


def typer_verbose_callback(show_verbose: bool) -> None:
    if show_verbose:
        logging.getLogger().setLevel(logging.DEBUG)
