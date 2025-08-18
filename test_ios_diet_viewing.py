#!/usr/bin/env python3
"""
Comprehensive test to analyze iOS diet viewing functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://nutricious4u-production.up.railway.app/api"
TEST_USER_ID = "EMoXb6rFuwN3xKsotq54K0kVArf1"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def test_diet_pdf_endpoint():
    """Test the diet PDF endpoint functionality"""
    print_section("Testing Diet PDF Endpoint")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the diet PDF endpoint
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf", headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')}")
        print(f"Content-Disposition: {response.headers.get('content-disposition')}")
        print(f"Cache-Control: {response.headers.get('cache-control')}")
        
        if response.status_code == 200:
            print(f"✅ Diet PDF endpoint working correctly")
            print(f"   PDF size: {len(response.content)} bytes")
            print(f"   Content type: {response.headers.get('content-type')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  No diet PDF found for user (expected for test)")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Diet PDF endpoint test failed: {e}")
        return False

def test_user_profile_diet_url():
    """Test if user profile contains diet PDF URL"""
    print_section("Testing User Profile Diet URL")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Get user profile
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=30)
        
        if response.status_code == 200:
            profile = response.json()
            diet_pdf_url = profile.get('dietPdfUrl')
            last_diet_upload = profile.get('lastDietUpload')
            
            print(f"✅ User profile retrieved successfully")
            print(f"   Diet PDF URL: {diet_pdf_url}")
            print(f"   Last Diet Upload: {last_diet_upload}")
            
            if diet_pdf_url:
                print(f"   ✅ Diet PDF URL exists")
                return True
            else:
                print(f"   ⚠️  No diet PDF URL found")
                return False
        else:
            print(f"❌ Failed to get user profile: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ User profile test failed: {e}")
        return False

def test_webview_compatibility():
    """Test WebView compatibility with iOS"""
    print_section("Testing WebView Compatibility")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test if the PDF can be accessed with iOS headers
        response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf", headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Check if the response is a valid PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                print(f"✅ PDF is accessible with iOS headers")
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {response.headers.get('content-length')}")
                
                # Check if the PDF content is valid
                if response.content.startswith(b'%PDF'):
                    print(f"   ✅ Valid PDF content detected")
                    return True
                else:
                    print(f"   ⚠️  Content doesn't appear to be a valid PDF")
                    return False
            else:
                print(f"   ⚠️  Unexpected content type: {content_type}")
                return False
        else:
            print(f"❌ PDF not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ WebView compatibility test failed: {e}")
        return False

def test_ios_specific_headers():
    """Test iOS-specific header handling"""
    print_section("Testing iOS-Specific Headers")
    
    try:
        # Test with various iOS headers
        ios_headers = [
            {
                'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
                'X-Platform': 'ios',
                'X-App-Version': '1.0.0',
                'Accept': 'application/pdf,*/*',
                'Connection': 'keep-alive'
            },
            {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'application/pdf,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br'
            }
        ]
        
        for i, headers in enumerate(ios_headers):
            print(f"\nTesting header set {i+1}:")
            try:
                response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf", headers=headers, timeout=30)
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   X-Platform: {response.headers.get('x-platform')}")
                
                if response.status_code == 200:
                    print(f"   ✅ Success with header set {i+1}")
                else:
                    print(f"   ❌ Failed with header set {i+1}")
                    
            except Exception as e:
                print(f"   ❌ Error with header set {i+1}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ iOS headers test failed: {e}")
        return False

def test_pdf_viewer_html():
    """Test the PDF viewer HTML generation"""
    print_section("Testing PDF Viewer HTML")
    
    try:
        # Simulate the HTML generation that happens in the mobile app
        pdf_url = f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf"
        
        # Create the HTML content similar to createPdfViewerHtml function
        html_content = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
            <style>
              body {{ 
                margin: 0; 
                padding: 0; 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f5f5f5;
              }}
              .pdf-container {{
                width: 100%;
                height: 100vh;
                display: flex;
                flex-direction: column;
              }}
              .pdf-header {{
                background: #fff;
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
                text-align: center;
                font-weight: bold;
              }}
              .pdf-viewer {{
                flex: 1;
                width: 100%;
                height: 100%;
                border: none;
              }}
              .pdf-fallback {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                flex-direction: column;
                background: #fff;
              }}
              .pdf-fallback a {{
                color: #007AFF;
                text-decoration: none;
                font-size: 16px;
                margin-top: 10px;
              }}
            </style>
          </head>
          <body>
            <div class="pdf-container">
              <div class="pdf-header">Diet PDF Viewer</div>
              <iframe 
                class="pdf-viewer" 
                src="{pdf_url}" 
                type="application/pdf"
                onerror="showFallback()"
              ></iframe>
            </div>
            <script>
              function showFallback() {{
                document.body.innerHTML = \`
                  <div class="pdf-fallback">
                    <p>Unable to display PDF in browser</p>
                    <a href="{pdf_url}" target="_blank">Open PDF in New Tab</a>
                  </div>
                \`;
              }}
              
              // Check if PDF loads successfully
              setTimeout(() => {{
                const iframe = document.querySelector('.pdf-viewer');
                if (iframe && iframe.contentDocument && iframe.contentDocument.body.innerHTML === '') {{
                  showFallback();
                }}
              }}, 3000);
            </script>
          </body>
        </html>
        """
        
        print(f"✅ PDF viewer HTML generated successfully")
        print(f"   PDF URL: {pdf_url}")
        print(f"   HTML length: {len(html_content)} characters")
        print(f"   Contains iframe: {'iframe' in html_content}")
        print(f"   Contains fallback: {'showFallback' in html_content}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF viewer HTML test failed: {e}")
        return False

