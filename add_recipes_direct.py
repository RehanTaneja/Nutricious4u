#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append('backend')

# Import Firebase client
from backend.services.firebase_client import initialize_firebase

def add_recipes():
    """Add sample recipes directly to Firestore"""
    
    # Initialize Firebase
    db, bucket = initialize_firebase()
    
    # Sample recipes data
    sample_recipes = [
  {
    "title": "Grilled Chicken Salad",
    "type": "Healthy Lunch",
    "allergies": "None",
    "link": "https://example.com/grilled-chicken-salad",
    "description": "A healthy and protein-rich salad with grilled chicken breast, mixed greens, cherry tomatoes, and a light vinaigrette dressing.",
    "calories": 350,
    "protein": 35,
    "fat": 12
  },
  {
    "title": "Quinoa Buddha Bowl",
    "type": "Vegetarian",
    "allergies": "Gluten",
    "link": "https://example.com/quinoa-buddha-bowl",
    "description": "A nutritious bowl with quinoa, roasted vegetables, avocado, and tahini dressing.",
    "calories": 420,
    "protein": 15,
    "fat": 18
  },
  {
    "title": "Salmon with Roasted Vegetables",
    "type": "Dinner",
    "allergies": "Fish",
    "link": "https://example.com/salmon-roasted-vegetables",
    "description": "Baked salmon fillet with a medley of roasted vegetables including broccoli, carrots, and sweet potatoes.",
    "calories": 480,
    "protein": 42,
    "fat": 22
  },
  {
    "title": "Greek Yogurt Parfait",
    "type": "Breakfast",
    "allergies": "Dairy",
    "link": "https://example.com/greek-yogurt-parfait",
    "description": "Greek yogurt layered with fresh berries, granola, and a drizzle of honey.",
    "calories": 280,
    "protein": 20,
    "fat": 8
  },
  {
    "title": "Vegetable Stir Fry",
    "type": "Asian",
    "allergies": "Soy",
    "link": "https://example.com/vegetable-stir-fry",
    "description": "Colorful stir-fried vegetables with tofu in a light ginger-soy sauce served over brown rice.",
    "calories": 320,
    "protein": 12,
    "fat": 10
  },
  {
    "title": "Turkey and Avocado Wrap",
    "type": "Lunch",
    "allergies": "Gluten",
    "link": "https://example.com/turkey-avocado-wrap",
    "description": "Lean turkey breast with fresh avocado, lettuce, and tomato wrapped in a whole grain tortilla.",
    "calories": 380,
    "protein": 28,
    "fat": 16
  },
  {
    "title": "Berry Smoothie Bowl",
    "type": "Breakfast",
    "allergies": "Berries",
    "link": "https://example.com/berry-smoothie-bowl",
    "description": "Thick smoothie bowl topped with fresh berries, granola, and coconut flakes.",
    "calories": 290,
    "protein": 8,
    "fat": 6
  },
  {
    "title": "Lentil Soup",
    "type": "Soup",
    "allergies": "None",
    "link": "https://example.com/lentil-soup",
    "description": "Hearty lentil soup with vegetables, herbs, and spices. Perfect for a healthy dinner.",
    "calories": 220,
    "protein": 18,
    "fat": 2
  }
]
    
    try:
        # Get the recipes collection
        recipes_ref = db.collection('recipes')
        
        # Add each recipe
        for recipe in sample_recipes:
            # Add timestamp
            recipe['createdAt'] = datetime.now()
            recipe['createdBy'] = 'system'
            
            # Add the recipe to Firestore
            doc_ref = recipes_ref.add(recipe)
            print(f"✅ Added recipe: {recipe['title']} (ID: {doc_ref[1].id})")
        
        print(f"\n🎉 Successfully added {len(sample_recipes)} sample recipes to Firestore!")
        print("📱 The recipes should now be visible in the mobile app.")
        
    except Exception as e:
        print(f"❌ Error adding recipes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_recipes()
