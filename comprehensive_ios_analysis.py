#!/usr/bin/env python3
"""
Comprehensive iOS Analysis Script
Analyzes the entire codebase for issues that could cause iOS crashes or functionality problems
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

class IOSIssueAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.file_patterns = {
            'typescript': ['*.ts', '*.tsx'],
            'javascript': ['*.js', '*.jsx'],
            'python': ['*.py'],
            'json': ['*.json'],
            'yaml': ['*.yml', '*.yaml']
        }
        
    def analyze_codebase(self) -> Dict[str, Any]:
        """Main analysis function"""
        print("🔍 Starting comprehensive iOS analysis...")
        
        # Analyze mobile app directory
        mobile_dir = self.root_dir / 'mobileapp'
        if mobile_dir.exists():
            self.analyze_mobile_app(mobile_dir)
        
        # Analyze backend directory
        backend_dir = self.root_dir / 'backend'
        if backend_dir.exists():
            self.analyze_backend(backend_dir)
        
        # Analyze root level files
        self.analyze_root_files()
        
        return {
            'total_issues': len(self.issues),
            'critical_issues': len([i for i in self.issues if i['severity'] == 'CRITICAL']),
            'high_issues': len([i for i in self.issues if i['severity'] == 'HIGH']),
            'medium_issues': len([i for i in self.issues if i['severity'] == 'MEDIUM']),
            'low_issues': len([i for i in self.issues if i['severity'] == 'LOW']),
            'issues': self.issues
        }
    
    def analyze_mobile_app(self, mobile_dir: Path):
        """Analyze mobile app for iOS-specific issues"""
        print("📱 Analyzing mobile app...")
        
        # Check for Promise.all patterns
        self.check_promise_all_patterns(mobile_dir)
        
        # Check for simultaneous API calls
        self.check_simultaneous_api_calls(mobile_dir)
        
        # Check for multiple useEffect hooks
        self.check_multiple_use_effects(mobile_dir)
        
        # Check for Firebase simultaneous calls
        self.check_firebase_simultaneous_calls(mobile_dir)
        
        # Check for timeout conflicts
        self.check_timeout_conflicts(mobile_dir)
        
        # Check for retry logic issues
        self.check_retry_logic_issues(mobile_dir)
        
        # Check for memory leaks
        self.check_memory_leaks(mobile_dir)
        
        # Check for iOS-specific issues
        self.check_ios_specific_issues(mobile_dir)
        
        # Check for WebView issues
        self.check_webview_issues(mobile_dir)
        
        # Check for AsyncStorage issues
        self.check_async_storage_issues(mobile_dir)
        
        # Check for navigation issues
        self.check_navigation_issues(mobile_dir)
        
        # Check for notification issues
        self.check_notification_issues(mobile_dir)
        
        # Check for image handling issues
        self.check_image_handling_issues(mobile_dir)
        
        # Check for file upload issues
        self.check_file_upload_issues(mobile_dir)
        
        # Check for state management issues
        self.check_state_management_issues(mobile_dir)
        
        # Check for error handling issues
        self.check_error_handling_issues(mobile_dir)
    
    def analyze_backend(self, backend_dir: Path):
        """Analyze backend for issues that could affect iOS"""
        print("🔧 Analyzing backend...")
        
        # Check for CORS issues
        self.check_cors_issues(backend_dir)
        
        # Check for timeout issues
        self.check_backend_timeout_issues(backend_dir)
        
        # Check for Firebase connection issues
        self.check_backend_firebase_issues(backend_dir)
        
        # Check for async/await issues
        self.check_backend_async_issues(backend_dir)
        
        # Check for error handling
        self.check_backend_error_handling(backend_dir)
    
    def analyze_root_files(self):
        """Analyze root level configuration files"""
        print("📄 Analyzing root files...")
        
        # Check package.json
        self.check_package_json()
        
        # Check app.json
        self.check_app_json()
        
        # Check eas.json
        self.check_eas_json()
    
    def check_promise_all_patterns(self, mobile_dir: Path):
        """Check for Promise.all patterns that could cause simultaneous API calls"""
        pattern = r'Promise\.all\s*\('
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context = self.get_line_context(content, line_num)
                
                self.issues.append({
                    'type': 'PROMISE_ALL_PATTERN',
                    'severity': 'HIGH',
                    'file': str(file_path.relative_to(self.root_dir)),
                    'line': line_num,
                    'description': 'Promise.all detected - could cause simultaneous API calls',
                    'context': context,
                    'recommendation': 'Replace with sequential calls or add delays'
                })
    
    def check_simultaneous_api_calls(self, mobile_dir: Path):
        """Check for patterns that could cause simultaneous API calls"""
        patterns = [
            r'await\s+Promise\.all\s*\(\s*\[',
            r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*fetch[^}]*\}',
            r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*api\.[a-zA-Z]+[^}]*\}'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'SIMULTANEOUS_API_CALLS',
                        'severity': 'HIGH',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Potential simultaneous API calls detected',
                        'context': context,
                        'recommendation': 'Add delays between API calls or use sequential processing'
                    })
    
    def check_multiple_use_effects(self, mobile_dir: Path):
        """Check for multiple useEffect hooks that could cause conflicts"""
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            # Count useEffect hooks
            useEffect_count = len(re.findall(r'useEffect\s*\(', content))
            
            if useEffect_count > 5:
                self.issues.append({
                    'type': 'MULTIPLE_USE_EFFECTS',
                    'severity': 'MEDIUM',
                    'file': str(file_path.relative_to(self.root_dir)),
                    'line': 1,
                    'description': f'Multiple useEffect hooks detected ({useEffect_count})',
                    'context': f'File contains {useEffect_count} useEffect hooks',
                    'recommendation': 'Consider consolidating useEffect hooks to prevent conflicts'
                })
    
    def check_firebase_simultaneous_calls(self, mobile_dir: Path):
        """Check for simultaneous Firebase calls"""
        patterns = [
            r'firestore\.collection.*\.get\(\)',
            r'firebase\.auth\(\)\.currentUser',
            r'firebase\.storage\(\)\.ref'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'FIREBASE_SIMULTANEOUS_CALLS',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Firebase call detected - could cause simultaneous requests',
                        'context': context,
                        'recommendation': 'Add delays between Firebase calls or use sequential processing'
                    })
    
    def check_timeout_conflicts(self, mobile_dir: Path):
        """Check for timeout configuration issues"""
        timeout_patterns = [
            r'timeout:\s*\d+',
            r'setTimeout\s*\(',
            r'clearTimeout\s*\('
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in timeout_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'TIMEOUT_CONFIGURATION',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Timeout configuration detected',
                        'context': context,
                        'recommendation': 'Ensure timeout values are appropriate for iOS'
                    })
    
    def check_retry_logic_issues(self, mobile_dir: Path):
        """Check for retry logic that could cause issues"""
        retry_patterns = [
            r'retry',
            r'retries',
            r'retryCondition'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in retry_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'RETRY_LOGIC',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Retry logic detected',
                        'context': context,
                        'recommendation': 'Ensure retry logic doesn\'t cause infinite loops on iOS'
                    })
    
    def check_memory_leaks(self, mobile_dir: Path):
        """Check for potential memory leaks"""
        memory_patterns = [
            r'setInterval\s*\(',
            r'addEventListener\s*\(',
            r'removeEventListener\s*\(',
            r'clearInterval\s*\('
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in memory_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'MEMORY_LEAK_POTENTIAL',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Potential memory leak detected',
                        'context': context,
                        'recommendation': 'Ensure proper cleanup in useEffect return function'
                    })
    
    def check_ios_specific_issues(self, mobile_dir: Path):
        """Check for iOS-specific issues"""
        ios_patterns = [
            r'Platform\.OS\s*===?\s*[\'"]ios[\'"]',
            r'CFNetwork',
            r'Darwin'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in ios_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'IOS_SPECIFIC_CODE',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'iOS-specific code detected',
                        'context': context,
                        'recommendation': 'Ensure iOS-specific code is properly tested'
                    })
    
    def check_webview_issues(self, mobile_dir: Path):
        """Check for WebView-related issues"""
        webview_patterns = [
            r'WebView',
            r'webview',
            r'<WebView'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in webview_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'WEBVIEW_USAGE',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'WebView usage detected',
                        'context': context,
                        'recommendation': 'Ensure WebView is properly configured for iOS'
                    })
    
    def check_async_storage_issues(self, mobile_dir: Path):
        """Check for AsyncStorage issues"""
        async_storage_patterns = [
            r'AsyncStorage\.getItem',
            r'AsyncStorage\.setItem',
            r'AsyncStorage\.removeItem'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in async_storage_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'ASYNC_STORAGE_USAGE',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'AsyncStorage usage detected',
                        'context': context,
                        'recommendation': 'Ensure AsyncStorage operations are properly awaited'
                    })
    
    def check_navigation_issues(self, mobile_dir: Path):
        """Check for navigation-related issues"""
        navigation_patterns = [
            r'navigation\.navigate',
            r'navigation\.push',
            r'navigation\.pop',
            r'navigation\.goBack'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in navigation_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'NAVIGATION_USAGE',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Navigation usage detected',
                        'context': context,
                        'recommendation': 'Ensure navigation is properly handled for iOS'
                    })
    
    def check_notification_issues(self, mobile_dir: Path):
        """Check for notification-related issues"""
        notification_patterns = [
            r'Notifications\.',
            r'notification',
            r'push.*notification'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in notification_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'NOTIFICATION_USAGE',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Notification usage detected',
                        'context': context,
                        'recommendation': 'Ensure notifications are properly configured for iOS'
                    })
    
    def check_image_handling_issues(self, mobile_dir: Path):
        """Check for image handling issues"""
        image_patterns = [
            r'Image\.',
            r'require\(.*\.(png|jpg|jpeg|gif)',
            r'imageUri',
            r'image.*upload'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in image_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'IMAGE_HANDLING',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Image handling detected',
                        'context': context,
                        'recommendation': 'Ensure image handling is optimized for iOS'
                    })
    
    def check_file_upload_issues(self, mobile_dir: Path):
        """Check for file upload issues"""
        upload_patterns = [
            r'upload',
            r'FormData',
            r'multipart',
            r'file.*upload'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in upload_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'FILE_UPLOAD',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'File upload detected',
                        'context': context,
                        'recommendation': 'Ensure file uploads are properly handled for iOS'
                    })
    
    def check_state_management_issues(self, mobile_dir: Path):
        """Check for state management issues"""
        state_patterns = [
            r'useState\s*\(',
            r'useContext\s*\(',
            r'useReducer\s*\(',
            r'setState'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            # Count state management patterns
            state_count = sum(len(re.findall(pattern, content)) for pattern in state_patterns)
            
            if state_count > 20:
                self.issues.append({
                    'type': 'STATE_MANAGEMENT_COMPLEXITY',
                    'severity': 'MEDIUM',
                    'file': str(file_path.relative_to(self.root_dir)),
                    'line': 1,
                    'description': f'Complex state management detected ({state_count} patterns)',
                    'context': f'File contains {state_count} state management patterns',
                    'recommendation': 'Consider simplifying state management to prevent iOS issues'
                })
    
    def check_error_handling_issues(self, mobile_dir: Path):
        """Check for error handling issues"""
        error_patterns = [
            r'try\s*\{',
            r'catch\s*\(',
            r'throw\s+new\s+Error',
            r'console\.error'
        ]
        
        for file_path in self.get_files(mobile_dir, ['*.ts', '*.tsx']):
            content = file_path.read_text(encoding='utf-8')
            
            # Check for missing error handling
            try_blocks = len(re.findall(r'try\s*\{', content))
            catch_blocks = len(re.findall(r'catch\s*\(', content))
            
            if try_blocks > catch_blocks:
                self.issues.append({
                    'type': 'MISSING_ERROR_HANDLING',
                    'severity': 'HIGH',
                    'file': str(file_path.relative_to(self.root_dir)),
                    'line': 1,
                    'description': f'Missing error handling detected ({try_blocks} try blocks, {catch_blocks} catch blocks)',
                    'context': f'File has {try_blocks} try blocks but only {catch_blocks} catch blocks',
                    'recommendation': 'Add proper error handling for all try blocks'
                })
    
    def check_cors_issues(self, backend_dir: Path):
        """Check for CORS configuration issues"""
        cors_patterns = [
            r'CORS',
            r'cors',
            r'Access-Control'
        ]
        
        for file_path in self.get_files(backend_dir, ['*.py']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in cors_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'CORS_CONFIGURATION',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'CORS configuration detected',
                        'context': context,
                        'recommendation': 'Ensure CORS is properly configured for iOS requests'
                    })
    
    def check_backend_timeout_issues(self, backend_dir: Path):
        """Check for backend timeout issues"""
        timeout_patterns = [
            r'timeout',
            r'wait_for',
            r'asyncio\.wait_for'
        ]
        
        for file_path in self.get_files(backend_dir, ['*.py']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in timeout_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'BACKEND_TIMEOUT',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Backend timeout configuration detected',
                        'context': context,
                        'recommendation': 'Ensure timeout values are appropriate for iOS requests'
                    })
    
    def check_backend_firebase_issues(self, backend_dir: Path):
        """Check for backend Firebase issues"""
        firebase_patterns = [
            r'firebase',
            r'firestore',
            r'Firebase'
        ]
        
        for file_path in self.get_files(backend_dir, ['*.py']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in firebase_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'BACKEND_FIREBASE',
                        'severity': 'MEDIUM',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Backend Firebase usage detected',
                        'context': context,
                        'recommendation': 'Ensure Firebase backend integration is stable'
                    })
    
    def check_backend_async_issues(self, backend_dir: Path):
        """Check for backend async/await issues"""
        async_patterns = [
            r'async\s+def',
            r'await\s+',
            r'asyncio'
        ]
        
        for file_path in self.get_files(backend_dir, ['*.py']):
            content = file_path.read_text(encoding='utf-8')
            
            for pattern in async_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = self.get_line_context(content, line_num)
                    
                    self.issues.append({
                        'type': 'BACKEND_ASYNC',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': line_num,
                        'description': 'Backend async/await usage detected',
                        'context': context,
                        'recommendation': 'Ensure async/await is properly implemented'
                    })
    
    def check_backend_error_handling(self, backend_dir: Path):
        """Check for backend error handling"""
        error_patterns = [
            r'try:',
            r'except:',
            r'raise\s+',
            r'logger\.error'
        ]
        
        for file_path in self.get_files(backend_dir, ['*.py']):
            content = file_path.read_text(encoding='utf-8')
            
            # Check for missing error handling
            try_blocks = len(re.findall(r'try:', content))
            except_blocks = len(re.findall(r'except:', content))
            
            if try_blocks > except_blocks:
                self.issues.append({
                    'type': 'BACKEND_MISSING_ERROR_HANDLING',
                    'severity': 'HIGH',
                    'file': str(file_path.relative_to(self.root_dir)),
                    'line': 1,
                    'description': f'Missing backend error handling detected ({try_blocks} try blocks, {except_blocks} except blocks)',
                    'context': f'File has {try_blocks} try blocks but only {except_blocks} except blocks',
                    'recommendation': 'Add proper error handling for all try blocks'
                })
    
    def check_package_json(self):
        """Check package.json for potential issues"""
        package_json = self.root_dir / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                
                # Check for problematic dependencies
                dependencies = data.get('dependencies', {})
                dev_dependencies = data.get('devDependencies', {})
                
                problematic_deps = [
                    'react-native-webview',
                    'react-native-pdf',
                    'react-native-fs',
                    'react-native-image-picker'
                ]
                
                for dep in problematic_deps:
                    if dep in dependencies or dep in dev_dependencies:
                        self.issues.append({
                            'type': 'PROBLEMATIC_DEPENDENCY',
                            'severity': 'MEDIUM',
                            'file': 'package.json',
                            'line': 1,
                            'description': f'Potentially problematic dependency: {dep}',
                            'context': f'Dependency {dep} detected in package.json',
                            'recommendation': 'Ensure this dependency is properly configured for iOS'
                        })
            except Exception as e:
                self.issues.append({
                    'type': 'PACKAGE_JSON_ERROR',
                    'severity': 'HIGH',
                    'file': 'package.json',
                    'line': 1,
                    'description': f'Error reading package.json: {e}',
                    'context': 'Failed to parse package.json',
                    'recommendation': 'Fix package.json syntax errors'
                })
    
    def check_app_json(self):
        """Check app.json for potential issues"""
        app_json = self.root_dir / 'mobileapp' / 'app.json'
        if app_json.exists():
            try:
                data = json.loads(app_json.read_text())
                
                # Check for iOS-specific configuration
                ios_config = data.get('expo', {}).get('ios', {})
                
                if not ios_config:
                    self.issues.append({
                        'type': 'MISSING_IOS_CONFIG',
                        'severity': 'MEDIUM',
                        'file': 'mobileapp/app.json',
                        'line': 1,
                        'description': 'Missing iOS-specific configuration',
                        'context': 'No iOS configuration found in app.json',
                        'recommendation': 'Add iOS-specific configuration to app.json'
                    })
            except Exception as e:
                self.issues.append({
                    'type': 'APP_JSON_ERROR',
                    'severity': 'HIGH',
                    'file': 'mobileapp/app.json',
                    'line': 1,
                    'description': f'Error reading app.json: {e}',
                    'context': 'Failed to parse app.json',
                    'recommendation': 'Fix app.json syntax errors'
                })
    
    def check_eas_json(self):
        """Check eas.json for potential issues"""
        eas_json = self.root_dir / 'eas.json'
        if eas_json.exists():
            try:
                data = json.loads(eas_json.read_text())
                
                # Check for iOS build configuration
                ios_build = data.get('build', {}).get('ios', {})
                
                if not ios_build:
                    self.issues.append({
                        'type': 'MISSING_IOS_BUILD_CONFIG',
                        'severity': 'MEDIUM',
                        'file': 'eas.json',
                        'line': 1,
                        'description': 'Missing iOS build configuration',
                        'context': 'No iOS build configuration found in eas.json',
                        'recommendation': 'Add iOS build configuration to eas.json'
                    })
            except Exception as e:
                self.issues.append({
                    'type': 'EAS_JSON_ERROR',
                    'severity': 'HIGH',
                    'file': 'eas.json',
                    'line': 1,
                    'description': f'Error reading eas.json: {e}',
                    'context': 'Failed to parse eas.json',
                    'recommendation': 'Fix eas.json syntax errors'
                })
    
    def get_files(self, directory: Path, patterns: List[str]) -> List[Path]:
        """Get all files matching the given patterns"""
        files = []
        for pattern in patterns:
            files.extend(directory.rglob(pattern))
        return files
    
    def get_line_context(self, content: str, line_num: int, context_lines: int = 3) -> str:
        """Get context around a specific line"""
        lines = content.split('\n')
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context_lines_list = []
        for i in range(start, end):
            prefix = '>>> ' if i == line_num - 1 else '    '
            context_lines_list.append(f'{prefix}{i+1:4d}: {lines[i]}')
        
        return '\n'.join(context_lines_list)

def main():
    """Main function"""
    analyzer = IOSIssueAnalyzer('.')
    results = analyzer.analyze_codebase()
    
    # Print summary
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"Total Issues: {results['total_issues']}")
    print(f"Critical: {results['critical_issues']}")
    print(f"High: {results['high_issues']}")
    print(f"Medium: {results['medium_issues']}")
    print(f"Low: {results['low_issues']}")
    
    # Save detailed report
    report_file = 'COMPREHENSIVE_IOS_ANALYSIS_REPORT.md'
    
    with open(report_file, 'w') as f:
        f.write("# Comprehensive iOS Analysis Report\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Issues**: {results['total_issues']}\n")
        f.write(f"- **Critical Issues**: {results['critical_issues']}\n")
        f.write(f"- **High Issues**: {results['high_issues']}\n")
        f.write(f"- **Medium Issues**: {results['medium_issues']}\n")
        f.write(f"- **Low Issues**: {results['low_issues']}\n\n")
        
        f.write("## Detailed Issues\n\n")
        
        # Group by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            severity_issues = [i for i in results['issues'] if i['severity'] == severity]
            if severity_issues:
                f.write(f"### {severity} Issues\n\n")
                
                for issue in severity_issues:
                    f.write(f"#### {issue['type']}\n")
                    f.write(f"- **File**: `{issue['file']}:{issue['line']}`\n")
                    f.write(f"- **Description**: {issue['description']}\n")
                    f.write(f"- **Recommendation**: {issue['recommendation']}\n")
                    f.write(f"- **Context**:\n```\n{issue['context']}\n```\n\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return results for further processing
    return results

if __name__ == "__main__":
    main()
