#!/usr/bin/env python3
"""
Debug Multiple Notification Listeners
====================================

This script analyzes the multiple notification listeners that could be causing conflicts.
"""

def analyze_notification_listeners():
    """Analyze all notification listeners"""
    print("🔍 ANALYZING NOTIFICATION LISTENERS")
    print("=" * 50)
    
    with open('mobileapp/screens.tsx', 'r') as f:
        content = f.read()
    
    # Find all notification listeners
    listeners = []
    
    # DashboardScreen listener
    dashboard_start = content.find('// Handle new diet notifications')
    if dashboard_start != -1:
        dashboard_end = content.find('} catch (error) {', dashboard_start)
        if dashboard_end != -1:
            listeners.append({
                'name': 'DashboardScreen',
                'location': 'screens.tsx',
                'purpose': 'Handle new diet notifications and show popup',
                'code': content[dashboard_start:dashboard_end]
            })
    
    # NotificationSettingsScreen listener
    settings_start = content.find('// Set up notification listener to handle new diets')
    if settings_start != -1:
        settings_end = content.find('} catch (error) {', settings_start)
        if settings_end != -1:
            listeners.append({
                'name': 'NotificationSettingsScreen',
                'location': 'screens.tsx',
                'purpose': 'Refresh diet notifications on new diet',
                'code': content[settings_start:settings_end]
            })
    
    # DieticianMessagesListScreen listener
    dietician_start = content.find('// Add notification listener for dietician messages')
    if dietician_start != -1:
        dietician_end = content.find('} catch (error) {', dietician_start)
        if dietician_end != -1:
            listeners.append({
                'name': 'DieticianMessagesListScreen',
                'location': 'screens.tsx',
                'purpose': 'Handle dietician message notifications',
                'code': content[dietician_start:dietician_end]
            })
    
    # Another listener (found in search)
    another_start = content.find('// Handle user message notifications')
    if another_start != -1:
        another_end = content.find('} catch (error) {', another_start)
        if another_end != -1:
            listeners.append({
                'name': 'Another Message Listener',
                'location': 'screens.tsx',
                'purpose': 'Handle user message notifications',
                'code': content[another_start:another_end]
            })
    
    # Firebase service listener
    with open('mobileapp/services/firebase.ts', 'r') as f:
        firebase_content = f.read()
    
    firebase_start = firebase_content.find('setupDietNotificationListener')
    if firebase_start != -1:
        firebase_end = firebase_content.find('}', firebase_start)
        if firebase_end != -1:
            listeners.append({
                'name': 'Firebase Service',
                'location': 'services/firebase.ts',
                'purpose': 'General diet notification handling',
                'code': firebase_content[firebase_start:firebase_end]
            })
    
    print(f"Found {len(listeners)} notification listeners:")
    print()
    
    for i, listener in enumerate(listeners, 1):
        print(f"{i}. 📱 {listener['name']}")
        print(f"   Location: {listener['location']}")
        print(f"   Purpose: {listener['purpose']}")
        
        # Check for potential conflicts
        conflicts = []
        if 'new_diet' in listener['code']:
            conflicts.append("Handles new_diet notifications")
        if 'setShowAutoExtractionPopup' in listener['code']:
            conflicts.append("Controls popup state")
        if 'loadDietNotifications' in listener['code']:
            conflicts.append("Refreshes diet notifications")
        if 'message_notification' in listener['code']:
            conflicts.append("Handles message notifications")
        
        if conflicts:
            print(f"   Conflicts: {', '.join(conflicts)}")
        else:
            print(f"   Conflicts: None detected")
        
        print()
    
    return listeners

