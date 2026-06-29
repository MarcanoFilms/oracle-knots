# Contributing to Oracle Knots

Thank you for your interest in contributing! We welcome contributions to both the Bitcoin Knots backend (C++) and the Oracle Knots GUI (Python, JavaScript, CSS).

## Code of Conduct

We prioritize:
- Professional and respectful interactions
- Technical excellence
- Protection of consensus rules
- Clear, well-documented code

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/oracle-knots.git
cd oracle-knots

# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
pytest test/ -v

# Commit and push
git commit -m "feat: description"
git push origin feature/my-feature
```

## Contribution Types

### GUI Contributions (Python, JavaScript, CSS)

**File locations:**
- Backend: `gui.py`, `security.py`, `security_middleware.py`
- Frontend: `gui/index.html`, `gui/app.js`, `gui/*.css`
- Tests: `test/test_*.py`

**Coding style:**
- **Python**: PEP 8 (4-space indentation, type hints)
- **JavaScript**: Google Style Guide (2-space, camelCase)
- **CSS**: BEM naming, design tokens

**Process:**
1. Fork the repository
2. Create feature branch (`feature/` prefix)
3. Make focused, well-tested changes
4. Run tests: `pytest test/ -v`
5. Submit PR with description

### Core Contributions (C++ - Bitcoin Knots)

**File locations:**
- Validation: `src/validation.cpp`, `src/consensus/`
- Network: `src/net.cpp`, `src/net_processing.cpp`
- Mining: `src/blocktemplate.cpp`

**Important:**
- Changes to consensus code require extensive peer review
- Test in regtest and signet before submission
- Follow Bitcoin Core C++ style guide
- Use `clang-format` before committing

## Testing Requirements

### Automated Tests

```bash
# GUI tests
python3 test/test_validators.py
python3 test/test_gui_integration.py

# All tests
pytest test/ -v --cov=.
```

**Target:** ≥75% code coverage

### Manual Testing

**For GUI changes:**
- Test on desktop, tablet, mobile
- Test on Chrome, Firefox, Safari
- Keyboard navigation
- Accessibility

**For core changes:**
- Regtest: `make test-regtest`
- Signet: Run on signet network
- Performance: Profile before/after

## Code Style

### Python Example

```python
def validate_bitcoin_address(address: str) -> Tuple[bool, str]:
    """Validate Bitcoin address format.
    
    Supports Bech32, P2PKH, P2SH.
    """
    if not isinstance(address, str):
        return False, "Address must be a string"
    # ... implementation
    return True, ""
```

### JavaScript Example

```javascript
function switchTab(tabId) {
  const tab = document.getElementById(tabId);
  if (!tab) {
    console.error(`Tab ${tabId} not found`);
    return;
  }
  // ... implementation
}
```

### CSS Example

```css
.button {
  padding: var(--spacing-2);
}

.button--primary {
  background-color: var(--color-primary);
}

.button__icon {
  margin-right: var(--spacing-1);
}
```

## Commit Messages

```
feat: add Bech32 address validation

Support for native Segwit (bc1) addresses
in addition to P2PKH and P2SH formats.

Fixes #42
```

**Types:** feat, fix, docs, test, refactor, perf, security, chore

## Pull Request Process

1. **Create PR** with clear title and description
2. **Link issues** with `Fixes #123`
3. **Include testing** details
4. **Add screenshots** for UI changes
5. **Respond to reviews** promptly
6. **Update documentation** if needed

## Developer Resources

- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - Setup and architecture
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - Features and usage
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - API endpoints
- **[SECURITY.md](SECURITY.md)** - Security guidelines

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/MarcanoFilms/oracle-knots/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarcanoFilms/oracle-knots/discussions)
- **Documentation**: [docs/](docs/) folder

## Recognition

Contributors are acknowledged in:
- `CHANGELOG.md`
- GitHub Contributors page
- Project documentation
