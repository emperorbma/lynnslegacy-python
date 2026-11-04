"""Shared FerUs line console: Logosta password entry + godmode hooks."""

from lynn.console import (
    PASSWORD,
    close_console,
    feed_key,
    open_console,
)
from lynn.events import reset_events
import lynn.events as events


def setup_function(_):
    reset_events()


def teardown_function(_):
    reset_events()


def test_logosta_defaults_match_fb():
    con = open_console(obj=object())
    assert con.prompt == "PASS> "
    assert con.max_entry == 10
    assert con.digits_only is False
    feed_key(con, 0, "F")
    feed_key(con, 0, "x")
    feed_key(con, 8, "")
    assert con.text == "F"
    feed_key(con, 13, "")
    assert con.done is True
    assert con.text != PASSWORD


def test_digits_only_and_submit_hook():
    got = []

    def _submit(text):
        got.append(text)
        close_console()

    con = open_console(
        prompt="Gold +> ",
        text="10",
        digits_only=True,
        max_entry=4,
        on_submit=_submit,
    )
    feed_key(con, 0, "a")
    assert con.text == "10"
    feed_key(con, 8, "")
    feed_key(con, 8, "")
    feed_key(con, 0, "2")
    feed_key(con, 0, "5")
    feed_key(con, 13, "")
    assert got == ["25"]
    assert events.console is None


def test_esc_cancel_hook():
    cancelled = []

    def _cancel():
        cancelled.append(True)
        close_console()

    con = open_console(prompt="Heal +> ", text="", on_cancel=_cancel)
    feed_key(con, 27, "")
    assert cancelled == [True]
    assert con.cancelled is True
    assert events.console is None


def test_logosta_esc_does_not_cancel_without_hook():
    con = open_console(obj=object())
    feed_key(con, 27, "")
    assert con.done is False
    assert con.text == ""
    close_console()
