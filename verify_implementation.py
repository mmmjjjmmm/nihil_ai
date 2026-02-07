#!/usr/bin/env python3
"""
Verification script for contribution feature implementation.
Checks that all modules can be imported without errors.
"""

import sys

def verify_imports():
    """Verify all new modules can be imported."""
    print("🔍 Verifying Implementation...\n")

    checks = []

    # Check 1: Answer Generator
    print("1. Checking answer_generator.py...")
    try:
        from app.services.answer_generator import generate_answer_suggestions
        print("   ✓ answer_generator imports successfully")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Failed to import answer_generator: {e}")
        checks.append(False)

    # Check 2: Contribution Service
    print("2. Checking contribution_service.py...")
    try:
        from app.services.contribution_service import (
            create_contribution_with_suggestions,
            get_contribution_by_token,
            finalize_contribution
        )
        print("   ✓ contribution_service imports successfully")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Failed to import contribution_service: {e}")
        checks.append(False)

    # Check 3: Stripe Service
    print("3. Checking stripe_service.py...")
    try:
        from app.services.stripe_service import (
            create_checkout_session,
            verify_webhook_signature
        )
        print("   ✓ stripe_service imports successfully")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Failed to import stripe_service: {e}")
        checks.append(False)

    # Check 4: Contributions API
    print("4. Checking contributions.py API...")
    try:
        from app.api.contributions import router
        print("   ✓ contributions API imports successfully")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Failed to import contributions API: {e}")
        checks.append(False)

    # Check 5: Database Model
    print("5. Checking PendingContribution model...")
    try:
        from app.core.database import PendingContribution
        print("   ✓ PendingContribution model imports successfully")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Failed to import PendingContribution: {e}")
        checks.append(False)

    # Check 6: Updated Config
    print("6. Checking configuration settings...")
    try:
        from app.core.config import settings
        assert hasattr(settings, 'stripe_api_key'), "Missing stripe_api_key"
        assert hasattr(settings, 'stripe_webhook_secret'), "Missing stripe_webhook_secret"
        assert hasattr(settings, 'chatgpt_model'), "Missing chatgpt_model"
        assert hasattr(settings, 'base_url'), "Missing base_url"
        assert hasattr(settings, 'contribution_expiry_hours'), "Missing contribution_expiry_hours"
        print("   ✓ All configuration settings present")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        checks.append(False)

    # Check 7: Updated Responder
    print("7. Checking responder.py modifications...")
    try:
        from app.services.responder import process_mention
        import inspect
        source = inspect.getsource(process_mention)
        assert 'create_contribution_with_suggestions' in source, "Responder not updated"
        print("   ✓ responder.py contains contribution flow")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Responder check failed: {e}")
        checks.append(False)

    # Check 8: Main API Router Registration
    print("8. Checking API router registration...")
    try:
        from app.api.main import app
        route_paths = [route.path for route in app.routes]
        assert any('/checkout' in path for path in route_paths), "Checkout routes not registered"
        print("   ✓ Contribution routes registered in main API")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Router registration check failed: {e}")
        checks.append(False)

    # Check 9: Template Files
    print("9. Checking template files...")
    try:
        import os
        template_dir = "app/templates"
        templates = ['checkout.html', 'success.html', 'cancel.html']
        for template in templates:
            path = os.path.join(template_dir, template)
            assert os.path.exists(path), f"Missing {template}"
        print("   ✓ All template files present")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Template check failed: {e}")
        checks.append(False)

    # Check 10: Dependencies
    print("10. Checking dependencies...")
    try:
        import stripe
        import jinja2
        print("   ✓ stripe and jinja2 installed")
        checks.append(True)
    except Exception as e:
        print(f"   ✗ Dependency check failed: {e}")
        checks.append(False)

    # Summary
    print("\n" + "="*50)
    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\n🎉 Implementation is complete and ready to use!")
        print("\nNext steps:")
        print("1. Configure .env with Stripe keys")
        print("2. Run: botx init-db")
        print("3. Run: python test_contribution_flow.py")
        return True
    else:
        print(f"❌ {total - passed} check(s) failed ({passed}/{total} passed)")
        print("\n⚠️  Please fix the errors above before proceeding.")
        return False


if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
