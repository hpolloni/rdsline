"""Tests for the CLI module."""

import os
from unittest.mock import patch, MagicMock, mock_open, call
import pytest
from rdsline import cli
from rdsline.settings import Settings
from rdsline.connections import NoopConnection
from rdsline.ui import UI
import yaml


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
    ui = UI(is_interactive=False)
    debug = cli.DebugCommand(False, ui)
    
    # Test initial state
    assert not debug.is_debug
    
    # Test toggling debug on
    with patch.object(ui, "print") as mock_print:
        debug([".debug"])
        mock_print.assert_called_once_with("Debugging is ON")
        assert debug.is_debug
    
    # Test toggling debug off
    with patch.object(ui, "print") as mock_print:
        debug([".debug"])
        mock_print.assert_called_once_with("Debugging is OFF")
        assert not debug.is_debug


def test_config_command() -> None:
    """Test the config command."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    
    # Test missing config file argument
    with patch.object(ui, "display_error") as mock_error:
        config([".config"])
        mock_error.assert_called_once_with("Expecting config file")
    
    # Test with config file
    with patch.object(Settings, "load_from_file") as mock_load, \
         patch.object(ui, "print") as mock_print:
        config([".config", "test_config.yaml"])
        mock_load.assert_called_once_with(os.path.expanduser("test_config.yaml"))
        mock_print.assert_called_once_with("Loaded configuration from test_config.yaml")


def test_profile_command_switch() -> None:
    """Test switching profiles."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    profile_cmd = cli.ProfileCommand(config, ui)
    
    # Test showing current connection when no profile name provided
    with patch.object(ui, "print") as mock_print:
        profile_cmd.switch_profile([".profile"])
        mock_print.assert_called_once()
        assert "NoopConnection" in mock_print.call_args[0][0]
    
    # Test switching to non-existent profile
    with patch.object(ui, "display_error") as mock_error:
        profile_cmd.switch_profile([".profile", "nonexistent"])
        mock_error.assert_called_once()
    
    # Test switching to existing profile
    with patch.object(Settings, "switch_profile") as mock_switch, \
         patch.object(ui, "print") as mock_print:
        profile_cmd.switch_profile([".profile", "test"])
        mock_switch.assert_called_once_with("test")
        mock_print.assert_called_once_with("Switched to profile: test")


def test_profile_command_list() -> None:
    """Test listing profiles."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    profile_cmd = cli.ProfileCommand(config, ui)
    
    # Test empty profiles
    with patch.object(ui, "print") as mock_print:
        profile_cmd.list_profiles([".profiles"])
        mock_print.assert_called_once_with("No profiles configured")
    
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
    with patch.object(ui, "print") as mock_print:
        profile_cmd.list_profiles([".profiles"])
        assert mock_print.call_count == 3  # Header + 2 profiles
        mock_print.assert_has_calls([
            call("Available profiles:"),
            call(" * default"),
            call("   test")
        ])


def test_profile_command_add_profile_success() -> None:
    """Test adding a new profile successfully."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config, ui)

    # Mock the input responses for interactive profile creation
    input_responses = [
        "test_profile",  # profile name
        "rds-secretsmanager",  # connection type
        "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",  # cluster ARN
        "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",  # secret ARN
        "test_db",  # database name
        "test_aws_profile",  # AWS profile
        "y"  # confirmation
    ]

    with patch.object(ui, "read_input", side_effect=input_responses), \
         patch.object(ui, "print") as mock_print, \
         patch("builtins.open", mock_open()) as mock_file:
        
        profile_cmd.add_profile([])
        
        assert "test_profile" in config.settings.profiles
        
        profile = config.settings.profiles["test_profile"]
        assert profile["type"] == "rds-secretsmanager"
        assert profile["cluster_arn"] == "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster"
        assert profile["secret_arn"] == "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret"
        assert profile["database"] == "test_db"
        assert profile["credentials"]["profile"] == "test_aws_profile"
        
        # Verify the file was opened for writing
        mock_file.assert_called_once_with("test_config.yaml", "w", encoding="utf-8")
        
        # Verify the final success message
        assert mock_print.call_args_list[-1] == call("\nProfile 'test_profile' added successfully")


