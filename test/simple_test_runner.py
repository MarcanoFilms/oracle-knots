#!/usr/bin/env python3
"""
Simple test runner for Oracle Knots GUI tests.
No external dependencies required (pure Python unittest).
"""
import importlib.util
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def run_test_class(test_module_path, class_name):
    """Load and run a test class from a module."""
    try:
        spec = importlib.util.spec_from_file_location(
            test_module_path.stem,
            test_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        test_class = getattr(module, class_name, None)
        if not test_class:
            return None, f"Class {class_name} not found in {test_module_path.name}"

        # Run all test methods in the class
        instance = test_class()
        results = []
        test_methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in test_methods:
            try:
                method = getattr(instance, method_name)
                method()
                results.append((method_name, True, None))
            except Exception as e:
                results.append((method_name, False, str(e)))

        return results, None
    except Exception as e:
        return None, f"Error loading {class_name}: {str(e)}"


def main():
    """Run all test files and report results."""
    test_dir = Path(__file__).parent
    test_files = [
        'test_wallet_api.py',
        'test_config_api.py',
        'test_security_validation.py',
        'test_dashboard_api.py',
    ]

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("Oracle Knots GUI - Test Suite")
    print(f"{'='*60}{Colors.RESET}\n")

    total_passed = 0
    total_failed = 0
    total_errors = 0

    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"{Colors.YELLOW}⊘ {test_file} not found{Colors.RESET}")
            continue

        print(f"\n{Colors.BOLD}{test_file}{Colors.RESET}")
        print(f"{'-'*60}")

        # Get all Test classes in the file
        try:
            spec = importlib.util.spec_from_file_location(
                test_file[:-3],
                test_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all test classes
            test_classes = [
                name for name in dir(module)
                if name.startswith('Test') and isinstance(getattr(module, name), type)
            ]

            if not test_classes:
                print(f"{Colors.YELLOW}⊘ No test classes found{Colors.RESET}")
                continue

            for class_name in sorted(test_classes):
                results, error = run_test_class(test_path, class_name)

                if error:
                    print(f"{Colors.RED}✗ {class_name}: {error}{Colors.RESET}")
                    total_errors += 1
                    continue

                print(f"\n  {Colors.BOLD}{class_name}{Colors.RESET}")

                class_passed = 0
                class_failed = 0

                for method_name, success, error_msg in results:
                    if success:
                        print(f"    {Colors.GREEN}✓{Colors.RESET} {method_name}")
                        class_passed += 1
                        total_passed += 1
                    else:
                        print(f"    {Colors.RED}✗{Colors.RESET} {method_name}")
                        if error_msg:
                            print(f"      {Colors.RED}{error_msg}{Colors.RESET}")
                        class_failed += 1
                        total_failed += 1

                print(f"  {class_name}: {class_passed} passed, {class_failed} failed")

        except Exception as e:
            print(f"{Colors.RED}✗ Error loading {test_file}: {str(e)}{Colors.RESET}")
            traceback.print_exc()
            total_errors += 1

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.RESET}")
    print(f"Total Passed:  {Colors.GREEN}{total_passed}{Colors.RESET}")
    print(f"Total Failed:  {Colors.RED}{total_failed}{Colors.RESET}")
    print(f"Total Errors:  {Colors.YELLOW}{total_errors}{Colors.RESET}")
    print(f"{'='*60}\n")

    if total_failed == 0 and total_errors == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
