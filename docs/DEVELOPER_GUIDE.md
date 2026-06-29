# Oracle Knots Developer Guide

**Version**: 1.0  
**For**: Developers who want to understand, modify, or contribute to Oracle Knots

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Development Setup](#development-setup)
4. [Codebase Structure](#codebase-structure)
5. [Key Components](#key-components)
6. [Building](#building)
7. [Testing](#testing)
8. [Contributing](#contributing)
9. [Debugging](#debugging)

---

## Project Overview

**Oracle Knots** is a modern Bitcoin node GUI built on Bitcoin Knots with a focus on user accessibility and sovereignty.

### Technology Stack

- **Backend**: Python 3 (Bottle framework)
- **Frontend**: HTML5, CSS3, JavaScript
- **Node**: Bitcoin Knots (C++)
- **GUI Runtime**: pywebview

### Design Philosophy

- **User-First**: Every feature designed for non-technical users
- **Accessibility**: WCAG AA compliance, keyboard navigation
- **Security**: Input validation, CSRF protection, rate limiting
- **Modularity**: Clean separation between GUI and node
- **Open Source**: MIT/Apache license, community contributions welcome

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────┐
│     Oracle Knots GUI            │
│  (HTML/CSS/JavaScript Frontend) │
└────────────┬────────────────────┘
             │
        HTTP/JSON API
             │
┌────────────▼────────────────────┐
│   Python Backend (gui.py)        │
│   • Route handling               │
│   • Bitcoin RPC communication    │
│   • Data processing              │
└────────────┬────────────────────┘
             │
        JSON-RPC API
             │
┌────────────▼────────────────────┐
│   bitcoind/bitcoin-cli           │
│   (Bitcoin Knots Node)           │
└─────────────────────────────────┘
             │
        P2P Network
             │
┌────────────▼────────────────────┐
│   Bitcoin Network Peers          │
└─────────────────────────────────┘
```

### Data Flow

**Reading blockchain info:**
1. Frontend requests `/api/blockchain` via HTTP
2. Python backend fetches data from bitcoind RPC
3. Data is processed and formatted
4. JSON response sent back to frontend
5. Frontend updates UI

**Sending a transaction:**
1. Frontend validates input (address, amount)
2. User confirms transaction
3. POST to `/api/wallet/send` with CSRF token
4. Backend validates input (server-side)
5. Bitcoin RPC command executed
6. Transaction broadcast to network
7. Response with txid sent to frontend

### Security Layers

1. **Frontend Validation**: Immediate user feedback
2. **Server Validation**: Prevent invalid requests from reaching bitcoind
3. **CSRF Protection**: Prevent unauthorized state changes
4. **Rate Limiting**: Prevent abuse and DoS
5. **Input Sanitization**: Prevent XSS and injection attacks
6. **Secrets Management**: Never log sensitive data

---

## Development Setup

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get install \
  build-essential \
  autoconf \
  automake \
  libtool \
  git \
  python3 \
  python3-dev \
  python3-pip

# macOS
brew install \
  autoconf \
  automake \
  libtool \
  python@3.11
```

### Clone and Build

```bash
# Clone repository
git clone https://github.com/MarcanoFilms/oracle-knots.git
cd oracle-knots

# Build Bitcoin Knots
./autogen.sh
./configure --prefix=$(pwd)/install
make -j$(nproc)
make install

# Install Python dependencies
pip install bottle pywebview

# Run development server
python3 gui.py
```

### Development Environment

**Recommended Tools:**
- **IDE**: VS Code with Python extension
- **Debugger**: Python pdb or IDE debugger
- **Linter**: pylint or flake8
- **Formatter**: black

**Git Workflow:**
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add feature: description"

# Push and create pull request
git push origin feature/my-feature
```

---

## Codebase Structure

```
oracle-knots/
├── gui/                          # Frontend files
│   ├── index.html               # Main HTML
│   ├── style.css                # Original styles
│   ├── design-tokens.css        # Design system tokens
│   ├── utilities.css            # Reusable utility classes
│   ├── responsive.css           # Responsive design
│   ├── wallet-ux.css            # Wallet-specific styles
│   ├── config-ux.css            # Config-specific styles
│   ├── onboarding-ux.css        # Onboarding styles
│   ├── navigation-ux.css        # Navigation styles
│   ├── app.js                   # Main JavaScript
│   └── help/                    # Markdown help guides
│
├── gui.py                       # Main Python backend
├── security.py                  # Security/validation functions
├── security_middleware.py       # Bottle middleware
│
├── test/                        # Testing
│   ├── test_validators.py       # Input validation tests (28 tests)
│   ├── test_gui_integration.py  # Integration tests (21 tests)
│   ├── TEST_PLAN.md             # Testing documentation
│   ├── MANUAL_QA_CHECKLIST.md   # QA checklist
│   └── simple_test_runner.py    # Standalone test runner
│
├── docs/                        # Documentation
│   ├── USER_GUIDE.md            # User documentation
│   ├── DEVELOPER_GUIDE.md       # Developer documentation
│   └── API_REFERENCE.md         # API documentation
│
└── build/                       # Built Bitcoin Knots binaries
    └── bin/
        ├── bitcoind             # Bitcoin node
        └── bitcoin-cli          # Bitcoin CLI
```

---

## Key Components

### gui.py (Main Backend)

**Purpose**: HTTP server, RPC communication, business logic

**Key Functions:**
- `route()` decorators for API endpoints
- `run_bitcoin_cli()` - Execute RPC commands
- `check_node_running()` - Node status
- `_summarize_peers()` - Format peer data
- `_top_rejections()` - Filter rejection stats

**Main Routes:**
- `GET /api/blockchain` - Blockchain info
- `GET /api/network` - Network status
- `POST /api/wallet/send` - Send transaction
- `GET /api/dashboard` - Dashboard data

### security.py (Validation & Protection)

**Purpose**: Input validation, XSS prevention, CSRF tokens, rate limiting

**Key Classes:**
- `InputValidator` - Validate wallet names, addresses, amounts
- `XSSPrevention` - Detect and prevent XSS
- `CSRFProtection` - Generate and validate tokens
- `RateLimiter` - Enforce request limits
- `SecretsManager` - Protect sensitive data

### app.js (Frontend Logic)

**Purpose**: UI interaction, API communication, data updates

**Key Functions:**
- `switchTab(tabId)` - Tab navigation
- Fetch API calls to backend
- DOM manipulation and updates
- Event listener setup

### CSS System

**Design tokens** (`design-tokens.css`)
- Color palette (12 colors)
- Typography scale (7 sizes)
- Spacing scale (8px multiples)
- Effects (shadows, transitions)

**Utilities** (`utilities.css`)
- Button classes
- Form classes
- Layout classes (flexbox, grid)
- Text classes

**Responsive** (`responsive.css`)
- Mobile (320px)
- Tablet (768px)
- Desktop (1024px)
- Large (1920px)

---

## Building

### Full Build

```bash
./autogen.sh
./configure
make -j$(nproc)
```

### Incremental Build

```bash
make -j$(nproc)
```

### Build Options

```bash
# Build without GUI
./configure --without-gui

# Build with specific features
./configure --enable-wallet --enable-zmq

# Custom install path
./configure --prefix=/opt/oracle-knots
```

### Verifying Build

```bash
# Check bitcoind
./build/bin/bitcoind --version

# Check bitcoin-cli
./build/bin/bitcoin-cli --version

# Start GUI
python3 gui.py
```

---

## Testing

### Unit Tests (49 tests passing)

```bash
# Run all unit tests
python3 test/test_validators.py
python3 test/test_gui_integration.py

# Run with pytest (if installed)
pytest test/ -v
```

### Integration Tests

```bash
# Requires running bitcoind
python3 test/test_gui_integration.py
```

### Manual Testing

Use `MANUAL_QA_CHECKLIST.md` for comprehensive manual testing:
- Dashboard functionality
- Wallet operations
- Configuration changes
- Responsive design
- Accessibility

### Adding Tests

```python
# In test/test_something.py
class TestFeature:
    def test_case_1(self):
        """Test description"""
        assert expected == actual
    
    def test_case_2(self):
        """Another test"""
        assert result is True
```

---

## Contributing

### Fork & Branch

```bash
# Fork on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/oracle-knots.git

# Create feature branch
git checkout -b feature/description
```

### Code Style

- **Python**: PEP 8
- **JavaScript**: Google style guide
- **CSS**: BEM naming, semantic classes

### Commit Messages

```
Add feature: description

Clear, descriptive commit message explaining:
- What you changed
- Why you changed it
- How to verify it works
```

### Pull Request

```bash
# Push to your fork
git push origin feature/description

# Create PR on GitHub
# Fill out PR template
# Link any related issues
```

### PR Requirements

- ✅ Tests pass
- ✅ No breaking changes (or documented)
- ✅ Documentation updated
- ✅ Security reviewed
- ✅ Performance impact assessed

---

## Debugging

### Python Debugging

**Using pdb:**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**Using IDE debugger:**
- Set breakpoint in VS Code
- Press F5 to debug
- Step through code

### JavaScript Debugging

**Browser DevTools:**
1. Press F12 in browser
2. Go to Console or Network tab
3. Set breakpoints in Sources tab
4. Reload page to debug

### Logs

**Python logging:**
```python
import logging
logging.info("Debug message")
logging.error("Error message")
```

**Browser console:**
```javascript
console.log("Message");
console.error("Error");
```

### Network Debugging

Use browser DevTools Network tab to inspect:
- API requests
- Response times
- Status codes
- Request/response bodies

---

## Performance Profiling

### Python Profiling

```python
import cProfile
cProfile.run('function_name()')
```

### Frontend Performance

Use Chrome DevTools:
1. Open DevTools (F12)
2. Go to Performance tab
3. Click record
4. Perform action
5. Click stop
6. Analyze results

---

## Documentation

### Code Comments

Keep minimal - only explain WHY, not WHAT:
```python
# Constant-time comparison prevents timing attacks
result = 0
for x, y in zip(a, b):
    result |= ord(x) ^ ord(y)
```

### Function Documentation

```python
def validate_address(address: str) -> Tuple[bool, str]:
    """Validate Bitcoin address format.
    
    Supports Bech32, P2PKH, and P2SH formats.
    """
```

---

## Architecture Decision Records

When making significant decisions, document in ADR format:

```markdown
# ADR: Title

**Status**: Accepted/Proposed

**Context**: Why this decision was needed

**Decision**: What we decided to do

**Consequences**: What this affects

**Alternatives Considered**: Other options
```

---

## Glossary

- **bitcoind**: Bitcoin Knots node daemon
- **RPC**: JSON-RPC protocol for communicating with bitcoind
- **UTXO**: Unspent Transaction Output
- **PSBT**: Partially Signed Bitcoin Transaction
- **Mempool**: Memory pool of unconfirmed transactions
- **BIP-110**: Policy engine specification

---

## Further Resources

- [Bitcoin Core Documentation](https://bitcoin.org/en/developer-documentation)
- [Bitcoin Knots Repository](https://github.com/bitcoinknots/bitcoin)
- [Bitcoin Improvement Proposals](https://github.com/bitcoin/bips)
- [Learn Me a Bitcoin](https://learnmeabitcoin.com/)

---

**Last Updated**: June 28, 2026  
**Maintained By**: Oracle Knots Community
