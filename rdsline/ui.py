"""
User interface module.
"""

import sys


class UI:
    """
    Handles user interface input and output.
    """

    def __init__(self, is_interactive=None):
        """
        Initialize the UI.

        Args:
            is_interactive: Whether the UI is interactive.
        """
        self.is_interactive = is_interactive

    def read_input(self, prompt=""):
        """
        Read input from the user.

        Args:
            prompt: The prompt to display.

        Returns:
            The user's input.

        Raises:
            KeyboardInterrupt: If the user presses Ctrl+C.
            EOFError: If EOF is encountered.
        """
        line = input(prompt)
        if line == ".quit":
            sys.exit(0)
        return line

    def get_command_input(self, prompt=""):
        """
        Get command input from the user.

        Args:
            prompt: The prompt to display.

        Returns:
            The command input.
        """
        if not self.is_interactive:
            line = sys.stdin.readline()
            if not line:
                raise EOFError()
            return line.rstrip("\n")
        return self.read_input(prompt)

    def print(self, message, end="\n"):
        """
        Print a message to the user.

        Args:
            message: The message to print.
            end: String to append after the message.
        """
        print(message, end=end)

    def display_error(self, message):
        """
        Display an error message to the user.

        Args:
            message: The error message to display.
        """
        print(f"Error: {message}", file=sys.stderr)

    def display_list(self, items, prefix=""):
        """
        Display a list of items.

        Args:
            items: The items to display.
            prefix: Prefix to add before each item.
        """
        for item in items:
            self.print(f"{prefix}{item}")
