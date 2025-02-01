"""Tests for the CLI module."""

import os
from unittest.mock import patch, MagicMock
import pytest
from rdsline import cli
from rdsline.settings import Settings
from rdsline.connections import NoopConnection


def test_help_text() -> None:
    """Test that the help text includes all commands."""
    help_text = cli._help()
    assert ".quit" in help_text
    assert ".config" in help_text
    assert ".show" in help_text
    assert ".debug" in help_text
    assert ".profile" in help_text
    assert ".profiles" in help_text


def test_read_quit() -> None:
    """Test that reading .quit exits the program."""
    with patch("builtins.input", return_value=".quit"):
        with pytest.raises(SystemExit):
            cli._read("prompt> ")


def test_read_eof() -> None:
    """Test that EOF exits the program."""
    with patch("builtins.input", side_effect=EOFError()):
        with pytest.raises(SystemExit):
            cli._read("prompt> ")


def test_read_normal_input() -> None:
    """Test reading normal input."""
    with patch("builtins.input", return_value="SELECT * FROM table"):
        result = cli._read("prompt> ")
        assert result == "SELECT * FROM table"


def test_parse_args_defaults() -> None:
    """Test parsing command line arguments with defaults."""
    with patch("sys.argv", ["rdsline"]):
        args = cli._parse_args()
        assert args.config is None
        assert args.profile is None
        assert not args.debug


def test_parse_args_all_options() -> None:
    """Test parsing command line arguments with all options."""
    with patch("sys.argv", ["rdsline", "--config", "config.yaml", "--profile", "test", "--debug"]):
        args = cli._parse_args()
        assert args.config == "config.yaml"
        assert args.profile == "test"
        assert args.debug


def test_debug_command() -> None:
    """Test the debug command."""
    debug = cli.DebugCommand(False)
    
    # Test initial state
    assert not debug.is_debug
    
    # Test toggling debug on
    result = debug([".debug"])
    assert "Debugging is ON" in result
    assert debug.is_debug
    
    # Test toggling debug off
    result = debug([".debug"])
    assert "Debugging is OFF" in result
    assert not debug.is_debug


def test_config_command() -> None:
    """Test the config command."""
    config = cli.ConfigCommand()
    
    # Test missing config file argument
    result = config([".config"])
    assert "ERROR: Expecting config file" in result
    
    # Test with config file
    with patch.object(Settings, "load_from_file") as mock_load:
        result = config([".config", "test_config.yaml"])
        mock_load.assert_called_once_with(os.path.expanduser("test_config.yaml"))


def test_profile_command_switch() -> None:
    """Test switching profiles."""
    config = cli.ConfigCommand()
    profile_cmd = cli.ProfileCommand(config)
    
    # Test missing profile name
    result = profile_cmd.switch_profile([".profile"])
    assert "ERROR: Expecting profile name" in result
    
    # Test switching to non-existent profile
    result = profile_cmd.switch_profile([".profile", "nonexistent"])
    assert "ERROR:" in result
    
    # Test switching to existing profile
    with patch.object(Settings, "switch_profile") as mock_switch:
        result = profile_cmd.switch_profile([".profile", "test"])
        mock_switch.assert_called_once_with("test")
        assert "Switched to profile: test" in result


def test_profile_command_list() -> None:
    """Test listing profiles."""
    config = cli.ConfigCommand()
    profile_cmd = cli.ProfileCommand(config)
    
    # Test empty profiles
    result = profile_cmd.list_profiles([".profiles"])
    assert "No profiles configured" in result
    
    # Test with profiles
    config.settings.profiles = {
        "default": {
            "type": "rds-secretsmanager",
            "cluster_arn": "default_arn",
            "secret_arn": "default_secret",
            "database": "default_db"
        },
        "test": {
            "type": "rds-secretsmanager",
            "cluster_arn": "test_arn",
            "secret_arn": "test_secret",
            "database": "test_db"
        }
    }
    result = profile_cmd.list_profiles([".profiles"])
    assert "Available profiles:" in result
    assert "default" in result
    assert "test" in result


@patch("builtins.input")
@patch("builtins.print")
def test_main_repl_execution(mock_print: MagicMock, mock_input: MagicMock) -> None:
    """Test the main REPL execution."""
    # Set up mock inputs to simulate user interaction
    mock_input.side_effect = [
        ".help",                 # Help command
        ".quit"                  # Quit command
    ]
    
    # Mock sys.stdin.isatty() to simulate terminal
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.isatty.return_value = True
        
        # Mock sys.argv to avoid needing command line arguments
        with patch("sys.argv", ["rdsline"]):
            with pytest.raises(SystemExit):
                cli.main()
    
    # Verify that help text was printed
    help_text = cli._help()
    help_text_printed = False
    for call in mock_print.call_args_list:
        args = call[0][0] if call[0] else ""
        if isinstance(args, str) and help_text in args:
            help_text_printed = True
            break
    assert help_text_printed, "Help text was not printed"
