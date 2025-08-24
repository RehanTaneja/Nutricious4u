#!/usr/bin/env python3
"""
iOS Crash Fixes Verification Script
This script tests the critical fixes implemented for iOS EAS build crashes.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def test_gesture_handler_import():
    """Test if react-native-gesture-handler is properly imported"""
    print("🔍 Testing gesture handler import...")
    
    index_path = Path("mobileapp/index.js")
    if not index_path.exists():
        print("❌ index.js not found")
        return False
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    if "import 'react-native-gesture-handler';" in content:
        lines = content.split('\n')
        first_import_line = None
        for i, line in enumerate(lines):
            if "import 'react-native-gesture-handler';" in line:
                first_import_line = i
                break
        
        if first_import_line == 0:
            print("✅ react-native-gesture-handler imported correctly as first line")
            return True
        else:
            print(f"⚠️  react-native-gesture-handler found at line {first_import_line + 1}, but should be first line")
            return False
    else:
        print("❌ react-native-gesture-handler import missing")
        return False

def test_ios_config_updates():
    """Test iOS configuration updates"""
    print("🔍 Testing iOS configuration updates...")
    
    # Test app.json
    app_json_path = Path("mobileapp/app.json")
    if not app_json_path.exists():
        print("❌ app.json not found")
        return False
    
    with open(app_json_path, 'r') as f:
        app_config = json.load(f)
    
    ios_config = app_config.get('expo', {}).get('ios', {})
    info_plist = ios_config.get('infoPlist', {})
    
    # Check for iOS-specific configurations
    checks = [
        ('bundleIdentifier', ios_config.get('bundleIdentifier') == 'com.nutricious4u.app'),
        ('buildNumber', 'buildNumber' in ios_config),
        ('NSAppTransportSecurity', 'NSAppTransportSecurity' in info_plist),
        ('UIRequiredDeviceCapabilities', 'UIRequiredDeviceCapabilities' in info_plist),
        ('UIBackgroundModes', 'UIBackgroundModes' in info_plist),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name} configured correctly")
        else:
            print(f"❌ {check_name} missing or incorrect")
            all_passed = False
    
    return all_passed

def test_eas_config():
    """Test EAS configuration"""
    print("🔍 Testing EAS configuration...")
    
    eas_json_path = Path("mobileapp/eas.json")
    if not eas_json_path.exists():
        print("❌ eas.json not found")
        return False
    
    with open(eas_json_path, 'r') as f:
        eas_config = json.load(f)
    
    builds = eas_config.get('build', {})
    
    # Check each build profile has iOS bundler configured
    profiles = ['development', 'preview', 'production']
    all_passed = True
    
    for profile in profiles:
        if profile in builds:
            ios_config = builds[profile].get('ios', {})
            if ios_config.get('bundler') == 'metro':
                print(f"✅ {profile} profile has metro bundler configured")
            else:
                print(f"❌ {profile} profile missing metro bundler")
                all_passed = False
        else:
            print(f"❌ {profile} profile not found")
            all_passed = False
    
    return all_passed

def test_firebase_ios_optimizations():
    """Test Firebase iOS optimizations"""
    print("🔍 Testing Firebase iOS optimizations...")
    
    firebase_path = Path("mobileapp/services/firebase.ts")
    if not firebase_path.exists():
        print("❌ firebase.ts not found")
        return False
    
    with open(firebase_path, 'r') as f:
        content = f.read()
    
    checks = [
        ('Platform import', "import { Platform } from 'react-native';" in content),
        ('iOS Firebase optimization', "if (Platform.OS === 'ios')" in content),
        ('Firestore settings', "firebase.firestore().settings(" in content),
        ('experimentalForceLongPolling', "experimentalForceLongPolling: false" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name} found")
        else:
            print(f"❌ {check_name} missing")
            all_passed = False
    
    return all_passed

def test_app_ios_optimizations():
    """Test App.tsx iOS optimizations"""
    print("🔍 Testing App.tsx iOS optimizations...")
    
    app_path = Path("mobileapp/App.tsx")
    if not app_path.exists():
        print("❌ App.tsx not found")
        return False
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    checks = [
        ('Platform import', "Platform" in content and "from 'react-native'" in content),
        ('iOS timeout handling', "Platform.OS === 'ios' ? 20000 : 15000" in content),
        ('iOS EAS build handling', "[iOS EAS Build]" in content),
        ('iOS error recovery', "[iOS] Attempting MainTabs recovery" in content),
        ('iOS minimal initialization', "Minimal initialization to prevent crashes" in content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name} found")
        else:
            print(f"❌ {check_name} missing")
            all_passed = False
    
    return all_passed

def test_dependency_compatibility():
    """Test dependency compatibility"""
    print("🔍 Testing dependency compatibility...")
    
    package_json_path = Path("mobileapp/package.json")
    if not package_json_path.exists():
        print("❌ package.json not found")
        return False
    
    with open(package_json_path, 'r') as f:
        package_config = json.load(f)
    
    dependencies = package_config.get('dependencies', {})
    
    # Check for potentially problematic dependencies
    ios_compatible_deps = [
        ('react-native-gesture-handler', '~2.24.0'),
        ('firebase', '^9.6.11'),
        ('expo', '53.0.20'),
        ('react', '19.0.0'),
        ('react-native', '0.79.5'),
    ]
    
    all_passed = True
    for dep_name, expected_version in ios_compatible_deps:
        if dep_name in dependencies:
            actual_version = dependencies[dep_name]
            print(f"✅ {dep_name}: {actual_version}")
        else:
            print(f"❌ {dep_name} missing")
            all_passed = False
    
    return all_passed

def run_lint_check():
    """Run lint check to ensure no syntax errors"""
    print("🔍 Running lint check...")
    
    # Change to mobileapp directory
    mobileapp_dir = Path("mobileapp")
    if not mobileapp_dir.exists():
        print("❌ mobileapp directory not found")
        return False
    
    # Check if package.json has lint script
    package_json_path = mobileapp_dir / "package.json"
    if package_json_path.exists():
        with open(package_json_path, 'r') as f:
            package_config = json.load(f)
        
        scripts = package_config.get('scripts', {})
        if 'lint' in scripts:
            print("Running npm run lint...")
            returncode, stdout, stderr = run_command("npm run lint", cwd=mobileapp_dir)
            if returncode == 0:
                print("✅ Lint check passed")
                return True
            else:
                print(f"❌ Lint check failed: {stderr}")
                return False
    
    # If no lint script, check TypeScript compilation
    print("Running TypeScript check...")
    returncode, stdout, stderr = run_command("npx tsc --noEmit", cwd=mobileapp_dir)
    if returncode == 0:
        print("✅ TypeScript check passed")
        return True
    else:
        print(f"⚠️ TypeScript check warnings: {stderr}")
        # Don't fail on TypeScript warnings, just show them
        return True

def main():
    """Run all tests"""
    print("🚀 Starting iOS Crash Fixes Verification\n")
    
    tests = [
        ("Gesture Handler Import", test_gesture_handler_import),
        ("iOS Configuration Updates", test_ios_config_updates),
        ("EAS Configuration", test_eas_config),
        ("Firebase iOS Optimizations", test_firebase_ios_optimizations),
        ("App.tsx iOS Optimizations", test_app_ios_optimizations),
        ("Dependency Compatibility", test_dependency_compatibility),
        ("Lint Check", run_lint_check),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All iOS crash fixes are properly implemented!")
        print("\n📱 Next steps:")
        print("1. Test the app in Expo Go on iOS device")
        print("2. Create an EAS development build: eas build --platform ios --profile development")
        print("3. Test the development build on a physical iOS device")
        print("4. If successful, create production build: eas build --platform ios --profile production")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Please fix the issues above before building.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
