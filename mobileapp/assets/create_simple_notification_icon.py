#!/usr/bin/env python3
"""
Create Simple Notification Icon
==============================

This script creates a simple notification icon by resizing logo.png to 96x96
since it already has a white background and green N.
"""

from PIL import Image
import os

def create_simple_notification_icon():
    """Create a simple notification icon by resizing logo.png"""
    
    # Load the original logo
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        print(f"❌ Logo file not found: {logo_path}")
        return False
    
    try:
        # Open the logo image
        logo = Image.open(logo_path)
        print(f"✅ Loaded logo: {logo.size} pixels")
        
        # Convert to RGBA if not already
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Resize to 96x96 (standard notification size)
        notification_icon = logo.resize((96, 96), Image.Resampling.LANCZOS)
        
        # Save the notification icon
        notification_icon_path = "notification-icon.png"
        notification_icon.save(notification_icon_path, "PNG")
        
        print(f"✅ Created simple notification icon: {notification_icon_path}")
        print(f"✅ Size: {notification_icon.size} pixels")
        print(f"✅ Format: Resized logo with white background and green N")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating notification icon: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Creating simple notification icon from logo.png...")
    
    success = create_simple_notification_icon()
    
    if success:
        print("\n✅ Notification icon creation completed!")
        print("📋 Created file:")
        print("   • notification-icon.png (resized logo)")
        print("\n📋 Next steps:")
        print("   1. The logo already has white background and green N")
        print("   2. This should work well for notifications")
        print("   3. Rebuild the EAS app to test")
    else:
        print("\n❌ Failed to create notification icon")
