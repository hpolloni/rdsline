# Contributing to RDSLine

Thank you for your interest in contributing to RDSLine! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Make
- Git

### Getting Started

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/rdsline.git
   cd rdsline
   ```

2. Set up the development environment:
   ```bash
   make setup-dev
   ```
   This will create a virtual environment and install all development dependencies.

## Development Workflow

### Code Quality Checks

We use several tools to ensure code quality:

- **mypy**: Static type checking
- **black**: Code formatting (line length: 100)
- **pylint**: Code linting
- **pytest**: Unit testing
- **coverage**: Code coverage reporting

Run all quality checks with:
```bash
make check
```

This will run type checking, formatting, linting, tests, and generate a coverage report.

### Running Tests

To run only the test suite without other checks:
```bash
make test
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Maximum line length is 100 characters
- Use descriptive variable names
- Add docstrings for all functions, classes, and modules

### Commit Messages

Write clear and descriptive commit messages:
- Start with a short summary line (50 chars or less)
- Follow with a blank line
- Add a more detailed description if needed

Example:
```
Add multi-profile support

- Implement Settings class for managing profiles
- Add profile switching and listing commands
- Update CLI to show current profile in prompt
```

## Pull Request Process

1. Create a new branch for your feature or bugfix
2. Make your changes, following our code style guidelines
3. Add or update tests as needed
4. Run `make check` to ensure all checks pass
5. Push your changes and create a pull request
6. Update the README.md if needed

## Getting Help

If you have questions or need help, please:
1. Check existing issues
2. Create a new issue with a clear description
3. Label the issue appropriately

## License

By contributing to RDSLine, you agree that your contributions will be licensed under the MIT License.
