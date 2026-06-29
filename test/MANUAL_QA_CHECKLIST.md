# Oracle Knots GUI - Manual QA Checklist

**Date**: June 28, 2026  
**Tester**: [Your Name]  
**Hardware**: MacBook Pro Intel i5 2013, 8GB RAM  
**Browser**: Safari/Chrome  
**Test Duration**: ~2-3 hours for full checklist  

---

## Pre-Testing Setup

- [ ] bitcoind running: `ps aux | grep bitcoind`
- [ ] GUI server running: `python3 gui.py` or `pywebview`
- [ ] Access GUI at `http://127.0.0.1:8080`
- [ ] Browser developer tools open (F12)
- [ ] Console clear of errors
- [ ] Network tab ready to monitor

---

## 1. DASHBOARD TAB

### 1.1 Page Load
- [ ] Dashboard loads within 2 seconds
- [ ] All status cards visible
- [ ] No layout shifts after loading
- [ ] Console shows no errors
- [ ] Network tab shows all resources loaded (HTTP 200)

### 1.2 Status Display
- [ ] Node status dot visible (colored: green/yellow/red)
- [ ] Status text displays correctly
- [ ] Network badge shows (mainnet/testnet/signet/regtest)
- [ ] Block number shows and updates
- [ ] Peer count shows and is accurate
- [ ] Sync percentage shows (0-100%)

### 1.3 Statistics Cards
- [ ] 4 cards visible in grid layout
- [ ] Card spacing even (16px margins)
- [ ] Card content readable
- [ ] Colors match design system
- [ ] Card shadows visible/subtle

### 1.4 Interactive Elements
- [ ] Stop Node button present and clickable
- [ ] Save All Settings button present
- [ ] Links clickable without errors
- [ ] Hover effects visible (subtle)

### 1.5 Real-time Updates
- [ ] Block count updates when new blocks arrive
- [ ] Peer count reflects actual connections
- [ ] Memory usage shows accurate value
- [ ] No flickering or excessive redraws

---

## 2. WALLET MANAGER TAB

### 2.1 Tab Accessibility
- [ ] Tab loads when clicked
- [ ] Content appears without lag
- [ ] No console errors
- [ ] Back to other tabs works

### 2.2 Empty Wallet State (No Wallet Loaded)
- [ ] "No wallet loaded" message displays
- [ ] Create wallet button visible
- [ ] Load wallet button visible
- [ ] Wallet list dropdown accessible

### 2.3 Wallet Creation Flow
- [ ] Click "Create Wallet" opens form
- [ ] Wallet name input functional
- [ ] Name validation works (only alphanumeric, -, _)
- [ ] Create button saves wallet
- [ ] Success message appears
- [ ] Wallet switches to new one automatically

### 2.4 Wallet Display (When Loaded)
- [ ] Wallet name shows in header
- [ ] Wallet selector dropdown works
- [ ] Balance displays correctly
- [ ] Balance updates on transaction

### 2.5 Receive Tab
- [ ] Address input shows current address
- [ ] Address copyable to clipboard
- [ ] Copy button works (shows feedback)
- [ ] QR code displays
- [ ] QR code is scannable
- [ ] Generate new address button works
- [ ] Previous addresses listed

### 2.6 Send Tab - Simple Mode
- [ ] Recipient address input functional
- [ ] Amount input functional
- [ ] Fee slider present
- [ ] Fee rate displays (sat/vB)
- [ ] Preview shows expected fee
- [ ] Send button active when form valid
- [ ] Send button disabled when form invalid

### 2.7 Send Tab - Coin Control
- [ ] Coin control toggle switches view
- [ ] UTXO list displays
- [ ] UTXO status colors correct:
  - [ ] Green = spendable
  - [ ] Gray = locked
  - [ ] Yellow = unconfirmed
  - [ ] Orange = immature
- [ ] Select/deselect UTXOs works
- [ ] Selected amount updates
- [ ] Change address selector works

### 2.8 Transaction History
- [ ] Transaction list loads
- [ ] Transactions sortable by date/amount
- [ ] Status badges show (confirmed/pending/failed)
- [ ] Amounts display correctly
- [ ] Addresses show (truncated with ellipsis)
- [ ] Search/filter functional

### 2.9 Address Management
- [ ] Address list accessible
- [ ] Addresses show with balances
- [ ] Labels editable
- [ ] Add label form works
- [ ] Delete address option present

### 2.10 PSBT Workflow
- [ ] PSBT decode input accepts text/file
- [ ] Decoded PSBT displays structure
- [ ] Sign button present (grayed out when no wallet)
- [ ] Sign produces signed PSBT
- [ ] Finalize button works
- [ ] Broadcast button present

---

## 3. CONFIGURATION TAB

### 3.1 Tab Accessibility
- [ ] Configuration tab loads
- [ ] Sub-tabs visible (Storage, Network, etc.)
- [ ] First tab (Storage & Sync) active by default
- [ ] Tab switching smooth

