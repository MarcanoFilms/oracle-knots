# Contributing to Oracle Knots

First, thank you for contributing to Oracle Knots! We aim to build a clean, high-quality, and robust platform for sovereign Bitcoin node operators.

## Code of Conduct
We prioritize professional and respectful interactions, technical excellence, and the protection of consensus rules.

## Coding Style
- Follow the C++ coding style used in Bitcoin Core / Bitcoin Knots.
- All code changes should be well-commented and documented.
- Run `clang-format` or standard formatters before committing.

## Development Workflow
1. **Fork the Repository:** Create a feature branch from the `main` branch.
2. **Implement Changes:** Keep pull requests focused on a single logical change or bugfix.
3. **Consensus Criticality:** Any changes touching `validation.cpp`, validation flags, or consensus parameters require extensive peer review. Do not attempt clever hacks on validation code.
4. **Testing:** Test your changes in **regtest** and **signet** before submitting. Include new unit tests or functional python tests under the `test/` directory.
5. **Open a PR:** Complete the PR template, detailing the testing performed.
