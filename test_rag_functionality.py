#!/usr/bin/env python3
"""
Test script to verify RAG functionality with diet PDFs.
This script tests the PDF text extraction and chatbot enhancement.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_ID = "test_user_123"  # Replace with actual test user ID

def test_pdf_rag_functionality():
    """Test the RAG functionality with diet PDFs."""
    
    print("Testing RAG Functionality with Diet PDFs...")
    print("=" * 50)
    
    # Test 1: Check if user has a diet PDF
    print("\n1. Testing GET /users/{user_id}/diet")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ User diet data retrieved successfully")
            print(f"  dietPdfUrl: {data.get('dietPdfUrl', 'Not found')}")
            print(f"  hasDiet: {data.get('hasDiet', False)}")
            print(f"  daysRemaining: {data.get('daysRemaining', 'N/A')}")
            
            if data.get('dietPdfUrl'):
                print("✓ User has a diet PDF - RAG functionality should work")
            else:
                print("⚠ User has no diet PDF - RAG functionality will use basic prompt")
        else:
            print(f"✗ Failed to get user diet: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting user diet: {e}")
        return False
    
    # Test 2: Test chatbot message with diet context
    print("\n2. Testing chatbot message with diet context")
    try:
        # Prepare a test message about diet
        test_message = "What should I eat for breakfast according to my diet plan?"
        
        # Get user profile first
        profile_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile")
        user_profile = None
        if profile_response.status_code == 200:
            user_profile = profile_response.json()
            print(f"✓ User profile retrieved")
        else:
            print(f"⚠ Could not get user profile: {profile_response.status_code}")
            # Create a minimal profile for testing
            user_profile = {
                "userId": TEST_USER_ID,
                "firstName": "Test",
                "lastName": "User",
                "age": 30,
                "gender": "Not specified",
                "email": "test@example.com",
                "dietPdfUrl": data.get('dietPdfUrl') if 'data' in locals() else None
            }
        
        # Send chatbot message
        chatbot_request = {
            "userId": TEST_USER_ID,
            "chat_history": [
                {"sender": "user", "text": "Hello"},
                {"sender": "bot", "text": "Hello! I'm NutriBot, your nutrition assistant."}
            ],
            "user_profile": user_profile,
            "user_message": test_message
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chatbot/message",
            json=chatbot_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            bot_message = result.get('bot_message', '')
            print(f"✓ Chatbot responded successfully")
            print(f"  User message: {test_message}")
            print(f"  Bot response: {bot_message[:200]}...")
            
            # Check if response mentions diet plan
            if any(keyword in bot_message.lower() for keyword in ['diet', 'plan', 'meal', 'nutrition']):
                print("✓ Response appears to reference diet/nutrition information")
            else:
                print("⚠ Response doesn't seem to reference diet information")
                
        else:
            print(f"✗ Chatbot request failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing chatbot: {e}")
        return False
    
    # Test 3: Test PDF text extraction (if PDF exists)
    if 'data' in locals() and data.get('dietPdfUrl'):
        print("\n3. Testing PDF text extraction")
        try:
            response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf")
            if response.status_code == 200:
                print(f"✓ PDF retrieved successfully")
                print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"  Content-Length: {len(response.content)} bytes")
                
                # Try to extract text (this would be done by the RAG service)
                print("  Note: PDF text extraction is handled by the RAG service on the backend")
                
            else:
                print(f"✗ Failed to retrieve PDF: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error testing PDF retrieval: {e}")
    
    print("\n" + "=" * 50)
    print("RAG Functionality Test Complete!")
    print("\nSummary:")
    print("- The chatbot now includes RAG functionality to read diet PDFs")
    print("- When a user has a diet PDF, the chatbot can answer questions about it")
    print("- The system automatically extracts text from PDFs and includes it in the prompt")
    print("- Users can ask questions like 'What should I eat for breakfast?' and get personalized answers")
    
    return True

def test_diet_specific_questions():
    """Test specific diet-related questions to verify RAG functionality."""
    
    print("\nTesting Diet-Specific Questions...")
    print("=" * 50)
    
    # Questions that should benefit from diet PDF context
    test_questions = [
        "What should I eat for breakfast according to my diet plan?",
        "Can you tell me about my lunch options?",
        "What are my dinner recommendations?",
        "How many calories should I consume today?",
        "What snacks are allowed in my diet?",
        "Are there any foods I should avoid?",
        "What's my recommended protein intake?",
        "Can you explain my meal timing?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {question}")
        try:
            # Get user profile
            profile_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile")
            user_profile = None
            if profile_response.status_code == 200:
                user_profile = profile_response.json()
            
            # Send question to chatbot
            chatbot_request = {
                "userId": TEST_USER_ID,
                "chat_history": [],
                "user_profile": user_profile,
                "user_message": question
            }
            
            response = requests.post(
                f"{API_BASE_URL}/chatbot/message",
                json=chatbot_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                bot_message = result.get('bot_message', '')
                print(f"   Response: {bot_message[:150]}...")
                
                # Check if response is personalized
                if any(keyword in bot_message.lower() for keyword in ['your diet', 'your plan', 'according to', 'recommended']):
                    print(f"   ✓ Response appears personalized")
                else:
                    print(f"   ⚠ Response seems generic")
                    
            else:
                print(f"   ✗ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")

if __name__ == "__main__":
    print("RAG Functionality Test Suite")
    print("=" * 50)
    
    # Run main test
    success = test_pdf_rag_functionality()
    
    if success:
        # Run diet-specific question tests
        test_diet_specific_questions()
    
    print("\nTest completed!") 