### 3.2 Storage & Sync Settings
- [ ] Chain selector works (main/test/signet/regtest)
- [ ] Blocksonly toggle functional
- [ ] Pruning mode selector works
- [ ] Prune size input shows when custom selected
- [ ] Txindex toggle visible
- [ ] Addressindex toggle visible
- [ ] All inputs properly labeled

### 3.3 Network Settings
- [ ] Network type selector works
- [ ] Port fields accept valid numbers
- [ ] Tor proxy input functional
- [ ] I2P proxy input functional
- [ ] Listen address selector works
- [ ] Help text displays for each field

### 3.4 Policy Settings
- [ ] Policy profile selector works
- [ ] Custom policy fields editable
- [ ] Settings validate (no negative numbers)
- [ ] Conflict detection works (txindex + pruning)
- [ ] Error messages clear

### 3.5 Setup Wizard
- [ ] Wizard accessible (first run or button)
- [ ] Step 1: Network selection works
- [ ] Step 2: Storage settings works
- [ ] Step 3: Policy settings works
- [ ] Step 4: Review shows summary
- [ ] Back/Next buttons work
- [ ] Save button saves config

### 3.6 Form Validation
- [ ] Required fields cannot be empty
- [ ] Number fields reject non-numeric input
- [ ] Port range validation works (1024-65535)
- [ ] Conflicting settings show error
- [ ] Error messages clear and helpful

### 3.7 Settings Persistence
- [ ] Change setting, save
- [ ] Reload page
- [ ] Setting persists (not lost)

---

## 4. POLICY ENGINE TAB

### 4.1 Tab Accessibility
- [ ] Policy tab loads
- [ ] Content displays correctly
- [ ] No errors in console

### 4.2 Policy Profile Selector
- [ ] Profile dropdown works
- [ ] Profile options visible (standard/conservative/custom)
- [ ] Selecting profile updates display
- [ ] Profile description shows

### 4.3 Policy Settings Display
- [ ] Current policy settings show
- [ ] Status badges present
- [ ] BIP-110 status shows
- [ ] Lock-in progress displays

### 4.4 Policy Validation
- [ ] Rejection stats display
- [ ] Custom rules editable
- [ ] Save button works
- [ ] Settings persist

### 4.5 Mempool Audit
- [ ] Audit button clickable
- [ ] Audit runs (shows loading state)
- [ ] Results display after completion
- [ ] Results show rejection rate

---

## 5. BIP-110 MINING TAB

### 5.1 Tab Accessibility
- [ ] Mining tab loads
- [ ] Content displays
- [ ] No console errors

### 5.2 Mining Status
- [ ] Mining status shows (active/inactive)
- [ ] Hash rate displays (if mining)
- [ ] Shares submitted shows
- [ ] Pool info displays

### 5.3 Template Information
- [ ] Current template shows
- [ ] Template size displays
- [ ] Lock-in status shows
- [ ] Difficulty shows

---

## 6. PEERS TAB

### 6.1 Tab Accessibility
- [ ] Peers tab loads ✅ (verified fixed)
- [ ] Peer list displays
- [ ] No console errors

### 6.2 Peer Information
- [ ] Peer count badge shows
- [ ] Peers table visible
- [ ] Table columns: ID, Address, User Agent, Direction, Height, Ping
- [ ] Data populates correctly

### 6.3 Peer Details
- [ ] Addresses display (IP or onion)
- [ ] Direction shows (inbound/outbound)
- [ ] Block height shows
- [ ] Ping time shows
- [ ] Connection icons visible (if present)

### 6.4 Peer Filtering (if available)
- [ ] Search by address works
- [ ] Filter by direction works
- [ ] Sort by column works

---

## 7. CLI TERMINAL TAB

### 7.1 Tab Accessibility
- [ ] CLI tab loads
- [ ] Terminal interface displays
- [ ] No console errors

### 7.2 Command Input
- [ ] Command input field functional
- [ ] Previous commands accessible (up arrow)
- [ ] Commands execute (show output)
- [ ] Errors display clearly

### 7.3 Command Reference
- [ ] Help command works
- [ ] Command list displays
- [ ] Commands formatted properly
- [ ] Examples show when available

---

## 8. LOGS VIEWER TAB

### 8.1 Tab Accessibility
- [ ] Logs tab loads
- [ ] Log display area visible
- [ ] No console errors

### 8.2 Log Display
- [ ] Recent logs show
- [ ] Timestamps visible
- [ ] Log levels displayed (error/warning/info)
- [ ] Colors distinguish log levels

### 8.3 Log Filtering (if available)
- [ ] Filter by level works
- [ ] Search in logs works
- [ ] Clear logs button present

---

## 9. RESPONSIVE DESIGN TESTING

### 9.1 Mobile View (375px)
- [ ] Open DevTools (F12)
- [ ] Set viewport to 375x667 (iPhone)
- [ ] Sidebar hidden (hamburger menu visible)
- [ ] Content full width
- [ ] No horizontal scrolling
- [ ] Buttons tappable (≥44px)
- [ ] Form inputs readable
- [ ] Text not too small

### 9.2 Tablet View (768px)
- [ ] Set viewport to 768x1024
- [ ] Sidebar narrower
- [ ] Content columns adjusted
- [ ] Tables responsive
- [ ] Touch targets adequate

