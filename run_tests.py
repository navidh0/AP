#!/usr/bin/env python
"""
Comprehensive test runner for the Django project.
This script runs all tests and provides detailed coverage information.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    print("Running test suite...")
    
    # Define test modules to run
    test_modules = [
        'core.tests',
        'core.admin_tests', 
        'doctor.tests',
        'booking.tests',
        'wallet.tests',
        'users.tests.test_signup',
        'users.tests.test_login',
        'users.tests.test_profile',
        'users.tests.test_activation',
        'users.tests.test_password_reset',
        'users.tests.test_password_change',
        'users.tests.test_otp_login',
        'users.tests.test_verify_phone',
        'users.tests.test_resend_activation',
        'users.tests.test_resend_otp',
    ]
    
    
    # Run tests
    failures = test_runner.run_tests(test_modules, verbosity=2)
    
    if failures:
        print(f"Tests failed: {failures}")
        sys.exit(1)
    else:
        print("All tests passed!")
        sys.exit(0)
