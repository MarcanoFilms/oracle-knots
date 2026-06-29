# Oracle Knots GUI Testing Plan

**Phase 3.1: Testing & QA**  
**Target Coverage**: ≥75% for gui.py  
**Target Quality**: Zero critical bugs before public release

---

## 1. Unit Testing Strategy

### Target: ≥75% coverage for `gui.py`

#### Current State
- Existing: `test/test_dashboard_api.py` (~40-50% coverage)
- Missing: Coverage for wallet operations, config validation, PSBT flows

#### Test Categories

**1.1 Dashboard API Tests** (Existing - Enhance)
```python
# test/test_dashboard_api.py - Expand existing tests
- test_get_blockchain_info()
- test_get_network_info()
- test_get_mempool_info()
- test_policy_rejection_parsing()
- test_prometheus_metrics_aggregation()
- test_node_status_calculation()
```

**1.2 Wallet API Tests** (New)
```python
# test/test_wallet_api.py - New file
- test_create_wallet()
- test_load_wallet()
- test_generate_address()
- test_send_transaction()
- test_list_utxos()
- test_lock_unlock_utxos()
- test_psbt_decode()
- test_psbt_sign()
- test_wallet_balance_calculation()
- test_transaction_filtering()
```

**1.3 Configuration API Tests** (New)
```python
# test/test_config_api.py - New file
- test_parse_bitcoin_conf()
- test_validate_config_conflicts()
- test_policy_toml_parsing()
- test_set_config_option()
- test_config_validation_errors()
- test_merge_configs()
```

**1.4 Security Tests** (New)
```python
# test/test_security_validation.py - New file
- test_input_validation_wallet_name()
- test_input_validation_address()
- test_input_validation_amount()
- test_input_validation_label()
- test_rate_limiting()
- test_rpc_command_validation()
```

**1.5 Integration Tests with GUI** (New)
```python
# test/test_gui_integration.py - New file
- test_dashboard_data_fetch()
- test_wallet_creation_flow()
- test_transaction_send_flow()
- test_config_update_flow()
- test_policy_change_flow()
```

#### Testing Framework
- **Tool**: pytest (Python testing framework)
- **Command**: `pytest test/ -v --cov=gui --cov-report=html`
- **Target**: Run before each commit

#### Test Execution
```bash
# Run all tests with coverage
pytest test/ -v --cov=gui --cov-report=html

# Run specific test file
pytest test/test_wallet_api.py -v

# Run with coverage threshold
pytest test/ --cov=gui --cov-fail-under=75
```

---

## 2. Integration Testing Strategy

### Target: Test main workflows with actual bitcoind

#### Integration Test Setup
1. **Regtest bitcoind instance**
   - Lightweight, local-only Bitcoin network
   - No network dependency
   - Instant block generation

2. **Test Environment**
   ```bash
   # Start regtest bitcoind for testing
   bitcoind -regtest -daemon -rest
   
   # Generate test blocks
   bitcoin-cli -regtest generatetoaddress 101 bcrt1q...
   
   # Create test wallet
   bitcoin-cli -regtest createwallet test_wallet
   ```

#### Integration Test Scenarios

**2.1 Blockchain Operations**
```python
# test/functional/feature_gui_blockchain.py
- test_blockchain_sync_tracking()
- test_get_best_blockhash()
- test_get_block_height()
- test_get_transaction_info()
- test_mempool_updates()
```

**2.2 Wallet Operations**
```python
# test/functional/feature_gui_wallet.py
- test_wallet_creation_and_loading()
- test_address_generation_and_derivation()
- test_coin_selection_and_sending()
- test_transaction_confirmation_tracking()
- test_fee_estimation_accuracy()
```

**2.3 Policy Engine Integration**
```python
# test/functional/feature_gui_policy.py
- test_policy_profile_switching()
- test_rejection_tracking()
- test_template_filtering()
- test_mempool_audit_accuracy()
```

**2.4 RPC Integration**
```python
# test/functional/feature_gui_rpc.py
- test_rpc_call_execution()
- test_rpc_error_handling()
- test_concurrent_rpc_requests()
- test_rpc_timeout_handling()
```

#### Test Execution
```bash
# Run functional tests
./test/functional/test_runner.py --suite gui

# Run specific functional test
./test/functional/test_runner.py feature_gui_wallet.py

# Run with logging
./test/functional/test_runner.py --suite gui --loglevel=debug
```

