# Suffolk LIT Lab Document Assembly Line Package

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, build, and test the repository:
- `python3 -m pip install --upgrade pip`
- `python3 -m pip install -e .` -- installs package in development mode. Takes 30-60 seconds. NEVER CANCEL. May fail with network timeouts; retry if needed.
- `python3 setup.py sdist` -- builds package distribution. Takes <1 second.
- `python3 -c "import docassemble.AssemblyLine; print('Version:', docassemble.AssemblyLine.__version__)"` -- verifies package imports correctly

### Linting and type checking:
- Install linting tools: `python3 -m pip install black mypy types-PyYAML pandas-stubs types-psycopg2 pillow pikepdf sqlalchemy[mypy]`
- `black --check docassemble/AssemblyLine` -- checks code formatting. Takes <5 seconds.
- `black docassemble/AssemblyLine` -- auto-formats code if needed. Takes <5 seconds.
- `mypy docassemble/AssemblyLine --config-file pyproject.toml` -- type checking. Takes 3-5 seconds. NEVER CANCEL.

### Testing:
- **Unit Tests**: Python unit tests exist in `test_*.py` files but require full docassemble environment to run. DO NOT attempt to run them locally - they will fail with import errors.
- **Integration Tests**: Use ALKiln framework with `.feature` files in `docassemble/AssemblyLine/data/sources/`. These require a running docassemble server and browser automation.
- **GitHub Actions Testing**: 
  - `ALKiln v5 tests` workflow runs integration tests on every push - takes 15-30 minutes. NEVER CANCEL.
  - `Run python only unit tests` workflow uses `SuffolkLITLab/ALActions/pythontests@main` - takes 5-10 minutes. NEVER CANCEL.
  - `formatting action` workflow runs black and docsig formatting checks - takes 2-3 minutes.

## Validation

- **NEVER try to run Python unit tests locally** - they require the full docassemble framework which cannot be installed in most development environments.
- Always run `black --check` and `mypy` before committing changes.
- Always verify package imports with the import test command above.
- The build process is very fast (<1 second) so always run `python3 setup.py sdist` to verify no syntax errors.
- Test your changes by creating simple interview files in `docassemble/AssemblyLine/data/questions/` and verifying they don't break the package structure.
- **Manual validation**: After making code changes, always run: `python3 -c "import docassemble.AssemblyLine; print('Package imports successfully')"` to ensure the package structure is valid.

## Common tasks

### Repository structure:
```
/
├── .github/workflows/          # GitHub Actions CI/CD
├── docassemble/AssemblyLine/   # Main Python package
│   ├── data/questions/         # 35 YAML interview files
│   ├── data/sources/          # Test files (.feature) and translations
│   ├── data/static/           # CSS, JS, images
│   ├── data/templates/        # Document templates (.docx, .pdf)
│   ├── *.py                   # 13 Python modules (core functionality)
│   └── test_*.py              # Unit tests (require docassemble server)
├── setup.py                   # Package configuration
├── pyproject.toml             # Tool configuration (black, mypy)
├── README.md                  # Installation and usage docs
└── bumpversion.sh             # Version bump script
```

### Core Python modules:
- `al_general.py` - Core classes (ALAddress, ALIndividual, etc.)
- `al_document.py` - Document assembly classes (ALDocument, ALDocumentBundle)
- `al_courts.py` - Court-related functionality
- `sessions.py` - Session management
- `language.py` - Internationalization support
- `sign.py` - Digital signature support

### Key interview files:
- `assembly_line.yml` - Main Assembly Line package include
- `ql_baseline.yml` - Question library baseline
- `test_*.yml` - Test interviews used by ALKiln

### Development workflow:
1. Make code changes to `.py` files
2. Run `black docassemble/AssemblyLine` to format
3. Run `mypy docassemble/AssemblyLine --config-file pyproject.toml` to type check
4. Run `python3 setup.py sdist` to verify build works
5. Test imports: `python3 -c "import docassemble.AssemblyLine; print('OK')"`
6. Commit changes - GitHub Actions will run full test suite

### ALKiln Testing Framework:
- ALKiln is a Node.js tool that automates browser testing of docassemble interviews
- Requires: `npm install -g @suffolklitlab/alkiln` (needs Chrome/Chromium)
- Test files: `*.feature` files in `docassemble/AssemblyLine/data/sources/`
- Uses Gherkin syntax to define test scenarios
- Tests run against live docassemble server instances
- **CRITICAL**: ALKiln tests take 15-30 minutes per run. NEVER CANCEL.
- Local ALKiln testing requires full docassemble server setup which is complex

### Timing expectations:
- Package installation: 30-60 seconds (dependency downloads)
- Build (`setup.py sdist`): <1 second  
- Code formatting (black): <5 seconds
- Type checking (mypy): 3-5 seconds
- GitHub Actions ALKiln tests: 15-30 minutes. NEVER CANCEL.
- GitHub Actions Python tests: 5-10 minutes. NEVER CANCEL.

### DO NOT do these things:
- Do not attempt to run unit tests locally (`python3 -m unittest` will fail)
- Do not try to install full docassemble server locally (complex, requires Docker)
- Do not cancel long-running GitHub Actions workflows
- Do not modify the core docassemble dependencies without careful testing

### Always check these files when making changes:
- `docassemble/AssemblyLine/__init__.py` - for version updates
- `setup.py` - for dependency changes  
- `pyproject.toml` - for tool configuration
- Related `.yml` interview files when changing Python classes

### Package publication:
- Use `./bumpversion.sh` to increment version numbers
- Builds are automatically published to PyPI via GitHub Actions
- Package is also deployed to Suffolk LIT Lab's development docassemble server

This package is a docassemble library for legal document assembly, providing reusable components for creating guided online court forms. It's part of the Suffolk LIT Lab's broader Assembly Line project for increasing access to justice through technology.