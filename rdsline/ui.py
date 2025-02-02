"""
User interface module.
"""

import sys


class UI:
    """
    Handles user interface input and output.
    """

    def __init__(self, is_interactive: bool = True):
        """
        Initialize the UI.

        Args:
            is_interactive (bool): Whether the UI is interactive.
        """
        self.is_interactive = is_interactive

    def read_input(self, prompt: str = "") -> str:
        """
        Read input from the user.

        Args:
            prompt (str): The prompt to display.

        Returns:
            str: The user's input.

        Raises:
            KeyboardInterrupt: If the user presses Ctrl+C.
            EOFError: If EOF is encountered.
        """
        line = input(prompt)
        if line == ".quit":
            sys.exit(0)
        return line

    def get_command_input(self, prompt: str = "") -> str:
        """
        Get command input from the user.

        Args:
            prompt (str): The prompt to display.

        Returns:
            str: The command input.
        """
        if not self.is_interactive:
            line = sys.stdin.readline()
            if not line:
                raise EOFError()
            return line.rstrip("\n")
        return self.read_input(prompt)

    def print(self, message: str, end: str = "\n") -> None:
        """
        Print a message to the user.

        Args:
            message (str): The message to print.
            end (str): String to append after the message.
        """
        print(message, end=end)

    def display_error(self, message: str) -> None:
        """
        Display an error message to the user.

        Args:
            message (str): The error message to display.
        """
        print(f"Error: {message}", file=sys.stderr)

    def display_list(self, items: list[str], prefix: str = "") -> None:
        """
        Display a list of items.

        Args:
            items (list[str]): The items to display.
            prefix (str): Prefix to add before each item.
        """
        for item in items:
            self.print(f"{prefix}{item}")