---

## 3. Visual Regression Testing Strategy

### Target: Prevent unintended UI changes

#### Baseline Setup
1. **Create visual baselines**
   - Screenshot each major screen at standard resolution (1440x900)
   - Store in `test/visual-baselines/`
   - Create baselines for: Dashboard, Wallet, Config, Policy, Peers, CLI, Logs

2. **Manual Visual Testing**
   ```
   test/visual-baselines/
   ├── dashboard.png
   ├── wallet-receive.png
   ├── wallet-send.png
   ├── wallet-utxos.png
   ├── config-storage.png
   ├── config-network.png
   ├── policy-selector.png
   ├── peers-list.png
   ├── cli-terminal.png
   └── logs-viewer.png
   ```

#### Regression Testing Process
1. Make CSS/HTML changes
2. Screenshot affected screens
3. Compare with baseline
4. Document any intentional changes
5. Update baselines if changes are approved

#### Automated Visual Testing (Optional)
```python
# test/e2e/visual-regression.py - Optional Playwright-based testing
- test_dashboard_layout_unchanged()
- test_wallet_card_styling_consistent()
- test_form_spacing_uniform()
- test_responsive_layout_valid_at_breakpoints()
```

---

## 4. Manual Testing Checklist

### Comprehensive Manual QA

#### 4.1 Dashboard Tab
```
[ ] Node status displays correctly
[ ] Blockchain sync progress updates in real-time
[ ] Policy profile shows current selection
[ ] BIP-110 status badge displays
[ ] Peer count reflects actual connections
[ ] Rejection stats update when transactions rejected
[ ] Mining template info displays correctly
[ ] Recent blocks strip shows recent blocks
[ ] All cards responsive on mobile/tablet/desktop
[ ] Color coding clear and accessible
```

#### 4.2 Wallet Manager Tab
```
[ ] No Wallet view displays when wallet not loaded
[ ] Create Wallet flow works
[ ] Load Wallet flow works
[ ] Wallet selector dropdown functional
[ ] Balance displays correctly in BTC and USD
[ ] Receive address generation works
[ ] QR code generates and displays
[ ] Copy address button copies to clipboard
[ ] Simple send creates valid transaction
[ ] Coin control UTXO selection works
[ ] UTXO status colors correct (spendable/locked/unconfirmed)
[ ] Transaction history loads and filters work
[ ] Address list displays with labels
[ ] PSBT decode/sign flow works
[ ] Wallet backup/encrypt works
```

#### 4.3 Policy Engine Tab
```
[ ] Policy profile selector works
[ ] Custom rules display
[ ] Rejection stats show real data
[ ] Profile descriptions accurate
[ ] BIP-110 status displays
[ ] Lock-in progress shows correctly
[ ] Mempool audit runs without errors
[ ] Results display correctly
```

#### 4.4 Configuration Tab
```
[ ] All sub-tabs accessible
[ ] Storage settings save correctly
[ ] Network settings functional
[ ] Policy rules editable
[ ] Form validation works (conflicts detected)
[ ] Toggle switches work
[ ] Dropdowns functional
[ ] Save button saves all changes
[ ] Error messages clear and helpful
[ ] Settings persist after reload
```

#### 4.5 Responsive Design Testing
```
Mobile (375px):
[ ] No horizontal scrolling
[ ] All buttons tappable (≥44px)
[ ] Text readable
[ ] Forms full-width
[ ] Navigation accessible

Tablet (768px):
[ ] 2-column layout where applicable
[ ] Sidebar narrower but visible
[ ] Spacing balanced
[ ] All features accessible

Desktop (1440px):
[ ] 3+ column layouts work
[ ] Sidebar at full width
[ ] Hover effects visible
[ ] All features easily accessible

Large (1920px):
[ ] Extra spacing used
[ ] Layouts don't feel cramped
[ ] Text readable at distance
```

#### 4.6 Accessibility Testing
```
Keyboard Navigation:
[ ] Tab through all interactive elements
[ ] Enter activates buttons
[ ] Space activates checkboxes
[ ] Arrow keys work in dropdowns
[ ] Escape closes modals
[ ] Focus ring visible everywhere

Color & Contrast:
[ ] Status indicators readable
[ ] Text has sufficient contrast
[ ] Color not sole method of communication
[ ] Colorblind mode considerations

Screen Reader:
[ ] Labels associated with inputs
[ ] Button text descriptive
[ ] Icons have alt text
[ ] Form errors announced
[ ] Status changes announced
```

