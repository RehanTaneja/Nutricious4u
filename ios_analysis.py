#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path

def analyze_ios_issues():
    """Analyze codebase for iOS-specific issues"""
    issues = []
    
    # Check for Promise.all patterns
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.ts', '.tsx')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Check for Promise.all
                        if 'Promise.all' in content:
                            issues.append({
                                'type': 'PROMISE_ALL',
                                'severity': 'HIGH',
                                'file': filepath,
                                'description': 'Promise.all detected - could cause simultaneous API calls'
                            })
                        
                        # Check for multiple useEffect
                        useEffect_count = content.count('useEffect')
                        if useEffect_count > 5:
                            issues.append({
                                'type': 'MULTIPLE_USE_EFFECT',
                                'severity': 'MEDIUM',
                                'file': filepath,
                                'description': f'Multiple useEffect hooks ({useEffect_count})'
                            })
                        
                        # Check for simultaneous API calls
                        if 'api.' in content and 'useEffect' in content:
                            issues.append({
                                'type': 'SIMULTANEOUS_API',
                                'severity': 'HIGH',
                                'file': filepath,
                                'description': 'Potential simultaneous API calls in useEffect'
                            })
                            
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return issues

def main():
    issues = analyze_ios_issues()
    
    print(f"Found {len(issues)} potential iOS issues:")
    for issue in issues:
        print(f"- {issue['severity']}: {issue['type']} in {issue['file']}")
        print(f"  {issue['description']}")
        print()

if __name__ == "__main__":
    main()
