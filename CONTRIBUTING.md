# Contributing to azvg

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/azvg.git
cd azvg
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e .
pip install -r requirements-dev.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=azvg --cov-report=html
```

## Code Quality

Format code:
```bash
black src/ tests/
```

Run linter:
```bash
ruff check src/
```

Type checking:
```bash
mypy src/azvg
```

## Commit Guidelines

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Ensure all checks pass
5. Update documentation
6. Submit PR with clear description


## Licensing

This project is dual-licensed under MIT OR Apache-2.0. Unless you explicitly 
state otherwise, any contribution intentionally submitted for inclusion in the 
work by you, as defined in the Apache-2.0 license, shall be dual licensed as 
above, without any additional terms or conditions.

By contributing to this project, you agree that your contributions will be 
licensed under both the MIT License and Apache License 2.0.
