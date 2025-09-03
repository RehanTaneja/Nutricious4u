#!/usr/bin/env python3
"""
Create a proper notification icon with transparency
"""

try:
    from PIL import Image, ImageDraw
    import os
    
    def create_notification_icon():
        """Create a simple, monochrome notification icon with transparency"""
        
        # Create a 96x96 image with transparency
        size = 96
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # Transparent background
        draw = ImageDraw.Draw(img)
        
        # Draw a simple, recognizable icon
        # Outer circle
        draw.ellipse([8, 8, size-8, size-8], outline=(255, 255, 255, 255), width=3)
        
        # Inner circle (nutrition/apple theme)
        center = size // 2
        draw.ellipse([center-20, center-20, center+20, center+20], 
                    fill=(255, 255, 255, 255))
        
        # Simple leaf
        leaf_points = [
            (center+20, center-20),
            (center+30, center-25),
            (center+25, center-15),
            (center+20, center-20)
        ]
        draw.polygon(leaf_points, fill=(255, 255, 255, 200))
        
        # Nutrition lines
        for i in range(3):
            y = center + 15 + (i * 8)
            draw.line([(center-15, y), (center+15, y)], 
                     fill=(255, 255, 255, 180), width=2)
        
        # Save the icon
        output_path = "../assets/notification_icon.png"
        img.save(output_path, "PNG")
        
        print(f"✅ Created notification icon: {output_path}")
        print(f"   Size: {size}x{size} pixels")
        print(f"   Format: PNG with transparency")
        print(f"   Colors: Monochrome white on transparent background")
        
        return True
        
    if __name__ == "__main__":
        create_notification_icon()
        
except ImportError:
    print("❌ PIL/Pillow not available. Creating fallback icon...")
    
    # Fallback: Create a simple icon using basic tools
    import subprocess
    import os
    
    def create_fallback_icon():
        """Create a fallback icon using basic tools"""
        
        # Create a simple SVG that we can convert
        svg_content = '''<svg width="96" height="96" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
  <circle cx="48" cy="48" r="44" fill="none" stroke="white" stroke-width="4"/>
  <circle cx="48" cy="48" r="20" fill="white"/>
  <path d="M68 28 Q72 26, 74 30 Q72 34, 68 32" fill="white"/>
  <line x1="48" y1="68" x2="48" y2="76" stroke="white" stroke-width="2"/>
  <line x1="32" y1="52" x2="64" y2="52" stroke="white" stroke-width="2"/>
  <line x1="36" y1="60" x2="60" y2="60" stroke="white" stroke-width="2"/>
</svg>'''
        
        svg_path = "notification_icon.svg"
        with open(svg_path, "w") as f:
            f.write(svg_content)
        
        print(f"✅ Created SVG icon: {svg_path}")
        print("   Note: This SVG needs to be converted to PNG with transparency")
        print("   Recommendation: Use an online SVG to PNG converter or design tool")
        
        return False
    
    create_fallback_icon()
