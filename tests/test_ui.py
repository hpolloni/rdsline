"""Tests for the UI module."""

from unittest.mock import patch, ANY
import pytest
from rdsline.ui import UI


def test_ui_init() -> None:
    """Test UI initialization."""
    ui = UI(is_interactive=True)
    assert ui.is_interactive

    ui = UI(is_interactive=False)
    assert not ui.is_interactive


def test_read_input() -> None:
    """Test reading input."""
    ui = UI()
    with patch("builtins.input", return_value="test input"):
        result = ui.read_input("prompt> ")
        assert result == "test input"

    with patch("builtins.input", side_effect=EOFError()):
        with pytest.raises(EOFError):
            ui.read_input("prompt> ")


def test_print() -> None:
    """Test printing output."""
    ui = UI()
    with patch("builtins.print") as mock_print:
        ui.print("test message")
        mock_print.assert_called_once_with("test message", end="\n")

        ui.print("test message", end="")
        mock_print.assert_called_with("test message", end="")


def test_display_error() -> None:
    """Test displaying error messages."""
    ui = UI()
    with patch("builtins.print") as mock_print:
        ui.display_error("test error")
        mock_print.assert_called_once_with("Error: test error", file=ANY)


def test_get_command_input() -> None:
    """Test getting command input."""
    ui = UI()
    
    # Test normal input
    with patch("builtins.input", return_value="test command"):
        result = ui.get_command_input("prompt> ")
        assert result == "test command"

    # Test quit command
    with patch("builtins.input", return_value=".quit"):
        with pytest.raises(SystemExit):
            ui.get_command_input("prompt> ")

    # Test EOF
    with patch("builtins.input", side_effect=EOFError()):
        with pytest.raises(EOFError):
            ui.get_command_input("prompt> ")