#### 4.7 Performance Testing
```
[ ] Dashboard loads in <1s
[ ] Wallet loads in <1s
[ ] API responses <500ms average
[ ] No lag during scrolling
[ ] Animations smooth at 60fps
[ ] No memory leaks after 30 min use
[ ] Battery drain acceptable on mobile
```

#### 4.8 Cross-Browser Testing
```
Chrome:
[ ] All features work
[ ] Styling correct
[ ] Performance good

Firefox:
[ ] All features work
[ ] Styling correct
[ ] Performance good

Safari:
[ ] All features work
[ ] Styling correct
[ ] Performance good

Edge:
[ ] All features work
[ ] Styling correct
[ ] Performance good

Mobile (iOS Safari, Chrome):
[ ] Touch interaction works
[ ] Responsive layout correct
[ ] Performance acceptable
```

---

## 5. Testing Timeline

### Week 9-10: Unit & Integration Tests
- **Days 1-2**: Set up test framework and create unit test files
- **Days 3-5**: Write and execute dashboard API tests
- **Days 6-7**: Write and execute wallet API tests
- **Days 8-9**: Write and execute config API tests
- **Days 10**: Security validation tests
- **Days 11-12**: Integration tests
- **Days 13-14**: Fix bugs found during testing

### Week 10-11: Visual & Manual Testing
- **Days 1-3**: Create visual baselines for all screens
- **Days 4-7**: Manual QA on multiple platforms
- **Days 8-10**: Responsive design testing
- **Days 11-14**: Cross-browser testing

### Week 12: Final QA
- **Days 1-3**: Performance optimization and testing
- **Days 4-5**: Security vulnerability assessment
- **Days 6-7**: Final manual smoke tests

---

## 6. Test Success Criteria

### Must Pass
- ✅ ≥75% code coverage for gui.py
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Zero critical bugs
- ✅ Dashboard <1s load time
- ✅ API responses <500ms average
- ✅ WCAG AA accessibility compliance
- ✅ Mobile responsive without horizontal scroll
- ✅ No console errors

### Should Pass
- ✅ ≥80% code coverage
- ✅ Lighthouse score ≥85 on desktop
- ✅ <2s initial page load (including assets)
- ✅ Mobile Lighthouse score ≥75
- ✅ No memory leaks after 1hr use
- ✅ All cross-browser tests pass

---

## 7. Test Environment Setup

### Dependencies
```bash
# Python testing
pip install pytest pytest-cov pytest-timeout

# Coverage reporting
pip install coverage

# Optional: Browser automation (visual regression)
pip install playwright
playwright install
```

### Test Configuration
```ini
# pytest.ini
[pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take >5s
    gui: GUI-specific tests
```

---

## 8. Continuous Integration Setup

### Pre-commit Checks
```bash
# Run before allowing commit
pytest test/unit -v --tb=short
```

### Pre-push Checks
```bash
# Run before allowing push
pytest test/ -v --cov=gui --cov-fail-under=75
```

### CI/CD Pipeline
```yaml
# GitHub Actions or similar
- Run unit tests
- Run integration tests  
- Check coverage (≥75%)
- Run linting
- Generate coverage report
```

---

## 9. Bug Tracking Template

### Issue Template
```
Title: [BUG] Dashboard sync percentage not updating

Environment:
- Browser: Chrome 126
- OS: macOS 14.5
- Node version: 29.3.0

Steps to Reproduce:
1. Open Dashboard
2. Wait for sync to progress
3. Observe sync percentage

Expected: Percentage updates every 2 seconds
Actual: Percentage frozen

Severity: Medium
Component: Dashboard
```

---

## 10. Documentation of Test Results

### Test Report Template
```
## Test Run Report - [Date]

**Summary**
- Total Tests: 150
- Passed: 145
- Failed: 5
- Skipped: 0
- Coverage: 76%

**Failures**
1. test_wallet_send_insufficient_funds - Fixed
2. test_config_validation_conflict - Fixed
3. test_psbt_signing_timeout - Investigation needed
...

**Recommendations**
- Address PSBT timeout issue
- Increase test coverage for wallet operations
- Add stress testing for concurrent RPC calls
```

---

**Ready to Execute**: All testing infrastructure documented and ready for implementation.
