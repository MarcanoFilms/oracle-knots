# Visual Regression Testing Guide

**Purpose**: Detect unintended UI changes that could break the user experience

---

## Setup

### 1. Create Baseline Screenshots

Baselines are the "golden" screenshots that represent the correct UI state. They're taken once and then compared against future changes.

**Location**: `test/visual-baselines/`

**Files needed**:
```
test/visual-baselines/
├── dashboard.png           # Main dashboard view
├── wallet-receive.png      # Wallet receive tab
├── wallet-send-simple.png  # Simple send form
├── wallet-send-advanced.png # Coin control send
├── wallet-addresses.png    # Address list
├── wallet-transactions.png # Transaction history
├── config-storage.png      # Storage & sync settings
├── config-network.png      # P2P network settings
├── config-policy.png       # Policy settings
├── config-wizard.png       # Setup wizard
├── policy-selector.png     # Policy profile selector
├── mining-status.png       # Mining/BIP-110 status
├── peers-list.png          # Connected peers
├── cli-terminal.png        # CLI command interface
└── logs-viewer.png         # Log viewer
```

---

## Creating Baselines

### Step 1: Screenshot Capture

On your development machine (MacBook Pro):

1. Open Oracle Knots GUI at `http://127.0.0.1:8080`
2. Navigate to each screen
3. Wait 2 seconds for content to load
4. Take full-window screenshot (1440x900 recommended)
5. Save to `test/visual-baselines/` with descriptive name

### Step 2: Document the Process

```bash
# Create baseline directory
mkdir -p test/visual-baselines

# Screenshot each screen (manual process)
# 1. Dashboard
# 2. Wallet Manager (Receive)
# 3. Wallet Manager (Send - Simple)
# 4. Wallet Manager (Send - Advanced)
# 5. Address Management
# 6. Transaction History
# 7. Configuration (Storage)
# 8. Configuration (Network)
# 9. Configuration (Policy)
# 10. Setup Wizard
# 11. Policy Selector
# 12. Mining Status
# 13. Peers List
# 14. CLI Terminal
# 15. Logs Viewer
```

---

## Visual Regression Testing Process

### After Making CSS/HTML Changes:

1. **Run functional tests** to ensure logic still works
2. **Take updated screenshots** of affected screens
3. **Compare with baselines**:
   - Check for unintended layout shifts
   - Verify spacing and alignment
   - Check color/contrast consistency
   - Confirm responsive behavior

4. **Document changes**:
   - If changes are intentional, update baselines
   - If changes are unintended, fix the code

5. **Update baselines** (if approved):
   ```bash
   # Replace old baseline with new version
   cp new-screenshot.png test/visual-baselines/dashboard.png
   git add test/visual-baselines/
   git commit -m "Update visual baseline: dashboard after layout fix"
   ```

---

## Automated Visual Regression (Optional)

For more advanced visual regression testing, you can use tools like:

### Option 1: Playwright (Python)
```python
# test/e2e/visual_regression.py
from playwright.sync_api import sync_playwright

def test_dashboard_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8080")
        page.screenshot(path="dashboard_current.png")
        
        # Compare with baseline
        # assert visual_diff < threshold
```

### Option 2: Cypress + Visual Testing
```javascript
// test/e2e/visual-tests.js
describe('Visual Regression Tests', () => {
  it('dashboard should match baseline', () => {
    cy.visit('http://127.0.0.1:8080')
    cy.matchImageSnapshot('dashboard')
  })
})
```

---

## Manual Visual Regression Checklist

For each screen, verify:

### Dashboard Tab
- [ ] Header layout correct (title, status, buttons aligned)
- [ ] Status cards display properly (4-column grid)
- [ ] Colors match design system (backgrounds, text, badges)
- [ ] Spacing consistent (16px between cards, 8px padding)
- [ ] Charts render correctly if present
- [ ] Responsive: mobile view stacks properly

### Wallet Tabs
- [ ] Receive address displays fully
- [ ] QR code is centered and sized correctly
- [ ] Send form layout looks good
- [ ] Input fields have proper spacing
- [ ] Buttons are properly aligned
- [ ] Error/success messages appear in correct location
- [ ] Table columns aligned properly

### Configuration Tab
- [ ] Sub-tabs visible and properly spaced
- [ ] Form fields aligned vertically
- [ ] Labels above inputs (not beside)
- [ ] Help text displays properly
- [ ] Toggle switches render correctly
- [ ] Dropdowns display properly
- [ ] Settings groups separated clearly

### Responsive Design
- [ ] Mobile (375px): No horizontal scroll, text readable
- [ ] Tablet (768px): 2-column layout works
- [ ] Desktop (1440px): 3-column layout works
- [ ] Large screen (1920px): Content not too spread out

---

## Comparison Techniques

### Manual Comparison
1. Open baseline in one window
2. Open current screenshot in another
3. Compare side-by-side
4. Document any differences

### Diff Tools
```bash
# Using ImageMagick to compare images
compare test/visual-baselines/dashboard.png dashboard_current.png dashboard_diff.png

# Using open-cv for pixel difference
python3 test/compare_images.py baseline.png current.png
```

---

## Fixing Visual Regressions

### If you find an unintended change:

1. **Identify the CSS rule** that caused the change
2. **Fix the CSS**
3. **Take new screenshot**
4. **Verify fix**
5. **Commit changes**:
   ```bash
   git add gui/style.css test/visual-baselines/dashboard.png
   git commit -m "Fix dashboard spacing - reduce padding from 20px to 16px"
   ```

### If it's an intended improvement:

1. **Verify it looks better**
2. **Check it's consistent with design system**
3. **Update baseline**:
   ```bash
   cp dashboard_new.png test/visual-baselines/dashboard.png
   git add test/visual-baselines/dashboard.png
   git commit -m "Improve dashboard layout - better visual hierarchy"
   ```

---

## CI/CD Integration

### Add to GitHub Actions

```yaml
# .github/workflows/visual-regression.yml
name: Visual Regression Tests

on: [pull_request]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run visual regression tests
        run: |
          # Install dependencies
          pip install playwright
          # Run visual tests
          python test/e2e/visual_regression.py
      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: visual-regression-diffs
          path: test/visual-diffs/
```

---

## Best Practices

1. **Take baselines at consistent viewport size** (1440x900)
2. **Wait for animations to complete** before capturing
3. **Use consistent data** (same wallet names, amounts, etc.)
4. **Capture in consistent order** every time
5. **Document changes** in commit messages
6. **Review diffs carefully** before approving
7. **Test on multiple platforms** (Mac, Linux, Windows)
8. **Compare against baselines before merging** PRs

---

## Reporting Visual Issues

If a visual regression is found:

```markdown
## Visual Regression Report

**Date**: 2026-06-28
**Screen**: Dashboard
**Issue**: Spacing between stat cards increased

### Details
- Previous spacing: 16px
- Current spacing: 24px
- Impact: Layout looks too spread out

### Fix
- Reverted css-padding from 24px to 16px
- Baseline updated
```

---

## Tools & Resources

- **ImageMagick** - Compare images pixel-by-pixel
- **Playwright** - Screenshot automation
- **Percy.io** - Visual testing SaaS (paid)
- **Applitools Eyes** - Visual testing SaaS (paid)
- **ResembleJS** - JavaScript visual testing

---

## Summary

Visual regression testing ensures that:
- ✅ Layout changes are intentional
- ✅ Styling remains consistent
- ✅ Responsive design works at all breakpoints
- ✅ Color and contrast are maintained
- ✅ Spacing and alignment are preserved

This is especially important for a GUI-focused project like Oracle Knots where visual consistency is a competitive advantage.