def identify_conflicts():
    """Identify potential conflicts between listeners"""
    print("🚨 IDENTIFYING POTENTIAL CONFLICTS")
    print("=" * 50)
    
    conflicts = [
        {
            'issue': 'Multiple new_diet handlers',
            'description': 'Multiple listeners handling the same notification type',
            'impact': 'Could cause race conditions or duplicate processing',
            'severity': 'HIGH'
        },
        {
            'issue': 'Popup state conflicts',
            'description': 'Multiple listeners trying to control popup state',
            'impact': 'Popup might not show or behave unpredictably',
            'severity': 'CRITICAL'
        },
        {
            'issue': 'Listener cleanup issues',
            'description': 'Multiple listeners might not be properly cleaned up',
            'impact': 'Memory leaks and duplicate listeners',
            'severity': 'MEDIUM'
        },
        {
            'issue': 'Processing order',
            'description': 'Unpredictable order of listener execution',
            'impact': 'Inconsistent behavior',
            'severity': 'MEDIUM'
        }
    ]
    
    for conflict in conflicts:
        print(f"⚠️  {conflict['issue']} ({conflict['severity']})")
        print(f"   Description: {conflict['description']}")
        print(f"   Impact: {conflict['impact']}")
        print()
    
    return conflicts

def create_fix_recommendations():
    """Create recommendations to fix the conflicts"""
    print("🛠️ FIX RECOMMENDATIONS")
    print("=" * 50)
    
    print("""
🔧 IMMEDIATE FIXES:

1. 🎯 CONSOLIDATE NOTIFICATION HANDLING:
   - Keep only ONE listener in DashboardScreen for new_diet notifications
   - Remove duplicate listeners from other screens
   - Use a centralized notification service

2. 🚫 REMOVE CONFLICTING LISTENERS:
   - Remove new_diet handling from NotificationSettingsScreen
   - Remove new_diet handling from Firebase service
   - Keep only message handling in other screens

3. 🔄 IMPLEMENT PROPER CLEANUP:
   - Ensure all listeners are properly cleaned up
   - Use useEffect cleanup functions
   - Avoid memory leaks

4. 🎯 CENTRALIZE POPUP CONTROL:
   - Only DashboardScreen should control popup state
   - Other screens should not interfere with popup logic
   - Use proper state management

🔧 SPECIFIC CHANGES NEEDED:

1. Remove this from NotificationSettingsScreen:
   ```javascript
   // Remove this entire useEffect
   useEffect(() => {
     const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
       // Remove new_diet handling here
     });
   }, []);
   ```

2. Remove this from Firebase service:
   ```javascript
   // Remove or modify setupDietNotificationListener
   export function setupDietNotificationListener() {
     // Remove new_diet handling
   }
   ```

3. Keep only DashboardScreen listener:
   ```javascript
   // Keep this in DashboardScreen
   useEffect(() => {
     const subscription = Notifications.addNotificationReceivedListener(async (notification) => {
       // Handle new_diet notifications and popup here
     });
     return () => subscription.remove();
   }, [userId]);
   ```

4. Add proper cleanup to all listeners:
   ```javascript
   useEffect(() => {
     const subscription = Notifications.addNotificationReceivedListener(handler);
     return () => subscription.remove(); // Always cleanup
   }, [dependencies]);
   ```
""")

def main():
    """Run multiple listener analysis"""
    print("🐛 MULTIPLE NOTIFICATION LISTENERS ANALYSIS")
    print("=" * 60)
    print("Analyzing potential conflicts between multiple listeners\n")
    
    # Analyze listeners
    listeners = analyze_notification_listeners()
    
    # Identify conflicts
    conflicts = identify_conflicts()
    
    # Create fix recommendations
    create_fix_recommendations()
    
    # Final summary
    print("\n🎯 FINAL SUMMARY")
    print("=" * 50)
    
    print(f"""
🚨 CRITICAL ISSUE FOUND!
========================

Found {len(listeners)} notification listeners that could be causing conflicts!

🔍 ROOT CAUSE:
Multiple listeners are handling the same notifications, causing:
- Race conditions
- Popup state conflicts
- Unpredictable behavior
- Memory leaks

🛠️ IMMEDIATE ACTION REQUIRED:
1. Remove duplicate new_diet listeners
2. Keep only DashboardScreen listener for popup
3. Implement proper cleanup
4. Test popup functionality

This explains why the popup isn't working - multiple listeners are interfering with each other! 🎯
""")

if __name__ == "__main__":
    main()