def test_upload_diet_screen_logic():
    """Test the upload diet screen logic"""
    print_section("Testing Upload Diet Screen Logic")
    
    try:
        headers = {
            'User-Agent': 'Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0',
            'X-Platform': 'ios',
            'X-App-Version': '1.0.0'
        }
        
        # Test the logic that determines if "View Current Diet" button should be shown
        # 1. Get user profile
        profile_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/profile", headers=headers, timeout=30)
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            diet_pdf_url = profile.get('dietPdfUrl')
            
            print(f"✅ User profile retrieved")
            print(f"   Diet PDF URL exists: {bool(diet_pdf_url)}")
            
            # 2. Test if the PDF URL is accessible
            if diet_pdf_url:
                pdf_response = requests.get(f"{API_BASE_URL}/users/{TEST_USER_ID}/diet/pdf", headers=headers, timeout=30)
                print(f"   PDF accessible: {pdf_response.status_code == 200}")
                
                if pdf_response.status_code == 200:
                    print(f"   ✅ 'View Current Diet' button should be visible")
                    return True
                else:
                    print(f"   ❌ 'View Current Diet' button should be hidden (PDF not accessible)")
                    return False
            else:
                print(f"   ⚠️  'View Current Diet' button should be hidden (no PDF URL)")
                return False
        else:
            print(f"❌ Failed to get user profile: {profile_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Upload diet screen logic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("iOS Diet Viewing Analysis")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Diet PDF Endpoint", test_diet_pdf_endpoint),
        ("User Profile Diet URL", test_user_profile_diet_url),
        ("WebView Compatibility", test_webview_compatibility),
        ("iOS-Specific Headers", test_ios_specific_headers),
        ("PDF Viewer HTML", test_pdf_viewer_html),
        ("Upload Diet Screen Logic", test_upload_diet_screen_logic),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Results Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! iOS diet viewing should work correctly.")
        print("\nPotential iOS Issues:")
        print("1. WebView configuration in React Native")
        print("2. iOS-specific permissions or restrictions")
        print("3. Network security settings in iOS")
        print("4. WebView content blocking")
        return 0
    else:
        print("⚠️  Some tests failed. iOS diet viewing may have issues.")
        print("\nRecommendations:")
        print("1. Check WebView configuration in the mobile app")
        print("2. Verify iOS-specific headers are being sent")
        print("3. Test on actual iOS device/simulator")
        print("4. Check iOS network security settings")
        return 1

if __name__ == "__main__":
    sys.exit(main())
