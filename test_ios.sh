#!/bin/bash

# iOS Testing Script
# Usage: ./test_ios.sh [quick|full|stress]

set -e

echo "📱 iOS Testing Suite"
echo "===================="

case "${1:-quick}" in
    "quick")
        echo "⚡ Running Quick iOS Test..."
        python quick_ios_test.py
        ;;
    "full")
        echo "🔍 Running Full iOS Simulation Test..."
        python ios_simulation_test.py
        ;;
    "stress")
        echo "🌐 Running Network Stress Test..."
        python ios_simulation_test.py
        ;;
    "all")
        echo "🚀 Running All Tests..."
        echo ""
        echo "1. Quick Test:"
        python quick_ios_test.py
        echo ""
        echo "2. Full Simulation:"
        python ios_simulation_test.py
        ;;
    *)
        echo "Usage: $0 [quick|full|stress|all]"
        echo ""
        echo "Options:"
        echo "  quick  - Fast validation (30 seconds)"
        echo "  full   - Comprehensive simulation (2-3 minutes)"
        echo "  stress - Network stress testing (1-2 minutes)"
        echo "  all    - Run all tests"
        echo ""
        echo "Examples:"
        echo "  $0 quick   # Quick check before EAS build"
        echo "  $0 full    # Full validation after changes"
        echo "  $0 all     # Complete testing suite"
        exit 1
        ;;
esac

echo ""
echo "✅ Testing complete!"
