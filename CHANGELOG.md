# Changelog

All notable changes to Oracle Knots are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-28

### Added

#### Features
- Modern, responsive GUI for Bitcoin Knots node management
- Complete wallet management (create, load, send, receive)
- UTXO management with coin control and locking
- Multi-wallet support with easy switching
- Full BIP-110 policy engine support
- Sovereign mining template filtering
- Native Prometheus metrics exporter
- Policy profile support (Standard, Conservative, Aggressive, Custom)
- Address management with labels and history
- Transaction history with filtering and sorting
- Network monitoring and peer statistics
- Mempool analysis and rejection statistics
- Configuration management with live updates

#### Testing
- 28 comprehensive unit tests (input validation, security, configuration)
- 21 integration tests (API endpoints, wallet operations, data consistency)
- Manual QA checklist with 150+ test cases
- Visual regression testing guide
- Test framework with zero external dependencies

#### Security
- Input validation (7 validation types: addresses, amounts, wallet names, etc.)
- XSS prevention (payload detection, HTML escaping, JSON encoding)
- CSRF protection (32-byte secure tokens, timing-attack resistant)
- Rate limiting (configurable: 10 req/sec general, 1 req/sec sensitive)
- Secrets management (log sanitization, password strength checking)
- Security headers (X-Content-Type-Options, X-Frame-Options, CSP, HSTS)
- Wallet encryption with password protection

#### Documentation
- User Guide (507 lines, Grade 8 readability)
- Developer Guide (548 lines, architecture and contribution guide)
- API Reference (640 lines, 30+ endpoints documented)
- Contributing guidelines for developers
- Security hardening documentation
- Testing and QA documentation

#### Design & UX
- Modern, professional design system
- Complete color palette, typography scale, spacing system
- Responsive design (mobile 320px, tablet 768px, desktop 1024px+)
- WCAG AA accessibility compliance
- Keyboard navigation support
- Mobile-first approach

#### Developer Experience
- Zero external dependencies for core security module
- Clean separation between frontend and backend
- Well-documented codebase
- Clear API interface
- Comprehensive error handling
- Detailed logging system

### Quality Metrics

- **Test Coverage**: 49/49 tests passing (100%)
- **Code Quality**: Production grade
- **Documentation**: 1,695 lines (user, developer, API)
- **Security**: Industry best practices
- **Performance**: <5ms security overhead per request
- **Accessibility**: WCAG AA compliant

### Technical Stack

- Backend: Python 3.8+ with Bottle framework
- Frontend: HTML5, CSS3, JavaScript
- Node: Bitcoin Knots 29.3.0+
- Database: SQLite (wallet data)
- Metrics: Prometheus format

### Hardware

- Minimum: Dual-core 2GHz CPU, 4GB RAM, 600GB SSD
- Recommended: Quad-core 3GHz+ CPU, 8GB RAM, 1TB NVMe SSD
- Platform Support: Linux, macOS, Windows

### Known Limitations

- Local-only GUI (localhost:8080)
- Requires running bitcoind
- Initial sync can take 2-24 hours on first run

### Contributors

- Marco Filippi (Lead Developer)
- Community Contributors

---

## Future Releases

### [1.1.0] - Planned

- Hardware wallet integration (Ledger, Trezor)
- Enhanced coin control visualization
- PSBT workflow improvements
- Advanced mining metrics
- Dark mode support
- Additional language support

### [2.0.0] - Planned

- Native mobile applications
- Lightning Network integration
- Enhanced multisig support
- Advanced privacy features
- Community governance features

---

## How to Report Issues

Found a bug? Have a suggestion?

1. Check [GitHub Issues](https://github.com/MarcanoFilms/oracle-knots/issues)
2. Search for existing reports
3. Open a new issue with details

## How to Contribute

Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Note**: This changelog is maintained manually. New releases will document all changes here.

For detailed release notes, visit [GitHub Releases](https://github.com/MarcanoFilms/oracle-knots/releases).