### 9.3 Desktop View (1440px)
- [ ] Default view
- [ ] 3-column layout where applicable
- [ ] Sidebar full width
- [ ] Spacing balanced
- [ ] Hover effects visible

### 9.4 Large Screen (1920px)
- [ ] Set viewport to 1920x1080
- [ ] Extra spacing used
- [ ] Content not too spread out
- [ ] Text readable at distance
- [ ] Layouts not cramped

### 9.5 Orientation Changes
- [ ] Rotate device (if mobile/tablet)
- [ ] Layout adapts
- [ ] Content still usable

---

## 10. ACCESSIBILITY TESTING

### 10.1 Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Focus ring visible (cyan outline)
- [ ] Skip link present (if applicable)
- [ ] Logical tab order

### 10.2 Form Keyboard Use
- [ ] Tab to all form fields
- [ ] Enter submits form
- [ ] Space toggles checkboxes
- [ ] Arrow keys work in dropdowns
- [ ] Escape closes modals

### 10.3 Color & Contrast
- [ ] Status colors clear
- [ ] Text contrast ≥4.5:1
- [ ] Color not sole indicator
- [ ] Error messages visible

### 10.4 Screen Reader Testing
- [ ] Labels associated with inputs
- [ ] Button text descriptive
- [ ] Form instructions clear
- [ ] Data tables have headers
- [ ] Images have alt text (if any)

---

## 11. PERFORMANCE TESTING

### 11.1 Load Times
- [ ] Dashboard loads in <1s
- [ ] Wallet loads in <1s
- [ ] Config loads in <1s
- [ ] No noticeable lag on tab switches

### 11.2 API Response Times
- [ ] Dashboard API <500ms
- [ ] Wallet API <500ms
- [ ] Config API <500ms
- [ ] All APIs responsive

### 11.3 Animations
- [ ] Smooth transitions (60fps if animated)
- [ ] No stuttering
- [ ] Animations not too slow

### 11.4 Resource Usage
- [ ] CPU usage reasonable (<50%)
- [ ] Memory usage stable (<500MB)
- [ ] No memory leaks over time
- [ ] Scrolling smooth

---

## 12. BROWSER COMPATIBILITY

### 12.1 Safari (macOS)
- [ ] All features work
- [ ] Styling correct
- [ ] Performance good
- [ ] No console errors

### 12.2 Chrome (if available)
- [ ] All features work
- [ ] Styling matches Safari
- [ ] Performance comparable

### 12.3 Firefox (if available)
- [ ] All features work
- [ ] Styling renders correctly

---

## 13. ERROR HANDLING

### 13.1 Network Errors
- [ ] Disconnect bitcoind
- [ ] GUI shows error gracefully
- [ ] Error message helpful
- [ ] Can retry operation

### 13.2 Invalid Input
- [ ] Enter invalid wallet name
- [ ] Enter invalid address
- [ ] Enter invalid amount
- [ ] Error messages appear
- [ ] Form doesn't submit

### 13.3 Rate Limiting
- [ ] Rapid-fire requests don't crash GUI
- [ ] Rate limit message appears (if applicable)
- [ ] Recovery is smooth

---

## 14. EDGE CASES

### 14.1 Empty States
- [ ] No wallet loaded: proper message
- [ ] No transactions: proper message
- [ ] No peers: proper message
- [ ] Empty address list: proper message

### 14.2 Boundary Values
- [ ] Maximum amount: handles correctly
- [ ] Minimum amount (1 satoshi): works
- [ ] Very long address: displays with truncation
- [ ] Very long label: truncates or wraps

### 14.3 Special Characters
- [ ] Labels with emojis: display correctly
- [ ] Addresses with special chars: display correctly
- [ ] Comments with quotes: don't break display

---

## 15. FEATURE INTERACTIONS

### 15.1 Wallet & Configuration
- [ ] Change network in config
- [ ] Wallet still loads correctly
- [ ] Transactions still display

### 15.2 Policy & Wallet
- [ ] Change policy settings
- [ ] Wallet still functional
- [ ] Existing transactions still valid

### 15.3 Multi-Tab Usage
- [ ] Open wallet, switch to config, back to wallet
- [ ] State preserved
- [ ] No data loss
- [ ] Smooth transitions

---

## NOTES & ISSUES FOUND

```
Date: _________________
Issue #1:
  Description: _________________________________
  Steps to Reproduce: __________________________
  Expected: ____________________________________
  Actual: _______________________________________
  Severity: (Critical/High/Medium/Low)
  
Issue #2:
  Description: _________________________________
  ...
```

---

## SIGN OFF

- [ ] All critical issues resolved
- [ ] All major issues resolved
- [ ] Minor issues documented
- [ ] Testing complete
- [ ] Ready for release

**Tester**: ____________________  
**Date**: ____________________  
**Notes**: ____________________

---

## QA Checklist Summary

**Total Checks**: ~150 items  
**Estimated Time**: 2-3 hours  
**Pass Rate Target**: 95%+

Use this checklist to ensure quality before each release.
