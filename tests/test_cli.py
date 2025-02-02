"""Tests for the CLI module."""

import os
from unittest.mock import patch, MagicMock
import pytest
from rdsline import cli
from rdsline.settings import Settings
from rdsline.connections import NoopConnection
import yaml
from unittest.mock import mock_open


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
    
    # Test showing current connection when no profile name provided
    result = profile_cmd.switch_profile([".profile"])
    assert isinstance(result, str)
    assert "NoopConnection" in result
    
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


def test_profile_command_add_profile_success() -> None:
    """Test adding a new profile successfully."""
    config = cli.ConfigCommand()
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config)

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

    with patch("builtins.input", side_effect=input_responses), \
         patch("builtins.print"), \
         patch("builtins.open", mock_open()) as mock_file:
        
        result = profile_cmd.add_profile([])
        
        assert "Profile 'test_profile' added successfully" in result
        assert "test_profile" in config.settings.profiles
        
        profile = config.settings.profiles["test_profile"]
        assert profile["type"] == "rds-secretsmanager"
        assert profile["cluster_arn"] == "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster"
        assert profile["secret_arn"] == "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret"
        assert profile["database"] == "test_db"
        assert profile["credentials"]["profile"] == "test_aws_profile"
        
        # Verify the file was opened for writing
        mock_file.assert_called_once_with("test_config.yaml", "w", encoding="utf-8")


def test_profile_command_add_profile_defaults() -> None:
    """Test adding a new profile with default values."""
    config = cli.ConfigCommand()
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config)

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

    with patch("builtins.input", side_effect=input_responses), \
         patch("builtins.print"), \
         patch("builtins.open", mock_open()):
        
        result = profile_cmd.add_profile([])
        
        profile = config.settings.profiles["test_profile"]
        assert profile["type"] == "rds-secretsmanager"  # default type
        assert profile["credentials"]["profile"] == "default"  # default AWS profile


def test_profile_command_add_profile_cancel() -> None:
    """Test cancelling profile creation."""
    config = cli.ConfigCommand()
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config)

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

    with patch("builtins.input", side_effect=input_responses), \
         patch("builtins.print"), \
         patch("builtins.open", mock_open()) as mock_file:
        
        result = profile_cmd.add_profile([])
        
        assert "Profile creation cancelled" in result
        assert "test_profile" not in config.settings.profiles
        mock_file.assert_not_called()


def test_profile_command_add_profile_validation() -> None:
    """Test validation of profile inputs."""
    config = cli.ConfigCommand()
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config)

    # Test empty profile name
    with patch("builtins.input", return_value=""), \
         patch("builtins.print"):
        result = profile_cmd.add_profile([])
        assert "Profile name cannot be empty" in result

    # Test invalid connection type
    input_responses = [
        "test_profile",
        "invalid_type"
    ]
    with patch("builtins.input", side_effect=input_responses), \
         patch("builtins.print"):
        result = profile_cmd.add_profile([])
        assert "Unsupported database connection type" in result

    # Test empty required fields
    required_field_tests = [
        ["test_profile", "rds-secretsmanager", "", "secret", "db"],  # empty cluster ARN
        ["test_profile", "rds-secretsmanager", "cluster", "", "db"],  # empty secret ARN
        ["test_profile", "rds-secretsmanager", "cluster", "secret", ""]  # empty database
    ]
    
    for inputs in required_field_tests:
        with patch("builtins.input", side_effect=inputs), \
             patch("builtins.print"):
            result = profile_cmd.add_profile([])
            assert "cannot be empty" in result


def test_profile_command_add_profile_keyboard_interrupt() -> None:
    """Test handling of KeyboardInterrupt during profile creation."""
    config = cli.ConfigCommand()
    config.config_file = "test_config.yaml"  # Set the config file path
    profile_cmd = cli.ProfileCommand(config)

    with patch("builtins.input", side_effect=KeyboardInterrupt()), \
         patch("builtins.print"), \
         patch("builtins.open", mock_open()) as mock_file:
        
        result = profile_cmd.add_profile([])
        
        assert "Profile creation cancelled" in result
        mock_file.assert_not_called()


@patch("builtins.input")
@patch("builtins.print")
def test_main_repl_execution(mock_print: MagicMock, mock_input: MagicMock) -> None:
    """Test the main REPL execution."""
    # Set up mock inputs to simulate user interaction
    mock_input.side_effect = [
        ".help",                 # Help command
        ".quit"                  # Quit command
    ]

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
         patch("sys.stdin") as mock_stdin, \
         patch("sys.argv", ["rdsline"]), \
         patch("rdsline.settings.create_boto3_session", return_value=mock_session):
        
        mock_stdin.isatty.return_value = True
        
        with pytest.raises(SystemExit):
            cli.main()
