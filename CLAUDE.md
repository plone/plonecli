# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

plonecli is a command-line interface for creating Plone packages. It orchestrates three main components:

1. **mr.bob** - The low-level templating engine that handles file generation and Q&A sessions
2. **bobtemplates.plone** - Collection of Plone-specific templates (addon, content_type, theme, etc.)
3. **plonecli** - High-level CLI wrapper providing developer workflow commands

### Key Components

#### Template Registry (`plonecli/registry.py`)
- **Template Discovery**: Uses `pkg_resources.iter_entry_points("mrbob_templates")` to find available templates
- **Context Detection**: Detects if you're in a package via `bobtemplate.cfg` to show relevant commands
- **Template Organization**: Separates standalone templates (addon) from subtemplates (content_type, theme, etc.)
- **Template Resolution**: Maps friendly CLI names to actual mr.bob template paths

#### CLI Interface (`plonecli/cli.py`)
- **Context-Sensitive Commands**: Different commands available globally vs. in package directories
- **Command Chaining**: Supports multiple commands in sequence (e.g., `plonecli create addon my.package build serve`)
- **Click Integration**: Uses `ClickFilteredAliasedGroup` for context-aware command filtering

#### mr.bob Configuration (`plonecli/configure_mrbob.py`)
- **Global Settings**: Manages user preferences in `~/.mrbob`
- **Template Defaults**: Pre-fills common values (author, email, Plone version)
- **Hooks System**: Pre/post question and render hooks for template customization

### Template Integration Flow

1. Templates register via Python entry points in `setup.py`:
   ```python
   entry_points={
       'mrbob_templates': [
           'plone_addon = bobtemplates.plone.bobregistry:plone_addon',
           'plone_content_type = bobtemplates.plone.bobregistry:plone_content_type',
       ],
   }
   ```

2. Each entry point returns a `RegEntry` object with:
   - `template`: actual mr.bob template path
   - `plonecli_alias`: CLI-friendly name  
   - `depend_on`: parent template (None for standalone, 'plone_addon' for subtemplates)
   - `deprecated`: deprecation flag
   - `info`: additional information

3. Registry builds hierarchical template map and filters based on current context

## Common Development Commands

### Setup Development Environment
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e .[dev,test]
```

### Running Tests
```bash
# Run all tests
tox

# Run tests for specific Python version
tox -e py39

# Run tests directly with pytest
py.test tests/

# Run specific test
py.test tests/ -k test_get_package_root
```

### Code Quality
```bash
# Run linting
tox -e lint-py39

# Apply import sorting
tox -e isort-apply

# Apply code formatting
tox -e autopep8
```

### Testing Template Changes
When modifying template discovery or registry behavior, test with:
```bash
# List available templates
plonecli -l

# Test template creation in tmp directory
cd tmp/
plonecli create addon test.package
cd test.package
plonecli add content_type
```

## Configuration Files

- `setup.py`: Dependencies include `mr.bob` and `bobtemplates.plone>=7.0.0a2`
- `tox.ini`: Comprehensive testing across Python 3.7-3.10 with coverage reporting
- `setup.cfg`: flake8, isort, and metadata configuration
- `.mrbob.ini`: mr.bob template configuration for the configure_mrbob command

## Context-Aware Behavior

The CLI behaves differently based on current directory:

- **Global Context**: Only `create` and `config` commands available
- **Package Context**: All commands available except `create` (detected via `bobtemplate.cfg`)

This is implemented in `ClickFilteredAliasedGroup.list_commands()` using `reg.root_folder` detection.