def test_profile_command_add_profile_defaults() -> None:
    """Test adding a new profile with default values."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config, ui)

    # Mock the input responses with empty values for defaults
    input_responses = [
        "test_profile",  # profile name
        "",  # connection type (should default to rds-secretsmanager)
        "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",  # cluster ARN
        "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",  # secret ARN
        "test_db",  # database name
        "",  # AWS profile (should default to "default")
        "y"  # confirmation
    ]

    with patch.object(ui, "read_input", side_effect=input_responses), \
         patch.object(ui, "print") as mock_print, \
         patch("builtins.open", mock_open()):
        
        profile_cmd.add_profile([])
        
        profile = config.settings.profiles["test_profile"]
        assert profile["type"] == "rds-secretsmanager"  # default type
        assert profile["credentials"]["profile"] == "default"  # default AWS profile
        
        # Verify the final success message
        assert mock_print.call_args_list[-1] == call("\nProfile 'test_profile' added successfully")


def test_profile_command_add_profile_cancel() -> None:
    """Test cancelling profile creation."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config, ui)

    # Mock the input responses but answer 'n' to confirmation
    input_responses = [
        "test_profile",  # profile name
        "rds-secretsmanager",  # connection type
        "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",  # cluster ARN
        "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",  # secret ARN
        "test_db",  # database name
        "test_aws_profile",  # AWS profile
        "n"  # confirmation - cancel
    ]

    with patch.object(ui, "read_input", side_effect=input_responses), \
         patch.object(ui, "print") as mock_print, \
         patch("builtins.open", mock_open()) as mock_file:
        
        profile_cmd.add_profile([])
        
        assert "test_profile" not in config.settings.profiles
        mock_file.assert_not_called()
        
        # Verify the cancellation message
        assert mock_print.call_args_list[-1] == call("Profile creation cancelled")


def test_profile_command_add_profile_validation() -> None:
    """Test validation of profile inputs."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config, ui)

    # Test empty profile name
    with patch.object(ui, "read_input", return_value=""), \
         patch.object(ui, "display_error") as mock_error:
        profile_cmd.add_profile([])
        mock_error.assert_called_once_with("Profile name cannot be empty")

    # Test invalid connection type
    input_responses = [
        "test_profile",
        "invalid_type"
    ]
    with patch.object(ui, "read_input", side_effect=input_responses), \
         patch.object(ui, "display_error") as mock_error:
        profile_cmd.add_profile([])
        mock_error.assert_called_once_with("Unsupported database connection type: invalid_type")

    # Test empty required fields
    required_field_tests = [
        ["test_profile", "rds-secretsmanager", "", "secret", "db"],  # empty cluster ARN
        ["test_profile", "rds-secretsmanager", "cluster", "", "db"],  # empty secret ARN
        ["test_profile", "rds-secretsmanager", "cluster", "secret", ""]  # empty database
    ]
    
    for inputs in required_field_tests:
        with patch.object(ui, "read_input", side_effect=inputs), \
             patch.object(ui, "display_error") as mock_error:
            profile_cmd.add_profile([])
            mock_error.assert_called_once()
            assert "cannot be empty" in mock_error.call_args[0][0]


def test_profile_command_add_profile_keyboard_interrupt() -> None:
    """Test handling of KeyboardInterrupt during profile creation."""
    ui = UI(is_interactive=False)
    config = cli.ConfigCommand(ui)
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config, ui)

    with patch.object(ui, "read_input", side_effect=KeyboardInterrupt()), \
         patch.object(ui, "print") as mock_print, \
         patch("builtins.open", mock_open()) as mock_file:
        
        profile_cmd.add_profile([])
        
        # Verify the cancellation message
        assert mock_print.call_args_list[-1] == call("Profile creation cancelled")
        mock_file.assert_not_called()


def test_help_command() -> None:
    """Test the HelpCommand class."""
    ui = UI()
    help_cmd = cli.HelpCommand(ui)

    with patch.object(ui, "print") as mock_print:
        help_cmd([".help"])
        
        # Verify that help text contains all available commands
        help_text = mock_print.call_args[0][0]
        assert ".quit" in help_text
        assert ".config" in help_text
        assert ".debug" in help_text
        assert ".profile" in help_text
        assert ".profiles" in help_text
        assert ".addprofile" in help_text
        assert ".show" not in help_text  # Verify removed command is not present

        # Verify command descriptions
        assert "quits the REPL" in help_text
        assert "sets new connection settings from a file" in help_text
        assert "toggle debugging information" in help_text
        assert "show current connection or switch to a different profile" in help_text
        assert "list available profiles" in help_text
        assert "add a new profile interactively" in help_text


@patch("sys.stdin")
def test_main_repl_execution(mock_stdin: MagicMock) -> None:
    """Test the main REPL execution."""
    mock_stdin.isatty.return_value = True

    # Create a mock config with a default profile
    mock_config = {
        "profiles": {
            "default": {
                "type": "rds-secretsmanager",
                "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
                "secret_arn": "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",
                "database": "test-db",
                "credentials": {"profile": "default"}
            }
        }
    }

    # Create a mock boto3 session
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    # Mock config file loading and boto3 session
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))), \
         patch("sys.argv", ["rdsline"]), \
         patch("rdsline.settings.create_boto3_session", return_value=mock_session), \
         patch.object(UI, "get_command_input", side_effect=EOFError()), \
         patch.object(UI, "print"):

        with pytest.raises(SystemExit):
            cli.main()
