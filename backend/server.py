from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Form, Depends
from dotenv import load_dotenv
load_dotenv()
import os
print("DEBUG: FIREBASE_PROJECT_ID =", os.getenv("FIREBASE_PROJECT_ID"))
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
import json
import time
from services.health_platform import HealthPlatformFactory

# Import Firebase with error handling
try:
    from services.firebase_client import db as firestore_db, bucket
    from services.firebase_client import upload_diet_pdf, list_non_dietician_users
    # --- Simple Notification System ---
    from services.simple_notification_service import get_notification_service
    # Import Firebase Admin Auth for user deletion
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    FIREBASE_AVAILABLE = True
    print("✅ Firebase client imported successfully")
    
    # Test Firebase connection
    if firestore_db is not None:
        try:
            # Try a simple operation to test the connection
            test_collection = firestore_db.collection("test")
            print("✅ Firebase connection test successful")
        except Exception as test_error:
            print(f"⚠️  Firebase connection test failed: {test_error}")
            FIREBASE_AVAILABLE = False
            firestore_db = None
    else:
        print("⚠️  Firebase database is None")
        FIREBASE_AVAILABLE = False
        
except Exception as e:
    print(f"⚠️  Firebase client import failed: {e}")
    firestore_db = None
    bucket = None
    upload_diet_pdf = None
    list_non_dietician_users = None
    get_user_notification_token = None
    send_push_notification = None
    check_users_with_one_day_remaining = None
    firebase_auth = None
    FIREBASE_AVAILABLE = False

# Add import for PDF RAG service
from services.pdf_rag_service import pdf_rag_service
# Add import for diet notification service
from services.diet_notification_service import diet_notification_service
# Add import for notification scheduler
from services.notification_scheduler_simple import get_simple_notification_scheduler as get_notification_scheduler
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
import requests
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure
from google.generativeai.types import ContentDict
import tempfile
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Helper function to check Firebase availability
def check_firebase_availability():
    """Check if Firebase is available and return appropriate error response if not"""
    if not FIREBASE_AVAILABLE or firestore_db is None:
        raise HTTPException(
            status_code=503, 
            detail="Firebase service is currently unavailable. Please try again later."
        )

# Helper function to get user's first name from user_data
def get_user_first_name(user_data: dict) -> str:
    """Get user's first name from user_data, with fallback to 'User' if not available"""
    first_name = user_data.get("firstName", "")
    if first_name and first_name.strip() and first_name != "User":
        return first_name.strip()
    # Fallback: try to get from "name" field if it exists
    name = user_data.get("name", "")
    if name and name.strip() and name != "User":
        # Extract first name from full name if it's a full name
        name_parts = name.strip().split()
        if name_parts:
            return name_parts[0]
    return "User"  # Final fallback

# Define all required Pydantic models before any usage
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class FoodItem(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    per_100g: bool = True

class FoodSearchResponse(BaseModel):
    foods: List[FoodItem]

class FoodLogRequest(BaseModel):
    userId: str
    foodName: str
    servingSize: str = "100"
    # Optional pre-calculated nutrition data (if provided, skip Gemini call)
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    # Timezone offset from frontend (in minutes, e.g., -480 for PST)
    timezoneOffset: Optional[int] = None

class FoodLog(BaseModel):
    userId: str
    food: FoodItem
    servingSize: str = "100"
    timestamp: Optional[datetime] = None

class LogSummaryResponse(BaseModel):
    history: List[dict]

class WorkoutItem(BaseModel):
    id: int
    name: str
    calories_per_minute: float
    type: str

class WorkoutSearchResponse(BaseModel):
    exercises: List[WorkoutItem]

class UserProfile(BaseModel):
    userId: str
    firstName: str
    lastName: str
    age: int
    gender: str
    email: str
    currentWeight: Optional[float] = None
    goalWeight: Optional[float] = None
    height: Optional[float] = None
    dietaryPreference: Optional[str] = None
    favouriteCuisine: Optional[str] = None
    allergies: Optional[str] = None
    medicalConditions: Optional[str] = None
    activityLevel: Optional[str] = None
    targetCalories: Optional[float] = None
    targetProtein: Optional[float] = None
    targetFat: Optional[float] = None
    stepGoal: Optional[int] = None
    caloriesBurnedGoal: Optional[int] = None
    dietPdfUrl: Optional[str] = None
    lastDietUpload: Optional[str] = None
    dieticianId: Optional[str] = None
    # Subscription fields
    subscriptionPlan: Optional[str] = None  # '1month', '2months', '3months', '6months', 'free', 'trial'
    subscriptionStartDate: Optional[str] = None
    subscriptionEndDate: Optional[str] = None
    totalAmountPaid: Optional[float] = 0.0
    isSubscriptionActive: Optional[bool] = False
    currentSubscriptionAmount: Optional[float] = 0.0
    autoRenewalEnabled: Optional[bool] = True
    # New subscription system fields
    freeTrialUsed: Optional[bool] = False
    freeTrialStartDate: Optional[str] = None
    freeTrialEndDate: Optional[str] = None
    pendingPlanSwitch: Optional[dict] = None  # {newPlanId: str, switchDate: str, amount: float}
    nextPlanId: Optional[str] = None
    subscriptionStatus: Optional[str] = None  # 'trial', 'active', 'expired', 'cancelled', 'pending_switch'
    lastPaymentReminderSent: Optional[dict] = None  # {oneWeek: bool, twoDays: bool, oneDay: bool}

class UpdateUserProfile(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    currentWeight: Optional[float] = None
    goalWeight: Optional[float] = None
    height: Optional[float] = None
    dietaryPreference: Optional[str] = None
    favouriteCuisine: Optional[str] = None
    allergies: Optional[str] = None
    medicalConditions: Optional[str] = None
    activityLevel: Optional[str] = None
    targetCalories: Optional[float] = None
    targetProtein: Optional[float] = None
    targetFat: Optional[float] = None
    stepGoal: Optional[int] = None
    caloriesBurnedGoal: Optional[int] = None
    # Subscription fields
    subscriptionPlan: Optional[str] = None
    subscriptionStartDate: Optional[str] = None
    subscriptionEndDate: Optional[str] = None
    totalAmountPaid: Optional[float] = None
    isSubscriptionActive: Optional[bool] = None
    # Diet fields
    dietPdfUrl: Optional[str] = None
    lastDietUpload: Optional[str] = None
    dieticianId: Optional[str] = None
    dietCacheVersion: Optional[float] = None

class ChatMessageRequest(BaseModel):
    userId: str
    chat_history: list
    user_profile: dict
    user_message: str

class ChatMessageResponse(BaseModel):
    bot_message: str

class SubscriptionPlan(BaseModel):
    planId: str
    name: str
    duration: str
    price: float
    description: str

class SelectSubscriptionRequest(BaseModel):
    userId: str
    planId: str
    autoRenewalEnabled: Optional[bool] = True  # Default to True if not provided

class SubscriptionResponse(BaseModel):
    success: bool
    message: str
    subscription: Optional[dict] = None



class SubscriptionStatus(BaseModel):
    subscriptionPlan: Optional[str] = None
    subscriptionStartDate: Optional[str] = None
    subscriptionEndDate: Optional[str] = None
    totalAmountPaid: float = 0.0
    isSubscriptionActive: bool = False
    autoRenewalEnabled: Optional[bool] = True
    # New subscription system fields
    freeTrialUsed: Optional[bool] = False
    isTrialActive: Optional[bool] = False
    trialEndDate: Optional[str] = None
    pendingPlanSwitch: Optional[dict] = None
    nextPlanId: Optional[str] = None
    subscriptionStatus: Optional[str] = None
    requiresPlanSelection: Optional[bool] = False

# --- Appointment Models ---
class AppointmentRequest(BaseModel):
    userId: str
    userName: str
    userEmail: str
    date: str
    timeSlot: str
    status: str = "confirmed"

class AppointmentResponse(BaseModel):
    id: str
    userId: str
    userName: str
    userEmail: str
    date: str
    timeSlot: str
    status: str
    createdAt: str

class BreakRequest(BaseModel):
    fromTime: str
    toTime: str
    specificDate: Optional[str] = None  # null for daily breaks, date string for specific date breaks

# Define app before any usage
app = FastAPI(title="Fitness Tracker API", version="1.0.0")

# Add CORS middleware with iOS-specific headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=[
        "*",  # Allows all headers
        "X-Platform",
        "X-App-Version",
        "User-Agent",
        "Accept",
        "Connection",
        "Keep-Alive"
    ],
    expose_headers=[
        "X-Platform",
        "X-App-Version",
        "Content-Length",
        "Content-Type"
    ]
)

# Add middleware for iOS connection handling and logging
@app.middleware("http")
async def ios_connection_middleware(request, call_next):
    """Middleware to handle iOS connection issues and add logging"""
    import time
    start_time = time.time()
    
    # Log request details
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    platform = request.headers.get("x-platform", "unknown")
    
    logger.info(f"[REQUEST] {request.method} {request.url.path} from {client_ip} (Platform: {platform}, UA: {user_agent[:50]}...)")
    
    # Log frontend events from query parameters (for push notification debugging)
    if request.query_params:
        frontend_event = request.query_params.get('frontendEvent')
        if frontend_event:
            # Extract user ID from path if available
            path_parts = request.url.path.split('/')
            user_id = 'unknown'
            if 'users' in path_parts:
                try:
                    user_idx = path_parts.index('users')
                    if user_idx + 1 < len(path_parts):
                        user_id = path_parts[user_idx + 1][:15] + '...'
                except:
                    pass
            
            logger.info(f"[FRONTEND_EVENT] {frontend_event} - user: {user_id}")
            logger.info(f"[FRONTEND_EVENT] Details: {dict(request.query_params)}")
    
    try:
        # Add timeout handling for long-running requests
        import asyncio
        try:
            # Account deletion needs more time (90 seconds), other requests 30 seconds
            timeout = 90.0 if request.url.path.endswith("/account") and request.method == "DELETE" else 30.0
            response = await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            timeout_duration = 90.0 if request.url.path.endswith("/account") and request.method == "DELETE" else 30.0
            logger.error(f"[TIMEOUT] {request.method} {request.url.path} - Request timed out after {timeout_duration} seconds")
            return JSONResponse(
                status_code=408,
                content={"detail": "Request timeout. Please try again."}
            )
        
        # Log response details
        process_time = time.time() - start_time
        logger.info(f"[RESPONSE] {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        # Add iOS-specific headers for better connection handling
        response.headers["X-Platform"] = platform
        response.headers["X-Response-Time"] = f"{process_time:.3f}"
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=75, max=1000"
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[ERROR] {request.method} {request.url.path} - {str(e)} ({process_time:.3f}s)")
        
        # Return a proper error response instead of raising
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again."}
        )

# Define api_router before any usage
api_router = APIRouter(prefix='/api')

# Add a simple test endpoint to verify deployment
@api_router.get("/test-deployment")
async def test_deployment():
    """Test endpoint to verify backend deployment"""
    return {
        "message": "Backend deployment test successful",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.1",
        "ios_fixes": "applied"
    }

# Add a Firebase test endpoint
@api_router.get("/test-firebase")
async def test_firebase():
    """Test endpoint to verify Firebase connection"""
    try:
        check_firebase_availability()
        
        # Try a simple Firestore operation
        test_collection = firestore_db.collection("test")
        test_doc = test_collection.document("connection_test")
        
        # Just check if we can access the collection
        return {
            "message": "Firebase connection test successful",
            "firebase_available": True,
            "firestore_db_type": str(type(firestore_db)),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "message": "Firebase connection test failed",
            "firebase_available": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }

# Create a thread pool executor
executor = ThreadPoolExecutor(max_workers=10)

# Suppress specific Firestore warning about positional arguments
warnings.filterwarnings('ignore', message='Detected filter using positional arguments.*')

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / '.env'

# Add startup logging
print("🚀 Starting Nutricious4u Backend Server...")
print(f"📁 Current directory: {os.getcwd()}")
print(f"🔧 Environment file path: {env_path}")
print(f"📦 Environment file exists: {env_path.exists()}")

# Check critical environment variables (only show if missing)
critical_vars = ['GEMINI_API_KEY', 'FIREBASE_PROJECT_ID']
missing_vars = []
for var in critical_vars:
    value = os.getenv(var)
    if not value:
        missing_vars.append(var)

if missing_vars:
    print(f"⚠️  Missing environment variables: {missing_vars}")
else:
    print("✅ All critical environment variables are set")

# Vertex AI Gemini setup
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured")
else:
    print("⚠️  Gemini API key not found")

# Firebase is now handled automatically in the firebase_client.py
# No need for reinitialization since it has multiple fallback mechanisms

async def get_nutrition_from_gemini(food_name, quantity):
    if not GEMINI_API_KEY:
        return {'calories': 'Error', 'protein': 'Error', 'fat': 'Error'}
    food_name = str(food_name).strip()
    try:
        qty = float(quantity)
    except Exception:
        qty = quantity
    logger.info(f"[GEMINI PROMPT] food_name='{food_name}', quantity={qty}")
    prompt = (
        f"""
        You are a bot that gives us 3 comma separated numbers representing the calories, protein and fat in the following food item: name and serving size: {food_name}, {qty}. Under no circumstances include any other text or extra numbers nor ask any further questions. If you can't give an exact value then give an estimate but only give numbers in the desired format. Only if the food item doesn't exist will you say the word \"Error\" and that's it.
        """
    )
    logger.info(f"[GEMINI PROMPT STRING] {prompt}")
    try:
        model = GenerativeModel('gemini-2.5-flash')
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        raw = response.text.strip()
        logger.info(f"[GEMINI RAW RESPONSE - UNCHANGED] {raw}")
        logger.info(f"[GEMINI RAW RESPONSE] {raw}")
        if raw.strip().lower() == "error":
            logger.error(f"[GEMINI ERROR] Model returned 'Error' for prompt: {prompt}")
            return {'calories': 'Error', 'protein': 'Error', 'fat': 'Error', 'raw': raw}
        try:
            # Take number before first comma
            part1, rest = raw.split(',', 1)
            calories = float(part1.strip())
            # Take number before next comma
            part2, rest = rest.split(',', 1)
            protein = float(part2.strip())
            # The rest is the third number
            fat = float(rest.strip())
            return {'calories': calories, 'protein': protein, 'fat': fat, 'raw': raw}
        except Exception as e:
            logger.error(f"[GEMINI PARSE ERROR] Could not extract 3 numbers from: {raw}, error: {e}")
            # Log the raw response at ERROR level for debugging
            logger.error(f"[GEMINI RAW RESPONSE - PARSE FAIL] {raw}")
            return {'calories': 'Error', 'protein': 'Error', 'fat': 'Error', 'raw': raw}
    except Exception as e:
        logger.error(f"[GEMINI ERROR] Exception: {e}", exc_info=True)
        return {'calories': 'Error', 'protein': 'Error', 'fat': 'Error'}

async def get_workout_nutrition_from_gemini(workout_name, duration):
    if not GEMINI_API_KEY:
        return {'calories': 'Error'}
    workout_name = str(workout_name).strip()
    
    # Pass duration as-is to Gemini, regardless of whether it's numeric or not
    logger.info(f"[GEMINI WORKOUT PROMPT] workout_name='{workout_name}', duration={duration}")
    
    prompt = (
        f"""
        You are a bot that gives us a single number representing the calories burned in the following workout: name and duration: {workout_name}, {duration} minutes. Under no circumstances include any other text or extra numbers nor ask any further questions. If you can't give an exact value then give an estimate but only give a single number in the desired format. Only if the workout doesn't exist will you say the word "Error" and that's it.
        """
    )
    
    logger.info(f"[GEMINI WORKOUT PROMPT STRING] {prompt}")
    try:
        model = GenerativeModel('gemini-2.5-flash')
        # Add timeout to the Gemini API call
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt)),
            timeout=20.0  # 20 second timeout for Gemini API call
        )
        raw = response.text.strip()
        logger.info(f"[GEMINI WORKOUT RAW RESPONSE - UNCHANGED] {raw}")
        logger.info(f"[GEMINI WORKOUT RAW RESPONSE] {raw}")
        if raw.strip().lower() == "error":
            return {'calories': 'Error'}
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) != 1:
            logger.error(f"[GEMINI WORKOUT PARSE ERROR] Expected 1 value (calories), got: {raw}")
            return {'calories': 'Error'}
        try:
            calories = float(parts[0])
            return {'calories': calories}
        except Exception as e:
            logger.error(f"[GEMINI WORKOUT PARSE ERROR] Could not convert to float: {parts}, error: {e}")
            return {'calories': 'Error'}
    except asyncio.TimeoutError:
        logger.error(f"[GEMINI WORKOUT TIMEOUT] Gemini API call timed out for workout: {workout_name}")
        return {'calories': 'Error'}
    except Exception as e:
        logger.error(f"[GEMINI WORKOUT ERROR] Exception: {e}", exc_info=True)
        return {'calories': 'Error'}

async def call_gemini_vision(image_path: str):
    # Use Gemini Vision API to extract calories, protein, fat from the image
    model = GenerativeModel('gemini-2.5-flash')
    prompt = (
        "You are a bot that gives us 3 comma separated numbers representing the calories, protein and fat in the food shown in this photo. Under no circumstances include any other text or extra numbers nor ask any further questions. If you can't give an exact value then give an estimate but only give numbers in the desired format. Only if the food item doesn't exist or can't be recognized will you say the word 'Error' and that's it."
    )
    with open(image_path, 'rb') as img_file:
        image_bytes = img_file.read()
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content([
                {"mime_type": "image/jpeg", "data": image_bytes},
                prompt
            ])
        )
        raw = response.text.strip()
        if raw.strip().lower() == "error":
            return {"calories": "Error", "protein": "Error", "fat": "Error", "raw": raw}
        try:
            part1, rest = raw.split(',', 1)
            calories = float(part1.strip())
            part2, rest = rest.split(',', 1)
            protein = float(part2.strip())
            fat = float(rest.strip())
            return {"calories": calories, "protein": protein, "fat": fat, "raw": raw}
        except Exception as e:
            return {"calories": "Error", "protein": "Error", "fat": "Error", "raw": raw}
    except Exception as e:
        return {"calories": "Error", "protein": "Error", "fat": "Error", "raw": str(e)}

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Fitness Tracker API is running!"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    loop = asyncio.get_event_loop()
    try:
        status_dict = input.dict()
        status_obj = StatusCheck(**status_dict)
        await loop.run_in_executor(executor, lambda: firestore_db.collection("status_checks").add(status_obj.dict()))
        return status_obj
    except Exception as e:
        logger.error(f"Error creating status check: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create status check")

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    loop = asyncio.get_event_loop()
    try:
        docs_stream = await loop.run_in_executor(executor, lambda: firestore_db.collection("status_checks").stream())
        status_checks = [StatusCheck(**doc.to_dict()) for doc in docs_stream]
        return status_checks
    except Exception as e:
        logger.error(f"Error fetching status checks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch status checks")



@api_router.get("/food/nutrition")
async def get_food_nutrition(food_name: str, quantity: str = "100"):
    """Get nutrition data for a food item without logging it"""
    try:
        logger.info(f"[NUTRITION] Getting nutrition for: {food_name}, {quantity}")
        nutrition = await get_nutrition_from_gemini(food_name, quantity)
        logger.info(f"[NUTRITION] Gemini nutrition response: {nutrition}")
        
        food = FoodItem(
            name=food_name,
            calories=float(nutrition["calories"]) if nutrition["calories"] != "Error" else 0,
            protein=float(nutrition["protein"]) if nutrition["protein"] != "Error" else 0,
            fat=float(nutrition["fat"]) if nutrition["fat"] != "Error" else 0,
            per_100g=True
        )
        
        return {"food": food.dict(), "success": True}
    except Exception as e:
        logger.error(f"[NUTRITION] Error getting nutrition data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get nutrition data: {e}")

@api_router.post("/food/log", response_model=FoodLog)
async def log_food_item(request: FoodLogRequest):
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"[FOOD LOG] Incoming request: {request}")
        logger.info(f"[FOOD LOG] Request nutrition data - calories: {request.calories}, protein: {request.protein}, fat: {request.fat}")
        user_id = request.userId
        if not user_id:
            logger.error("[FOOD LOG] userId missing in request")
            raise HTTPException(status_code=400, detail="userId is required")
        
        # Check if daily reset is needed
        try:
            user_doc = firestore_db.collection("user_profiles").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                last_food_log_date = user_data.get("lastFoodLogDate")
                # Use user's timezone for daily reset if available
                if request.timezoneOffset is not None:
                    utc_time = datetime.utcnow()
                    user_local_time = utc_time - timedelta(minutes=request.timezoneOffset)
                    today = user_local_time.strftime('%Y-%m-%d')
                    logger.info(f"[FOOD LOG] Using user's local date for daily reset: UTC {utc_time} - {request.timezoneOffset}min = {user_local_time} -> {today}")
                else:
                    today = datetime.now().strftime('%Y-%m-%d')
                    logger.info(f"[FOOD LOG] Using server date for daily reset: {today}")
                
                if last_food_log_date != today:
                    logger.info(f"[FOOD LOG] Daily reset needed for user {user_id}. Last: {last_food_log_date}, Today: {today}")
                    # Reset daily data
                    await reset_daily_data(user_id)
        except Exception as reset_error:
            logger.warning(f"[FOOD LOG] Error checking daily reset: {reset_error}")
            # Continue with food logging even if reset fails
        
        # COMPREHENSIVE LOGGING: Trace every step of nutrition data handling
        logger.info(f"[FOOD LOG TRACE] 🔍 Starting nutrition data analysis...")
        logger.info(f"[FOOD LOG TRACE] - Food name: {request.foodName}")
        logger.info(f"[FOOD LOG TRACE] - Serving size: {request.servingSize}")
        logger.info(f"[FOOD LOG TRACE] - Provided calories: {request.calories}")
        logger.info(f"[FOOD LOG TRACE] - Provided protein: {request.protein}")
        logger.info(f"[FOOD LOG TRACE] - Provided fat: {request.fat}")
        
        # Use provided nutrition data if available, otherwise get from Gemini
        if request.calories is not None and request.protein is not None and request.fat is not None:
            logger.info(f"[FOOD LOG TRACE] ✅ Using provided nutrition data from frontend")
            logger.info(f"[FOOD LOG TRACE] - Raw calories value: {request.calories} (type: {type(request.calories)})")
            logger.info(f"[FOOD LOG TRACE] - Raw protein value: {request.protein} (type: {type(request.protein)})")
            logger.info(f"[FOOD LOG TRACE] - Raw fat value: {request.fat} (type: {type(request.fat)})")
            
            # CRITICAL FIX: Frontend provides TOTAL calories for the serving, not per-100g
            # We need to store these as total calories and set per_100g=False
            food = FoodItem(
                name=request.foodName,
                calories=request.calories,
                protein=request.protein,
                fat=request.fat,
                per_100g=False  # These are TOTAL calories for the serving, not per-100g
            )
            
            logger.info(f"[FOOD LOG TRACE] ✅ Created FoodItem with provided data (TOTAL calories):")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.calories: {food.calories} (TOTAL for serving)")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.protein: {food.protein} (TOTAL for serving)")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.fat: {food.fat} (TOTAL for serving)")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.per_100g: {food.per_100g} (FALSE = total calories)")
            
            nutrition = {"calories": request.calories, "protein": request.protein, "fat": request.fat, "raw": "provided"}
        else:
            logger.info(f"[FOOD LOG TRACE] ⚠️ No nutrition data provided, getting from Gemini")
            nutrition = await get_nutrition_from_gemini(request.foodName, request.servingSize)
            logger.info(f"[FOOD LOG TRACE] Gemini nutrition response: {nutrition}")
            food = FoodItem(
                name=request.foodName,
                calories=float(nutrition["calories"]) if nutrition["calories"] != "Error" else 0,
                protein=float(nutrition["protein"]) if nutrition["protein"] != "Error" else 0,
                fat=float(nutrition["fat"]) if nutrition["fat"] != "Error" else 0,
                per_100g=True
            )
            
            logger.info(f"[FOOD LOG TRACE] ✅ Created FoodItem from Gemini:")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.calories: {food.calories}")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.protein: {food.protein}")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.fat: {food.fat}")
            logger.info(f"[FOOD LOG TRACE] - FoodItem.per_100g: {food.per_100g}")
        log_entry = FoodLog(
            userId=user_id,
            food=food,
            servingSize=request.servingSize
        )
        def log_food_in_db():
            # CRITICAL FIX: Use user's local time by applying timezone offset correctly
            if request.timezoneOffset is not None:
                # JavaScript getTimezoneOffset() returns minutes to subtract from UTC to get local time
                # For PST: getTimezoneOffset() = 480 (UTC - 480 minutes = PST)
                # For EDT: getTimezoneOffset() = 240 (UTC - 240 minutes = EDT)
                utc_time = datetime.utcnow()
                local_time = utc_time - timedelta(minutes=request.timezoneOffset)
                log_entry.timestamp = local_time
                logger.info(f"[FOOD LOG] Using user's local time: UTC {utc_time} - {request.timezoneOffset}min = {log_entry.timestamp}")
            else:
                # Fallback to server time if no timezone provided
                log_entry.timestamp = datetime.now()
                logger.info(f"[FOOD LOG] Using server local time (no timezone provided): {log_entry.timestamp}")
                
            firestore_db.collection(f"users/{user_id}/food_logs").add(log_entry.dict())
            logger.info(f"[FOOD LOG] Written to Firestore: {log_entry.dict()}")
            
            # Delete food logs older than 7 days (using same time calculation)
            if request.timezoneOffset is not None:
                seven_days_ago = local_time - timedelta(days=7)
            else:
                seven_days_ago = datetime.now() - timedelta(days=7)
            old_logs_query = firestore_db.collection(f"users/{user_id}/food_logs").where("timestamp", "<", seven_days_ago)
            old_logs = list(old_logs_query.stream())
            for doc in old_logs:
                doc.reference.delete()
                logger.info(f"[FOOD LOG] Deleted old log: {doc.id}")
        await loop.run_in_executor(executor, log_food_in_db)
        logger.info(f"[FOOD LOG] Returning log entry: {log_entry}")
        # Always include the raw Gemini response in the API response for debugging
        return {**log_entry.dict(), 'raw_gemini_response': nutrition.get('raw', None)}
    except Exception as e:
        logger.error(f"[FOOD LOG] Error logging food for user {request.userId}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to log food: {e}")

@api_router.get("/food/log/summary/{user_id}", response_model=LogSummaryResponse)
async def get_food_log_summary(user_id: str):
    try:
        logger.info(f"[SUMMARY] Fetching summary for user: {user_id}")
        
        # Check if Firebase is available
        if not FIREBASE_AVAILABLE or firestore_db is None:
            logger.error("[SUMMARY] Firebase is not available, returning service unavailable")
            raise HTTPException(status_code=503, detail="Database service is currently unavailable. Please try again later.")
        
        # CRITICAL FIX: Use local time instead of UTC for consistent user experience
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=6)
        logger.info(f"[SUMMARY] Using local time - today: {today}, start_of_week: {start_of_week}")
        logs_ref = firestore_db.collection(f"users/{user_id}/food_logs")
        
        # Use datetime object for query, not isoformat string
        query = logs_ref.where("timestamp", ">=", start_of_week)
        docs_stream = query.stream()
        
        history = {}
        all_logs = []
        
        logger.info(f"[SUMMARY TRACE] 🔍 Processing {len(list(docs_stream))} documents...")
        docs_stream = query.stream()  # Re-create stream since we consumed it
        
        for doc_index, doc in enumerate(docs_stream):
            log = doc.to_dict()
            all_logs.append(log)
            
            logger.info(f"[SUMMARY TRACE] 📄 Document {doc_index + 1}:")
            logger.info(f"[SUMMARY TRACE] - Raw log data: {log}")
            
            if not log or not isinstance(log, dict):
                logger.warning(f"[SUMMARY TRACE] ⚠️ Skipping invalid log data")
                continue
                
            ts = log.get("timestamp")
            logger.info(f"[SUMMARY TRACE] - Timestamp: {ts} (type: {type(ts)})")
            
            # Firestore may return a datetime or a string
            if isinstance(ts, str):
                try:
                    log_date = datetime.fromisoformat(ts).strftime('%Y-%m-%d')
                    logger.info(f"[SUMMARY TRACE] - Parsed date from string: {log_date}")
                except Exception as e:
                    logger.warning(f"[SUMMARY TRACE] ⚠️ Failed to parse date from string: {e}")
                    continue
            elif isinstance(ts, datetime):
                log_date = ts.strftime('%Y-%m-%d')
                logger.info(f"[SUMMARY TRACE] - Parsed date from datetime: {log_date}")
            else:
                logger.warning(f"[SUMMARY TRACE] ⚠️ Unknown timestamp type: {type(ts)}")
                continue
                
            if log_date not in history:
                history[log_date] = {"calories": 0, "protein": 0, "fat": 0}
                logger.info(f"[SUMMARY TRACE] - Created new history entry for {log_date}")
            
            food_item = log.get("food")
            logger.info(f"[SUMMARY TRACE] - Food item data: {food_item}")
            
            if food_item is None or not isinstance(food_item, dict):
                logger.warning(f"[SUMMARY TRACE] ⚠️ Invalid food item data")
                food_item = {}
                
            serving_size = log.get("servingSize", "100")
            logger.info(f"[SUMMARY TRACE] - Serving size: {serving_size} (type: {type(serving_size)})")
            
            try:
                serving_size_num = float(serving_size)
                logger.info(f"[SUMMARY TRACE] - Parsed serving size: {serving_size_num}")
            except Exception as e:
                logger.warning(f"[SUMMARY TRACE] ⚠️ Failed to parse serving size, using 100: {e}")
                serving_size_num = 100
                
            calories = food_item.get("calories", 0)
            protein = food_item.get("protein", 0)
            fat = food_item.get("fat", 0)
            per_100g = food_item.get("per_100g", True)
            
            logger.info(f"[SUMMARY TRACE] - Raw nutrition from food_item:")
            logger.info(f"[SUMMARY TRACE]   * calories: {calories} (type: {type(calories)})")
            logger.info(f"[SUMMARY TRACE]   * protein: {protein} (type: {type(protein)})")
            logger.info(f"[SUMMARY TRACE]   * fat: {fat} (type: {type(fat)})")
            logger.info(f"[SUMMARY TRACE]   * per_100g: {per_100g}")
            
            # CRITICAL FIX: Handle both per-100g and total calories correctly
            if per_100g:
                # Old logic: calories are per 100g, multiply by serving size
                calories_contribution = (calories * serving_size_num) / 100
                protein_contribution = (protein * serving_size_num) / 100
                fat_contribution = (fat * serving_size_num) / 100
                logger.info(f"[SUMMARY TRACE] - Per-100g calculation: ({calories} * {serving_size_num}) / 100 = {calories_contribution}")
            else:
                # New logic: calories are total for the serving, use as-is
                calories_contribution = calories
                protein_contribution = protein
                fat_contribution = fat
                logger.info(f"[SUMMARY TRACE] - Total serving calculation: {calories} (used as-is) = {calories_contribution}")
            
            logger.info(f"[SUMMARY TRACE] - Final contributions:")
            logger.info(f"[SUMMARY TRACE]   * Calories: {calories_contribution}")
            logger.info(f"[SUMMARY TRACE]   * Protein: {protein_contribution}")
            logger.info(f"[SUMMARY TRACE]   * Fat: {fat_contribution}")
            
            # Add to history
            history[log_date]["calories"] += calories_contribution
            history[log_date]["protein"] += protein_contribution
            history[log_date]["fat"] += fat_contribution
            
            logger.info(f"[SUMMARY TRACE] - Updated totals for {log_date}:")
            logger.info(f"[SUMMARY TRACE]   * Total calories: {history[log_date]['calories']}")
            logger.info(f"[SUMMARY TRACE]   * Total protein: {history[log_date]['protein']}")
            logger.info(f"[SUMMARY TRACE]   * Total fat: {history[log_date]['fat']}")
            
        logger.info(f"[SUMMARY DEBUG] All logs fetched for user {user_id}: {all_logs}")
        today_str = today.strftime('%Y-%m-%d')
        if today_str not in history:
            history[today_str] = {"calories": 0, "protein": 0, "fat": 0}
        sorted_dates = sorted(history.keys(), reverse=True)
        formatted_history = [{"day": date, **history[date]} for date in sorted_dates]
        logger.info(f"[SUMMARY] Returning summary for user {user_id}: {formatted_history}")
        return LogSummaryResponse(history=formatted_history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SUMMARY] Error getting food log summary for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve summary.")

async def _get_food_log_summary_internal(user_id: str, loop):
    """Internal function to get food log summary with better error handling"""
    try:
        # CRITICAL FIX: Use local time consistently
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=6)
        logger.info(f"[SUMMARY INTERNAL] Using local time - today: {today}, start_of_week: {start_of_week}")
        logs_ref = firestore_db.collection(f"users/{user_id}/food_logs")
        
        # Use datetime object for query, not isoformat string
        query = logs_ref.where("timestamp", ">=", start_of_week)
        docs_stream = await loop.run_in_executor(executor, query.stream)
        
        history = {}
        all_logs = []
        
        for doc in docs_stream:
            log = doc.to_dict()
            all_logs.append(log)
            if not log or not isinstance(log, dict):
                continue
            ts = log.get("timestamp")
            # Firestore may return a datetime or a string
            if isinstance(ts, str):
                try:
                    log_date = datetime.fromisoformat(ts).strftime('%Y-%m-%d')
                except Exception:
                    continue
            elif isinstance(ts, datetime):
                log_date = ts.strftime('%Y-%m-%d')
            else:
                continue
            if log_date not in history:
                history[log_date] = {"calories": 0, "protein": 0, "fat": 0}
            food_item = log.get("food")
            if food_item is None or not isinstance(food_item, dict):
                food_item = {}
            serving_size = log.get("servingSize", "100")
            try:
                # Extract numeric value from serving size (e.g., "2 slices" -> 2)
                import re
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', str(serving_size))
                if numeric_match:
                    serving_size_num = float(numeric_match.group(1))
                else:
                    serving_size_num = 100
            except Exception:
                serving_size_num = 100
            calories = food_item.get("calories", 0)
            protein = food_item.get("protein", 0)
            fat = food_item.get("fat", 0)
            per_100g = food_item.get("per_100g", True)
            
            # If per_100g is True, apply serving size multiplier
            # If per_100g is False, values are already calculated for the serving
            if per_100g:
                calculated_calories = (calories * serving_size_num) / 100
                calculated_protein = (protein * serving_size_num) / 100
                calculated_fat = (fat * serving_size_num) / 100
            else:
                calculated_calories = calories
                calculated_protein = protein
                calculated_fat = fat
            
            logger.info(f"[SUMMARY DEBUG] Processing log for {log_date}:")
            logger.info(f"[SUMMARY DEBUG] - Food: {food_item.get('name', 'Unknown')}")
            logger.info(f"[SUMMARY DEBUG] - Serving size: {serving_size_num}g")
            logger.info(f"[SUMMARY DEBUG] - Per 100g: {per_100g}")
            logger.info(f"[SUMMARY DEBUG] - Raw calories: {calories}")
            logger.info(f"[SUMMARY DEBUG] - Raw protein: {protein}")
            logger.info(f"[SUMMARY DEBUG] - Raw fat: {fat}")
            logger.info(f"[SUMMARY DEBUG] - Calculated calories: {calculated_calories}")
            logger.info(f"[SUMMARY DEBUG] - Calculated protein: {calculated_protein}")
            logger.info(f"[SUMMARY DEBUG] - Calculated fat: {calculated_fat}")
            
            history[log_date]["calories"] += calculated_calories
            history[log_date]["protein"] += calculated_protein
            history[log_date]["fat"] += calculated_fat
            
            logger.info(f"[SUMMARY DEBUG] - Running totals for {log_date}: calories={history[log_date]['calories']}, protein={history[log_date]['protein']}, fat={history[log_date]['fat']}")
            
        logger.info(f"[SUMMARY DEBUG] All logs fetched for user {user_id}: {all_logs}")
        
        # Ensure we have data for all 7 days, even if some days have no food logs
        # Generate the same 7 days that the frontend expects (6 days ago to today)
        for i in range(6, -1, -1):  # 6 days ago to today (matches frontend logic)
            day_date = today - timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')
            if day_str not in history:
                history[day_str] = {"calories": 0, "protein": 0, "fat": 0}
        
        logger.info(f"[SUMMARY] Generated date range for last 7 days ending {today.strftime('%Y-%m-%d')}")
        
        # Sort dates in descending order (most recent first)
        sorted_dates = sorted(history.keys(), reverse=True)
        formatted_history = [{"day": date, **history[date]} for date in sorted_dates]
        # Enhanced logging for debugging tracker issues
        logger.info(f"[SUMMARY] 📊 Returning summary for user {user_id}")
        logger.info(f"[SUMMARY] Total days in history: {len(formatted_history)}")
        logger.info(f"[SUMMARY] Date order: {[item['day'] for item in formatted_history]}")
        logger.info(f"[SUMMARY] Today's date (backend): {today.strftime('%Y-%m-%d')}")
        
        # Log today's specific data for debugging
        today_str = today.strftime('%Y-%m-%d')
        today_data_in_history = next((item for item in formatted_history if item['day'] == today_str), None)
        
        logger.info(f"[SUMMARY] Today's data in response: {today_data_in_history}")
        
        # Log all history data for debugging
        for item in formatted_history:
            logger.info(f"[SUMMARY] Date {item['day']}: calories={item['calories']}, protein={item['protein']}, fat={item['fat']}")
        
        return LogSummaryResponse(history=formatted_history)
        
    except Exception as e:
        logger.error(f"[SUMMARY INTERNAL] Error in internal function for user {user_id}: {e}")
        raise

@api_router.get("/workout/search", response_model=WorkoutSearchResponse)
async def search_workouts(query: str = Query(..., min_length=1)):
    """Search for workout exercises"""
    try:
        # Mock workout data
        mock_workouts = [
            WorkoutItem(id=1, name="Running", calories_per_minute=10, type="cardio"),
            WorkoutItem(id=2, name="Walking", calories_per_minute=5, type="cardio"),
            WorkoutItem(id=3, name="Cycling", calories_per_minute=8, type="cardio"),
            WorkoutItem(id=4, name="Swimming", calories_per_minute=12, type="cardio"),
            WorkoutItem(id=5, name="Push-ups", calories_per_minute=7, type="strength"),
            WorkoutItem(id=6, name="Pull-ups", calories_per_minute=8, type="strength"),
            WorkoutItem(id=7, name="Squats", calories_per_minute=6, type="strength"),
            WorkoutItem(id=8, name="Deadlifts", calories_per_minute=9, type="strength"),
            WorkoutItem(id=9, name="Yoga", calories_per_minute=3, type="flexibility"),
            WorkoutItem(id=10, name="Pilates", calories_per_minute=4, type="flexibility"),
            WorkoutItem(id=11, name="Jumping Jacks", calories_per_minute=8, type="cardio"),
            WorkoutItem(id=12, name="Burpees", calories_per_minute=12, type="strength"),
        ]
        
        # Filter workouts based on search query
        filtered_workouts = [
            workout for workout in mock_workouts 
            if query.lower() in workout.name.lower()
        ]
        
        return WorkoutSearchResponse(exercises=filtered_workouts)
        
    except Exception as e:
        logger.error(f"Error searching for workout: {e}")
        raise HTTPException(status_code=500, detail="Failed to search for workout.")

@api_router.get("/workout/log/summary/{user_id}", response_model=LogSummaryResponse)
async def get_workout_log_summary(user_id: str):
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"[WORKOUT SUMMARY] Fetching workout summary for user: {user_id}")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=6)
        logs_ref = firestore_db.collection("workout_logs")
        # Only logs for this user and in the last 7 days
        query = logs_ref.where("userId", "==", user_id).where("date", ">=", start_of_week.isoformat())
        docs_stream = await loop.run_in_executor(executor, query.stream)
        history = {}
        all_logs = []
        for doc in docs_stream:
            log = doc.to_dict()
            if not log or not isinstance(log, dict):
                continue
            all_logs.append(log)
            ts = log.get("date")
            # Firestore may return a datetime or a string
            if isinstance(ts, str):
                try:
                    log_date = datetime.fromisoformat(ts).strftime('%Y-%m-%d')
                except Exception:
                    continue
            elif isinstance(ts, datetime):
                log_date = ts.strftime('%Y-%m-%d')
            else:
                continue
            if log_date not in history:
                history[log_date] = {"calories": 0}
            calories = log.get("calories", 0)
            try:
                calories = float(calories)
            except Exception:
                calories = 0
            history[log_date]["calories"] += calories
        logger.info(f"[WORKOUT SUMMARY DEBUG] All workout logs fetched for user {user_id}: {all_logs}")
        today_str = today.strftime('%Y-%m-%d')
        if today_str not in history:
            history[today_str] = {"calories": 0}
        sorted_dates = sorted(history.keys(), reverse=True)
        formatted_history = [{"day": date, **history[date]} for date in sorted_dates]
        logger.info(f"[WORKOUT SUMMARY] Returning summary for user {user_id}: {formatted_history}")
        return LogSummaryResponse(history=formatted_history)
    except Exception as e:
        logger.error(f"[WORKOUT SUMMARY] Error getting workout log summary for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve workout summary.")

# User Profile Endpoints
@api_router.post("/users/profile", response_model=UserProfile)
async def create_user_profile(profile: UserProfile):
    """Create a new user profile."""
    check_firebase_availability()
    loop = asyncio.get_event_loop()
    try:
        profile_dict = profile.dict()
        user_id = profile_dict.get("userId")
        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")

        # Prevent creating placeholder profiles
        is_placeholder = (
            profile_dict.get("firstName", "User") == "User" and
            profile_dict.get("lastName", "") == "" and
            (not profile_dict.get("email") or profile_dict.get("email", "").endswith("@example.com"))
        )
        if is_placeholder:
            logger.warning(f"Attempted to create placeholder profile for user {user_id}: {profile_dict}")
            raise HTTPException(status_code=400, detail="Cannot create placeholder user profile.")

        doc_ref = firestore_db.collection("user_profiles").document(user_id)
        doc = await loop.run_in_executor(executor, doc_ref.get)

        if doc.exists:
            return doc.to_dict()

        # Add isDietician field based on email
        if profile_dict.get("email") == "nutricious4u@gmail.com":
            profile_dict["isDietician"] = True
        else:
            profile_dict["isDietician"] = False
        
        # Default new users to free plan
        if not profile_dict.get("isDietician"):
            profile_dict["subscriptionPlan"] = "free"
            profile_dict["isSubscriptionActive"] = False
            profile_dict["subscriptionStartDate"] = None
            profile_dict["subscriptionEndDate"] = None
            profile_dict["currentSubscriptionAmount"] = 0.0
            profile_dict["totalAmountPaid"] = 0.0
            profile_dict["autoRenewalEnabled"] = True
            # New subscription system fields
            profile_dict["freeTrialUsed"] = False
            profile_dict["freeTrialStartDate"] = None
            profile_dict["freeTrialEndDate"] = None
            profile_dict["pendingPlanSwitch"] = None
            profile_dict["nextPlanId"] = None
            profile_dict["subscriptionStatus"] = "expired"
            profile_dict["lastPaymentReminderSent"] = {
                "oneWeek": False,
                "twoDays": False,
                "oneDay": False
            }
        
        # Set new_diet_received to false for all new users
        profile_dict["new_diet_received"] = False
        
        await loop.run_in_executor(executor, lambda: doc_ref.set(profile_dict))
        logger.info(f"Created profile for user {user_id} with isDietician={profile_dict.get('isDietician')}")
        return profile_dict
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user profile.")

@api_router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get a user's profile."""
    logger.info(f"[PROFILE_FETCH] Starting profile fetch for user_id: {user_id}")
    
    # Check if Firebase is available
    if not FIREBASE_AVAILABLE or firestore_db is None:
        logger.error("[PROFILE_FETCH] Firebase is not available, returning service unavailable")
        raise HTTPException(status_code=503, detail="Database service is currently unavailable. Please try again later.")
    
    try:
        # Simplified version without timeout handling first
        logger.info(f"[PROFILE_FETCH] Querying Firestore for user_id: {user_id}")
        
        # Create document reference
        doc_ref = firestore_db.collection("user_profiles").document(user_id)
        
        # Execute the query
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"[PROFILE_FETCH] No profile found for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary
        profile = doc.to_dict()
        
        if profile is None:
            logger.warning(f"[PROFILE_FETCH] Profile is None for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        logger.info(f"[PROFILE_FETCH] Profile found for user_id: {user_id}, firstName: {profile.get('firstName', 'N/A')}")
        
        # Filter out placeholder profiles
        is_placeholder = (
            profile.get("firstName", "User") == "User" and
            profile.get("lastName", "") == "" and
            (not profile.get("email") or profile.get("email", "").endswith("@example.com"))
        )
        if is_placeholder:
            logger.warning(f"[PROFILE_FETCH] Filtered out placeholder profile for user {user_id}: {profile}")
            raise HTTPException(status_code=404, detail="User profile not found (placeholder)")
        
        logger.info(f"[PROFILE_FETCH] Successfully returning profile for user_id: {user_id}")
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PROFILE_FETCH] Error getting user profile for user_id {user_id}: {e}")
        logger.error(f"[PROFILE_FETCH] Error type: {type(e).__name__}")
        import traceback
        logger.error(f"[PROFILE_FETCH] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

async def _get_user_profile_internal(user_id: str, loop):
    """Internal function to get user profile with better error handling"""
    try:
        logger.info(f"[PROFILE_FETCH] Querying Firestore for user_id: {user_id}")
        
        # Check if firestore_db is available
        if firestore_db is None:
            logger.error("[PROFILE_FETCH] Firestore database is not initialized")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Create document reference
        doc_ref = firestore_db.collection("user_profiles").document(user_id)
        
        # Execute the query with better error handling
        try:
            doc = await loop.run_in_executor(executor, doc_ref.get)
        except Exception as firestore_error:
            logger.error(f"[PROFILE_FETCH] Firestore query failed for user {user_id}: {firestore_error}")
            logger.error(f"[PROFILE_FETCH] Firestore error type: {type(firestore_error).__name__}")
            raise HTTPException(status_code=503, detail="Database query failed")
        
        if not doc.exists:
            logger.warning(f"[PROFILE_FETCH] No profile found for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary with error handling
        try:
            profile = doc.to_dict()
        except Exception as dict_error:
            logger.error(f"[PROFILE_FETCH] Failed to convert document to dict for user {user_id}: {dict_error}")
            raise HTTPException(status_code=500, detail="Failed to process user profile")
        
        if profile is None:
            logger.warning(f"[PROFILE_FETCH] Profile is None for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        logger.info(f"[PROFILE_FETCH] Profile found for user_id: {user_id}, firstName: {profile.get('firstName', 'N/A')}")
        
        # Filter out placeholder profiles
        is_placeholder = (
            profile.get("firstName", "User") == "User" and
            profile.get("lastName", "") == "" and
            (not profile.get("email") or profile.get("email", "").endswith("@example.com"))
        )
        if is_placeholder:
            logger.warning(f"[PROFILE_FETCH] Filtered out placeholder profile for user {user_id}: {profile}")
            raise HTTPException(status_code=404, detail="User profile not found (placeholder)")
        
        logger.info(f"[PROFILE_FETCH] Successfully returning profile for user_id: {user_id}")
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PROFILE_FETCH INTERNAL] Unexpected error in internal function for user {user_id}: {e}")
        logger.error(f"[PROFILE_FETCH INTERNAL] Error type: {type(e).__name__}")
        import traceback
        logger.error(f"[PROFILE_FETCH INTERNAL] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.patch("/users/{user_id}/profile", response_model=UserProfile)
async def update_user_profile(user_id: str, profile_update: UpdateUserProfile):
    """Update a user's profile. If not found, create it with defaults."""
    check_firebase_availability()
    loop = asyncio.get_event_loop()
    try:
        update_dict = profile_update.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid update fields provided")
        doc_ref = await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id))
        doc = await loop.run_in_executor(executor, doc_ref.get)
        # Default values for required fields
        defaults = {
            "userId": user_id,
            "firstName": update_dict.get("firstName", "User"),
            "lastName": update_dict.get("lastName", ""),
            "age": update_dict.get("age", 18),
            "gender": update_dict.get("gender", "other"),
            "email": update_dict.get("email", f"{user_id}@example.com"),
            "currentWeight": update_dict.get("currentWeight", 60),
            "goalWeight": update_dict.get("goalWeight", 60),
            "height": update_dict.get("height", 170),
            "dietaryPreference": update_dict.get("dietaryPreference", "other"),
            "favouriteCuisine": update_dict.get("favouriteCuisine", ""),
            "allergies": update_dict.get("allergies", ""),
            "medicalConditions": update_dict.get("medicalConditions", ""),
            "activityLevel": update_dict.get("activityLevel", "sedentary"),
            "targetCalories": update_dict.get("targetCalories", 2000),
            "targetProtein": update_dict.get("targetProtein", 100),
            "targetFat": update_dict.get("targetFat", 60),
            "stepGoal": update_dict.get("stepGoal", 10000),
            "caloriesBurnedGoal": update_dict.get("caloriesBurnedGoal", 2000),
            # Diet fields with defaults
            "dietPdfUrl": update_dict.get("dietPdfUrl"),
            "lastDietUpload": update_dict.get("lastDietUpload"),
            "dieticianId": update_dict.get("dieticianId"),
            "dietCacheVersion": update_dict.get("dietCacheVersion"),
        }
        if not doc.exists:
            # Create new profile with defaults and any provided updates
            await loop.run_in_executor(executor, lambda: doc_ref.set(defaults))
            logger.info(f"Created profile for user {user_id} via PATCH")
            return defaults
        # If profile exists, update with provided fields (fill missing with defaults if needed)
        await loop.run_in_executor(executor, lambda: doc_ref.update(update_dict))
        updated_doc = await loop.run_in_executor(executor, doc_ref.get)
        profile = updated_doc.to_dict()
        if profile is None:
            profile = {}
        # Fill any missing required fields with defaults (but preserve diet fields)
        for k, v in defaults.items():
            if profile.get(k) is None:
                profile[k] = v
        
        # Ensure diet fields are preserved from the update
        if "dietPdfUrl" in update_dict:
            profile["dietPdfUrl"] = update_dict["dietPdfUrl"]
        if "lastDietUpload" in update_dict:
            profile["lastDietUpload"] = update_dict["lastDietUpload"]
        if "dieticianId" in update_dict:
            profile["dieticianId"] = update_dict["dieticianId"]
        if "dietCacheVersion" in update_dict:
            profile["dietCacheVersion"] = update_dict["dietCacheVersion"]
        return profile
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@api_router.post("/workout/log")
async def log_workout_item(log: dict):
    loop = asyncio.get_event_loop()
    try:
        user_id = log.get("userId")
        exercise_id = log.get("exerciseId")
        exercise_name = log.get("exerciseName")
        wtype = log.get("type")
        duration = log.get("duration")
        sets = log.get("sets")
        reps = log.get("reps")
        date = log.get("date")
        if not user_id or not exercise_id or not exercise_name or not wtype:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Handle non-numeric duration values
        original_duration = duration
        try:
            # Try to validate duration is numeric, but don't fail if it's not
            if duration is not None:
                float(duration)
        except (ValueError, TypeError):
            # Duration is not numeric, but we'll still process it
            logger.warning(f"Non-numeric duration received: {duration} for exercise: {exercise_name}")
        
        # Use Gemini to get calories/protein/fat burned with timeout
        try:
            nutrition = await asyncio.wait_for(
                get_workout_nutrition_from_gemini(exercise_name, duration),
                timeout=25.0  # 25 second timeout for Gemini API
            )
        except asyncio.TimeoutError:
            logger.error(f"Gemini API timeout for workout: {exercise_name}")
            # Fallback to a default calculation
            nutrition = {"calories": 100}  # Default fallback
        
        entry = {
            "userId": user_id,
            "exerciseId": exercise_id,
            "exerciseName": exercise_name,
            "type": wtype,
            "duration": original_duration,  # Store the original duration value
            "sets": sets,
            "reps": reps,
            "date": date or datetime.now().isoformat(),
            "calories": nutrition["calories"],
            "protein": 0, # No protein/fat burned in this simplified model
            "fat": 0 # No protein/fat burned in this simplified model
        }
        await loop.run_in_executor(executor, lambda: firestore_db.collection("workout_logs").add(entry))
        return entry
    except Exception as e:
        logger.error(f"Error logging workout: {e}")
        raise HTTPException(status_code=500, detail="Failed to log workout item.")

@api_router.post("/chatbot/message", response_model=ChatMessageResponse)
async def chatbot_message(request: ChatMessageRequest):
    """
    Accepts chat history, user profile, and user message. Returns Gemini's response.
    Now includes RAG functionality to read and understand the user's diet PDF.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured on server.")
    try:
        # Build system prompt with user profile
        profile = request.user_profile or {}
        system_prompt = (
            "You are NutriBot, a cautious and helpful nutrition assistant. "
            "You provide diet and nutrition advice based on the user's profile. "
            "Never give medical advice, and always recommend consulting a healthcare professional for medical concerns. "
            "If you are unsure, say so.\n"
        )
        if profile:
            system_prompt += "\nUser Profile:\n"
            for k, v in profile.items():
                if v:
                    system_prompt += f"{k}: {v}\n"
        system_prompt += '\nNever change or update user information. Only use it for context.'

        # Enhance prompt with diet PDF context using RAG
        diet_pdf_url = profile.get("dietPdfUrl") if profile else None
        if diet_pdf_url:
            try:
                system_prompt = pdf_rag_service.enhance_chatbot_prompt(
                    request.userId, 
                    diet_pdf_url, 
                    firestore_db, 
                    system_prompt
                )
                logger.info(f"[CHATBOT] Enhanced prompt with diet PDF for user {request.userId}")
            except Exception as e:
                logger.warning(f"[CHATBOT] Failed to enhance prompt with diet PDF: {e}")
                # Continue with original prompt if RAG enhancement fails

        # Format chat history for Gemini using dicts (SDK may accept these directly)
        # If the SDK requires Content objects, you may need to convert them here.
        formatted_history = [
            {"role": "user", "parts": [{"text": system_prompt}]}
        ]
        for msg in request.chat_history:
            role = msg.get("sender")
            text = msg.get("text")
            if not text:
                continue
            if role == "user":
                formatted_history.append({"role": "user", "parts": [{"text": text}]})
            elif role == "bot":
                formatted_history.append({"role": "model", "parts": [{"text": text}]})
        # Add the latest user message
        formatted_history.append({"role": "user", "parts": [{"text": request.user_message}]})
        # If the SDK requires Content objects, convert here (example):
        # formatted_history = [genai.Content(**msg) for msg in formatted_history]

        # Call Gemini
        model = GenerativeModel('gemini-2.5-flash')
        def get_response():
            content_history = [ContentDict(**msg) for msg in formatted_history]
            chat = model.start_chat(history=content_history)
            return chat.send_message(request.user_message)
        response = await asyncio.get_event_loop().run_in_executor(None, get_response)
        bot_text = response.text if hasattr(response, 'text') else str(response)
        return ChatMessageResponse(bot_message=bot_text)
    except Exception as e:
        logger.error(f"[CHATBOT] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get chatbot response: {e}")

# --- Routine Models ---
class RoutineItem(BaseModel):
    type: str  # 'food' or 'workout'
    name: str
    quantity: Optional[str] = None  # For food: serving size; for workout: duration
    # Optionally, add more fields as needed

class Routine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    items: List[RoutineItem]
    calories: float = 0
    protein: float = 0
    fat: float = 0
    burned: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RoutineCreateRequest(BaseModel):
    name: str
    items: List[RoutineItem]

class RoutineUpdateRequest(BaseModel):
    name: Optional[str] = None
    items: Optional[List[RoutineItem]] = None

# --- Routine Endpoints ---
@api_router.get("/users/{user_id}/routines", response_model=List[Routine])
async def list_routines(user_id: str):
    loop = asyncio.get_event_loop()
    try:
        routines_ref = firestore_db.collection(f"users/{user_id}/routines")
        docs = await loop.run_in_executor(executor, lambda: list(routines_ref.stream()))
        routines = []
        for doc in docs:
            data = doc.to_dict()
            if not data:
                continue  # Skip if data is None
            # Convert items to RoutineItem objects if needed
            items = [RoutineItem(**item) if isinstance(item, dict) else item for item in data.get("items", [])]
            routines.append(Routine(
                id=data.get("id", doc.id),
                name=data["name"],
                items=items,
                calories=data.get("calories", 0),
                protein=data.get("protein", 0),
                fat=data.get("fat", 0),
                burned=data.get("burned", 0),
                created_at=data.get("created_at", datetime.utcnow()),
                updated_at=data.get("updated_at", datetime.utcnow())
            ))
        return routines
    except Exception as e:
        logger.error(f"Error listing routines: {e}")
        raise HTTPException(status_code=500, detail="Failed to list routines")

@api_router.post("/users/{user_id}/routines", response_model=Routine)
async def create_routine(user_id: str, req: RoutineCreateRequest):
    loop = asyncio.get_event_loop()
    try:
        # Calculate nutrition for the routine using Gemini
        calories, protein, fat, burned = 0, 0, 0, 0
        for item in req.items:
            if item.type == 'food':
                nutrition = await get_nutrition_from_gemini(item.name, item.quantity or "100")
                if nutrition["calories"] != "Error":
                    calories += float(nutrition["calories"])
                if nutrition["protein"] != "Error":
                    protein += float(nutrition["protein"])
                if nutrition["fat"] != "Error":
                    fat += float(nutrition["fat"])
            elif item.type == 'workout':
                workout_nutrition = await get_workout_nutrition_from_gemini(item.name, item.quantity or "30")
                if workout_nutrition["calories"] != "Error":
                    burned += float(workout_nutrition["calories"])
        routine = Routine(
            name=req.name,
            items=req.items,
            calories=calories,
            protein=protein,
            fat=fat,
            burned=burned
        )
        routines_ref = firestore_db.collection(f"users/{user_id}/routines")
        await loop.run_in_executor(executor, lambda: routines_ref.document(routine.id).set(routine.dict()))
        return routine
    except Exception as e:
        logger.error(f"Error creating routine: {e}")
        raise HTTPException(status_code=500, detail="Failed to create routine")

@api_router.patch("/users/{user_id}/routines/{routine_id}", response_model=Routine)
async def update_routine(user_id: str, routine_id: str, req: RoutineUpdateRequest):
    loop = asyncio.get_event_loop()
    try:
        routines_ref = firestore_db.collection(f"users/{user_id}/routines")
        doc_ref = routines_ref.document(routine_id)
        doc = await loop.run_in_executor(executor, doc_ref.get)
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Routine not found")
        routine_data = doc.to_dict()
        if not routine_data:
            raise HTTPException(status_code=404, detail="Routine not found")
        # Convert items to RoutineItem objects if needed
        current_items = [RoutineItem(**item) if isinstance(item, dict) else item for item in routine_data.get("items", [])]
        # Update fields
        name = req.name if req.name is not None else routine_data["name"]
        items = [RoutineItem(**item) if isinstance(item, dict) else item for item in req.items] if req.items is not None else current_items
        # Recalculate nutrition
        calories, protein, fat, burned = 0, 0, 0, 0
        for item in items:
            if item.type == 'food':
                nutrition = await get_nutrition_from_gemini(item.name, item.quantity or "100")
                if nutrition["calories"] != "Error":
                    calories += float(nutrition["calories"])
                if nutrition["protein"] != "Error":
                    protein += float(nutrition["protein"])
                if nutrition["fat"] != "Error":
                    fat += float(nutrition["fat"])
            elif item.type == 'workout':
                workout_nutrition = await get_workout_nutrition_from_gemini(item.name, item.quantity or "30")
                if workout_nutrition["calories"] != "Error":
                    burned += float(workout_nutrition["calories"])
        updated = {
            "name": name,
            "items": [item.dict() for item in items],
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "burned": burned,
            "updated_at": datetime.utcnow()
        }
        await loop.run_in_executor(executor, lambda: doc_ref.update(updated))
        doc = await loop.run_in_executor(executor, doc_ref.get)
        data = doc.to_dict()
        if not data:
            raise HTTPException(status_code=404, detail="Routine not found")
        items = [RoutineItem(**item) if isinstance(item, dict) else item for item in data.get("items", [])]
        return Routine(
            id=data.get("id", doc.id),
            name=data["name"],
            items=items,
            calories=data.get("calories", 0),
            protein=data.get("protein", 0),
            fat=data.get("fat", 0),
            burned=data.get("burned", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )
    except Exception as e:
        logger.error(f"Error updating routine: {e}")
        raise HTTPException(status_code=500, detail="Failed to update routine")

@api_router.delete("/users/{user_id}/routines/{routine_id}")
async def delete_routine(user_id: str, routine_id: str):
    loop = asyncio.get_event_loop()
    try:
        routines_ref = firestore_db.collection(f"users/{user_id}/routines")
        doc_ref = routines_ref.document(routine_id)
        await loop.run_in_executor(executor, lambda: doc_ref.delete())
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting routine: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete routine")

@api_router.post("/users/{user_id}/routines/{routine_id}/log")
async def log_routine(user_id: str, routine_id: str):
    loop = asyncio.get_event_loop()
    try:
        routines_ref = firestore_db.collection(f"users/{user_id}/routines")
        doc_ref = routines_ref.document(routine_id)
        doc = await loop.run_in_executor(executor, doc_ref.get)
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Routine not found")
        routine = doc.to_dict()
        if routine is None:
            raise HTTPException(status_code=404, detail="Routine not found")
        # Convert to Routine model for attribute access
        routine_obj = Routine(**routine)
        # Convert items to RoutineItem objects if needed
        items = [RoutineItem(**item) if isinstance(item, dict) else item for item in routine_obj.items]
        now = datetime.utcnow()
        # Calculate per-item nutrition from routine (split by type)
        food_items = [item for item in items if item.type == 'food']
        workout_items = [item for item in items if item.type == 'workout']
        n_food = len(food_items) if len(food_items) > 0 else 1
        n_workout = len(workout_items) if len(workout_items) > 0 else 1
        # Log food
        for item in food_items:
            food_log = {
                "userId": user_id,
                "food": {
                    "name": item.name,
                    "calories": float(routine_obj.calories) / n_food,
                    "protein": float(routine_obj.protein) / n_food,
                    "fat": float(routine_obj.fat) / n_food,
                    "per_100g": True
                },
                "servingSize": item.quantity or "100",
                "timestamp": now
            }
            firestore_db.collection(f"users/{user_id}/food_logs").add(food_log)
        # Log workout
        for item in workout_items:
            workout_log = {
                "userId": user_id,
                "exerciseId": "routine",
                "exerciseName": item.name,
                "type": "routine",
                "duration": item.quantity or "30",
                "sets": None,
                "reps": None,
                "date": now.isoformat(),
                "calories": float(routine_obj.burned) / n_workout
            }
            firestore_db.collection("workout_logs").add(workout_log)
        # Delete food logs older than 7 days
        seven_days_ago = now - timedelta(days=7)
        food_logs_ref = firestore_db.collection(f"users/{user_id}/food_logs")
        old_food_logs = list(food_logs_ref.where("timestamp", "<", seven_days_ago).stream())
        for doc in old_food_logs:
            doc.reference.delete()
        # Delete workout logs older than 7 days
        workout_logs_ref = firestore_db.collection("workout_logs")
        old_workout_logs = list(workout_logs_ref.where("userId", "==", user_id).where("date", "<", (now - timedelta(days=7)).isoformat()).stream())
        for doc in old_workout_logs:
            doc.reference.delete()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error logging routine: {e}")
        raise HTTPException(status_code=500, detail="Failed to log routine")

# --- Diet PDF Upload Endpoint (Dietician Only) ---
@api_router.post("/users/{user_id}/diet/upload")
async def upload_user_diet_pdf(user_id: str, file: UploadFile = File(...), dietician_id: str = Form(...)):
    """
    Dietician uploads a new diet PDF for a user. Replaces previous diet, updates timestamp, and returns the new URL.
    """
    logger.info(f"[DIET UPLOAD] ===== DIET UPLOAD STARTED =====")
    logger.info(f"[DIET UPLOAD] user_id: {user_id}")
    logger.info(f"[DIET UPLOAD] dietician_id: {dietician_id}")
    logger.info(f"[DIET UPLOAD] file: {file}")
    logger.info(f"[DIET UPLOAD] file.filename: {file.filename if file else 'None'}")
    logger.info(f"[DIET UPLOAD] file.size: {file.size if file else 'None'}")
    
    try:
        logger.info(f"[DIET UPLOAD] Starting diet upload for user {user_id} by dietician {dietician_id}")
        logger.info(f"[DIET UPLOAD] File: {file.filename}, Size: {file.size} bytes")
        print(f"Starting diet upload for user {user_id} by dietician {dietician_id}")
        print(f"File: {file.filename}, Size: {file.size} bytes")
        
        # Read file data
        file_data = await file.read()
        logger.info(f"[DIET UPLOAD] Read {len(file_data)} bytes from file")
        print(f"Read {len(file_data)} bytes from file")
        
        # Upload to Firebase Storage
        logger.info(f"[DIET UPLOAD] Calling upload_diet_pdf with user_id={user_id}, filename={file.filename}")
        print(f"Calling upload_diet_pdf with user_id={user_id}, filename={file.filename}")
        pdf_url = upload_diet_pdf(user_id, file_data, file.filename)
        logger.info(f"[DIET UPLOAD] Upload completed. PDF URL: {pdf_url}")
        print(f"Upload completed. PDF URL: {pdf_url}")
        
        # Store the filename in Firestore instead of the signed URL (which expires)
        # The signed URL will be generated when needed by the PDF serving endpoint
        # Use timezone-aware datetime for consistent calculation
        from datetime import timezone
        diet_info = {
            "dietPdfUrl": file.filename,  # Store filename, not signed URL
            "lastDietUpload": datetime.now(timezone.utc).isoformat(),
            "dieticianId": dietician_id,
            "dietCacheVersion": datetime.now(timezone.utc).timestamp()  # Cache busting flag
        }
        
        print(f"Updating Firestore with diet info: {diet_info}")
        print(f"[Upload Debug] lastDietUpload timestamp: {diet_info['lastDietUpload']}")
        print(f"[Upload Debug] cache version: {diet_info['dietCacheVersion']}")
        try:
            # Use executor for Firestore operations
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                # Update the document
                await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id).update(diet_info))
                print(f"Successfully updated Firestore for user {user_id}")
                
                # Verify the update with retry mechanism
                max_retries = 3
                for attempt in range(max_retries):
                    await asyncio.sleep(0.5)  # Wait for update to propagate
                    updated_doc = await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id).get())
                    if updated_doc.exists:
                        updated_data = updated_doc.to_dict()
                        diet_pdf_url = updated_data.get('dietPdfUrl')
                        cache_version = updated_data.get('dietCacheVersion')
                        last_upload = updated_data.get('lastDietUpload')
                        
                        print(f"Verified Firestore update (attempt {attempt + 1}):")
                        print(f"  - dietPdfUrl: {diet_pdf_url}")
                        print(f"  - dietCacheVersion: {cache_version}")
                        print(f"  - lastDietUpload: {last_upload}")
                        
                        # Check if all fields were updated correctly
                        if (diet_pdf_url == diet_info['dietPdfUrl'] and 
                            cache_version == diet_info['dietCacheVersion'] and
                            last_upload == diet_info['lastDietUpload']):
                            print(f"✅ All fields updated correctly on attempt {attempt + 1}")
                            break
                        else:
                            print(f"⚠️ Some fields not updated correctly on attempt {attempt + 1}")
                            if attempt == max_retries - 1:
                                print("❌ Failed to update all fields after all retries")
                                # Try one more direct update
                                await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id).update({
                                    "dietCacheVersion": diet_info['dietCacheVersion']
                                }))
                                print("🔄 Attempted direct cache version update")
                    else:
                        print(f"ERROR: User document {user_id} not found after update (attempt {attempt + 1})")
                        if attempt == max_retries - 1:
                            raise Exception(f"User document {user_id} not found after update")
        except Exception as firestore_error:
            print(f"ERROR updating Firestore: {firestore_error}")
            raise firestore_error
        
        # Extract notifications from the new diet PDF but DON'T automatically schedule
        try:
            print(f"Starting notification extraction from new diet PDF: {file.filename}")
            notifications = diet_notification_service.extract_and_create_notifications(
                user_id, file.filename, firestore_db
            )
            
            if notifications:
                # Store notifications in Firestore with the new PDF URL
                user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
                try:
                    await loop.run_in_executor(executor, lambda: user_notifications_ref.set({
                        "diet_notifications": notifications,
                        "extracted_at": datetime.now().isoformat(),
                        "diet_pdf_url": file.filename,  # Use the new PDF filename
                    }, merge=True))
                    logger.info(f"[DIET UPLOAD] Successfully stored notifications in Firestore for user {user_id}")
                except RuntimeError as e:
                    if "cannot schedule new futures after shutdown" in str(e):
                        logger.error(f"[DIET UPLOAD] ThreadPoolExecutor shutdown error, using direct Firestore call")
                        # Use direct Firestore call as fallback
                        user_notifications_ref.set({
                            "diet_notifications": notifications,
                            "extracted_at": datetime.now().isoformat(),
                            "diet_pdf_url": file.filename,
                        }, merge=True)
                        logger.info(f"[DIET UPLOAD] Successfully stored notifications using direct Firestore call for user {user_id}")
                    else:
                        raise
                
                # Set new_diet_received flag in user profile for popup trigger
                logger.info(f"[DIET UPLOAD] Setting new_diet_received=True for user {user_id}")
                try:
                    user_profile_ref = firestore_db.collection("user_profiles").document(user_id)
                    logger.info(f"[DIET UPLOAD] Created Firestore reference for user {user_id}")
                    
                    # Test if document exists first
                    try:
                        doc_exists = await loop.run_in_executor(executor, lambda: user_profile_ref.get().exists)
                        logger.info(f"[DIET UPLOAD] Document exists check: {doc_exists}")
                    except RuntimeError as e:
                        if "cannot schedule new futures after shutdown" in str(e):
                            logger.error(f"[DIET UPLOAD] ThreadPoolExecutor shutdown error, using direct Firestore call for flag setting")
                            # Use direct Firestore call as fallback
                            doc_exists = user_profile_ref.get().exists
                            logger.info(f"[DIET UPLOAD] Document exists check (direct): {doc_exists}")
                        else:
                            raise
                    
                    if not doc_exists:
                        logger.error(f"[DIET UPLOAD] Document {user_id} does not exist in user_profiles collection!")
                        # Create the document with the flag
                        try:
                            await loop.run_in_executor(executor, lambda: user_profile_ref.set({
                                "new_diet_received": True
                            }, merge=True))
                            logger.info(f"[DIET UPLOAD] Created document with new_diet_received=True for user {user_id}")
                        except RuntimeError as e:
                            if "cannot schedule new futures after shutdown" in str(e):
                                logger.error(f"[DIET UPLOAD] ThreadPoolExecutor shutdown error, using direct Firestore call for document creation")
                                user_profile_ref.set({
                                    "new_diet_received": True
                                }, merge=True)
                                logger.info(f"[DIET UPLOAD] Created document with new_diet_received=True using direct call for user {user_id}")
                            else:
                                raise
                    else:
                        # Update existing document
                        try:
                            await loop.run_in_executor(executor, lambda: user_profile_ref.update({
                                "new_diet_received": True
                            }))
                            logger.info(f"[DIET UPLOAD] Updated existing document with new_diet_received=True for user {user_id}")
                        except RuntimeError as e:
                            if "cannot schedule new futures after shutdown" in str(e):
                                logger.error(f"[DIET UPLOAD] ThreadPoolExecutor shutdown error, using direct Firestore call for document update")
                                user_profile_ref.update({
                                    "new_diet_received": True
                                })
                                logger.info(f"[DIET UPLOAD] Updated existing document with new_diet_received=True using direct call for user {user_id}")
                            else:
                                raise
                    
                    # Verify the update
                    try:
                        updated_doc = await loop.run_in_executor(executor, lambda: user_profile_ref.get())
                        if updated_doc.exists:
                            updated_data = updated_doc.to_dict()
                            flag_value = updated_data.get("new_diet_received")
                            logger.info(f"[DIET UPLOAD] Verification: new_diet_received={flag_value}")
                        else:
                            logger.error(f"[DIET UPLOAD] Verification failed: document does not exist after update")
                    except RuntimeError as e:
                        if "cannot schedule new futures after shutdown" in str(e):
                            logger.error(f"[DIET UPLOAD] ThreadPoolExecutor shutdown error, using direct Firestore call for verification")
                            updated_doc = user_profile_ref.get()
                            if updated_doc.exists:
                                updated_data = updated_doc.to_dict()
                                flag_value = updated_data.get("new_diet_received")
                                logger.info(f"[DIET UPLOAD] Verification (direct): new_diet_received={flag_value}")
                            else:
                                logger.error(f"[DIET UPLOAD] Verification failed (direct): document does not exist after update")
                        else:
                            raise
                        
                except Exception as flag_error:
                    logger.error(f"[DIET UPLOAD] Error setting new_diet_received flag: {flag_error}")
                    import traceback
                    logger.error(f"[DIET UPLOAD] Flag setting traceback: {traceback.format_exc()}")
                    # Don't raise the error, just log it - diet upload should still succeed
                
                print(f"Extracted {len(notifications)} timed activities from new diet PDF for user {user_id}")
                print(f"Stored notifications with new PDF URL: {file.filename}")
                print(f"Set new_diet_received=True for popup trigger")
                
                # DO NOT automatically schedule here - let the user trigger it via popup
                # This prevents backend/frontend scheduling conflicts
                    
            else:
                print(f"No timed activities found in new diet PDF for user {user_id}")
                
        except Exception as e:
            print(f"Error extracting notifications from new diet PDF: {e}")
            import traceback
            traceback.print_exc()
        
        # Send notification using new simple system
        print(f"[DIET UPLOAD] ===== SENDING NOTIFICATION =====")
        print(f"[DIET UPLOAD] User ID: {user_id}")
        
        try:
            notification_service = get_notification_service(firestore_db)
            
            # Get dietician name for personalization
            dietician_doc = firestore_db.collection("user_profiles").document(dietician_id).get()
            dietician_name = "Your dietician"
            if dietician_doc.exists:
                dietician_data = dietician_doc.to_dict()
                first_name = dietician_data.get("firstName", "")
                last_name = dietician_data.get("lastName", "")
                if first_name and last_name:
                    dietician_name = f"{first_name} {last_name}"
                elif first_name:
                    dietician_name = first_name
            
            success = notification_service.send_new_diet_notification(user_id, dietician_name)
            
            if success:
                print(f"[DIET UPLOAD] ✅ NOTIFICATION SENT SUCCESSFULLY to user {user_id}")
                print(f"[DIET UPLOAD] 🎯 User should see notification")
            else:
                print(f"[DIET UPLOAD] ❌ NOTIFICATION FAILED to send to user {user_id}")
                
        except Exception as notif_error:
            print(f"[DIET UPLOAD] ❌ Error sending notification: {notif_error}")
        
        print(f"[DIET UPLOAD] ===== UPLOAD COMPLETE =====")
        
        return {"success": True, "pdf_url": pdf_url, "message": "Diet uploaded successfully"}
        
    except Exception as e:
        logger.error(f"[DIET UPLOAD ERROR] ===== DIET UPLOAD FAILED =====")
        logger.error(f"[DIET UPLOAD ERROR] user_id: {user_id}")
        logger.error(f"[DIET UPLOAD ERROR] dietician_id: {dietician_id}")
        logger.error(f"[DIET UPLOAD ERROR] Error: {e}")
        logger.error(f"[DIET UPLOAD ERROR] Error type: {type(e).__name__}")
        import traceback
        logger.error(f"[DIET UPLOAD ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Check Users with 1 Day Remaining (for scheduled jobs) ---
@api_router.post("/diet/check-reminders")
async def check_diet_reminders():
    """
    DEPRECATED: This endpoint is deprecated. Use the scheduled job instead.
    """
    logger.info("[Diet Reminders] Endpoint deprecated - use scheduled job")
    return {
        "success": True,
        "message": "Endpoint deprecated - use scheduled job",
        "users_with_one_day": 0,
        "users": []
    }

# --- Get User Diet PDF and Countdown ---
@api_router.get("/users/{user_id}/diet")
async def get_user_diet(user_id: str):
    """
    Returns the user's diet PDF URL and days left until new diet.
    Countdown is 3 days for trial users, 7 days for regular subscriptions.
    """
    try:
        # Add timeout for Firestore operations
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Use ThreadPoolExecutor to handle Firestore operations asynchronously
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            doc = await loop.run_in_executor(
                executor, 
                lambda: firestore_db.collection("user_profiles").document(user_id).get()
            )
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found.")
        
        data = doc.to_dict()
        pdf_url = data.get("dietPdfUrl")
        last_upload = data.get("lastDietUpload")
        days_left = None
        hours_left = None
        
        # Check if user is on trial (3 days countdown) or regular subscription (7 days countdown)
        subscription_status = data.get("subscriptionStatus", "")
        subscription_plan = data.get("subscriptionPlan", "")
        is_trial = subscription_status == "trial" or subscription_plan == "trial"
        
        # Set countdown duration: 3 days (72 hours) for trial, 7 days (168 hours) for regular
        countdown_hours = 72 if is_trial else 168
        
        if last_upload:
            try:
                # Handle timezone-aware datetime strings
                if last_upload.endswith('Z'):
                    # Convert UTC timezone to naive datetime
                    last_upload = last_upload.replace('Z', '+00:00')
                last_dt = datetime.fromisoformat(last_upload)
                
                # Use timezone-aware datetime for consistent calculation
                from datetime import timezone
                now = datetime.now(timezone.utc)
                
                # Ensure last_dt is timezone-aware for comparison
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                
                time_diff = now - last_dt
                
                # Calculate total hours remaining (3 days for trial, 7 days for regular)
                total_hours_remaining = max(0, countdown_hours - int(time_diff.total_seconds() / 3600))
                days_left = total_hours_remaining // 24
                hours_left = total_hours_remaining % 24
                
                logger.info(f"[DIET] User {user_id}: is_trial={is_trial}, countdown_hours={countdown_hours}, days_left={days_left}, hours_left={hours_left}")
            except ValueError as e:
                logger.error(f"Error parsing lastDietUpload date for user {user_id}: {e}")
                days_left = None
                hours_left = None
        
        return {
            "dietPdfUrl": pdf_url, 
            "daysLeft": days_left, 
            "hoursLeft": hours_left,
            "lastDietUpload": last_upload,
            "hasDiet": pdf_url is not None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diet for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve diet information. Please try again.")

@api_router.get("/users/{user_id}/new-diet-popup-trigger")
async def get_new_diet_popup_trigger(user_id: str):
    """
    Check if new diet popup should be shown for the user.
    For existing users without the attribute, set it to True by default.
    """
    try:
        # Get user's profile to check new_diet_received flag
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        
        if not user_doc.exists:
            return {"showPopup": False, "reason": "User not found"}
        
        user_data = user_doc.to_dict()
        
        # Check if user has the new_diet_received attribute
        if "new_diet_received" not in user_data:
            # Existing user without the attribute - check if they have a diet
            # If they have a diet, set to True (they should see popup)
            # If no diet, set to False (no popup needed)
            
            # Check if user has a diet by looking at dietPdfUrl
            has_diet = user_data.get("dietPdfUrl") is not None
            
            if has_diet:
                logger.info(f"[NEW DIET POPUP] Existing user {user_id} missing new_diet_received attribute but has diet, setting to True")
                new_diet_received = True
            else:
                logger.info(f"[NEW DIET POPUP] Existing user {user_id} missing new_diet_received attribute and no diet, setting to False")
                new_diet_received = False
            
            # Update the user document with the new attribute
            user_doc.reference.update({
                "new_diet_received": new_diet_received
            })
            
            logger.info(f"[NEW DIET POPUP] Set new_diet_received={new_diet_received} for existing user {user_id}")
        else:
            new_diet_received = user_data.get("new_diet_received", False)
        
        logger.info(f"[NEW DIET POPUP] User {user_id}: new_diet_received={new_diet_received}")
        
        return {
            "showPopup": new_diet_received,
            "reason": "new_diet_received flag" if new_diet_received else "no new diet"
        }
        
    except Exception as e:
        logger.error(f"Error checking new diet popup trigger: {e}")
        return {"showPopup": False, "reason": f"Error: {e}"}

@api_router.get("/debug/user-token/{user_id}")
async def debug_user_token(user_id: str):
    """Debug endpoint to check user's notification token status"""
    print(f"[DEBUG ENDPOINT] ===== DEBUGGING USER TOKEN =====")
    print(f"[DEBUG ENDPOINT] User ID: {user_id}")
    
    try:
        check_firebase_availability()
        
        # Get user document
        print(f"[DEBUG ENDPOINT] Step 1: Getting user document from Firestore")
        doc = firestore_db.collection("user_profiles").document(user_id).get()
        
        if not doc.exists:
            print(f"[DEBUG ENDPOINT] ❌ User document does not exist")
            return {
                "user_id": user_id,
                "status": "error",
                "message": "User document does not exist",
                "document_exists": False
            }
        
        print(f"[DEBUG ENDPOINT] ✅ User document exists")
        data = doc.to_dict()
        
        # Check all token-related fields
        print(f"[DEBUG ENDPOINT] Step 2: Analyzing document fields")
        has_expo_push_token = "expoPushToken" in data
        has_notification_token = "notificationToken" in data
        has_fcm_token = "fcmToken" in data
        
        print(f"[DEBUG ENDPOINT] Token fields:")
        print(f"  - expoPushToken exists: {has_expo_push_token}")
        print(f"  - notificationToken exists: {has_notification_token}")
        print(f"  - fcmToken exists: {has_fcm_token}")
        
        # Get token previews
        expo_token_preview = None
        if has_expo_push_token:
            expo_token = data.get("expoPushToken")
            expo_token_preview = expo_token[:30] + "..." if expo_token else None
            print(f"  - expoPushToken preview: {expo_token_preview}")
        
        notification_token_preview = None
        if has_notification_token:
            notif_token = data.get("notificationToken")
            notification_token_preview = notif_token[:30] + "..." if notif_token else None
            print(f"  - notificationToken preview: {notification_token_preview}")
        
        # Check token validity
        expo_token_valid = False
        if expo_token_preview:
            expo_token_valid = expo_token_preview.startswith("ExponentPushToken")
            print(f"  - expoPushToken valid format: {expo_token_valid}")
        
        notification_token_valid = False
        if notification_token_preview:
            notification_token_valid = notification_token_preview.startswith("ExponentPushToken")
            print(f"  - notificationToken valid format: {notification_token_valid}")
        
        # Check other relevant fields
        print(f"[DEBUG ENDPOINT] Step 3: Checking other fields")
        is_dietician = data.get("isDietician", False)
        platform = data.get("platform")
        last_token_update = data.get("lastTokenUpdate")
        new_diet_received = data.get("new_diet_received", False)
        
        print(f"[DEBUG ENDPOINT] Other fields:")
        print(f"  - isDietician: {is_dietician}")
        print(f"  - platform: {platform}")
        print(f"  - lastTokenUpdate: {last_token_update}")
        print(f"  - new_diet_received: {new_diet_received}")
        
        # Test backend token retrieval functions
        print(f"[DEBUG ENDPOINT] Step 4: Testing backend token retrieval")
        notification_service = get_notification_service(firestore_db)
        user_token_result = notification_service.get_user_token(user_id)
        print(f"[DEBUG ENDPOINT] get_user_token() result: {user_token_result[:20] if user_token_result else 'None'}...")
        
        dietician_token_result = None
        if is_dietician:
            # Use new simple notification service
            notification_service = get_notification_service(firestore_db)
            dietician_token_result = notification_service.get_user_token(user_id)
            print(f"[DEBUG ENDPOINT] get_user_token() result for dietician: {dietician_token_result[:20] if dietician_token_result else 'None'}...")
        
        print(f"[DEBUG ENDPOINT] ===== DEBUG COMPLETE =====")
        
        return {
            "user_id": user_id,
            "status": "success",
            "document_exists": True,
            "tokens": {
                "expo_push_token": {
                    "exists": has_expo_push_token,
                    "preview": expo_token_preview,
                    "valid": expo_token_valid
                },
                "notification_token": {
                    "exists": has_notification_token,
                    "preview": notification_token_preview,
                    "valid": notification_token_valid
                },
                "fcm_token": {
                    "exists": has_fcm_token
                }
            },
            "user_info": {
                "is_dietician": is_dietician,
                "platform": platform,
                "last_token_update": last_token_update,
                "new_diet_received": new_diet_received
            },
            "backend_token_test": {
                "get_user_token_result": user_token_result[:20] + "..." if user_token_result else None,
                "get_user_token_result_for_dietician": dietician_token_result[:20] + "..." if dietician_token_result else "N/A (not dietician)"
            }
        }
        
    except Exception as e:
        print(f"[DEBUG ENDPOINT] ❌ Error checking token status: {e}")
        import traceback
        print(f"[DEBUG ENDPOINT] Traceback: {traceback.format_exc()}")
        return {
            "user_id": user_id,
            "status": "error",
            "message": str(e),
            "document_exists": False
        }

@api_router.get("/debug/test-notification/{user_id}")
async def debug_test_notification(user_id: str):
    """Debug endpoint to test sending a notification to a user"""
    print(f"[TEST NOTIFICATION] ===== TESTING NOTIFICATION SEND =====")
    print(f"[TEST NOTIFICATION] User ID: {user_id}")
    
    try:
        # Get user token
        print(f"[TEST NOTIFICATION] Step 1: Getting user token")
        user_token = get_user_notification_token(user_id)
        
        if not user_token:
            print(f"[TEST NOTIFICATION] ❌ No token found for user")
            return {
                "user_id": user_id,
                "status": "error",
                "message": "No notification token found for user",
                "token_found": False
            }
        
        print(f"[TEST NOTIFICATION] ✅ Token found: {user_token[:20]}...")
        
        # Send test notification
        print(f"[TEST NOTIFICATION] Step 2: Sending test notification")
        test_payload = {
            "type": "test_notification",
            "userId": user_id,
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        success = send_push_notification(
            user_token,
            "Test Notification",
            "This is a test notification to verify push notifications are working.",
            test_payload
        )
        
        if success:
            print(f"[TEST NOTIFICATION] ✅ Test notification sent successfully")
            return {
                "user_id": user_id,
                "status": "success",
                "message": "Test notification sent successfully",
                "token_found": True,
                "notification_sent": True
            }
        else:
            print(f"[TEST NOTIFICATION] ❌ Test notification failed to send")
            return {
                "user_id": user_id,
                "status": "error",
                "message": "Test notification failed to send",
                "token_found": True,
                "notification_sent": False
            }
        
    except Exception as e:
        print(f"[TEST NOTIFICATION] ❌ Error testing notification: {e}")
        import traceback
        print(f"[TEST NOTIFICATION] Traceback: {traceback.format_exc()}")
        return {
            "user_id": user_id,
            "status": "error",
            "message": str(e),
            "token_found": False,
            "notification_sent": False
        }

# --- Appointment Management Endpoints ---
@api_router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentRequest):
    """Create a new appointment"""
    try:
        # Validate appointment data
        if not appointment.userId or not appointment.date or not appointment.timeSlot:
            raise HTTPException(status_code=400, detail="Missing required appointment fields")
        
        # Check for overlapping appointments
        appointment_date = appointment.date.split('T')[0]  # Get date part only
        existing_appointments = firestore_db.collection("appointments").where("date", ">=", appointment.date).where("date", "<", appointment.date + "T23:59:59").stream()
        
        for doc in existing_appointments:
            existing_appt = doc.to_dict()
            if existing_appt.get("timeSlot") == appointment.timeSlot:
                raise HTTPException(status_code=409, detail="Time slot already booked")
        
        # Check for breaks
        breaks = firestore_db.collection("breaks").stream()
        for doc in breaks:
            break_data = doc.to_dict()
            if (break_data.get("fromTime") <= appointment.timeSlot <= break_data.get("toTime") and
                (not break_data.get("specificDate") or break_data.get("specificDate") == appointment_date)):
                raise HTTPException(status_code=409, detail="Time slot is during a break")
        
        # Create appointment
        appointment_data = appointment.dict()
        appointment_data["createdAt"] = datetime.utcnow().isoformat()
        
        doc_ref = firestore_db.collection("appointments").add(appointment_data)
        
        return AppointmentResponse(
            id=doc_ref[1].id,
            **appointment_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")

@api_router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(user_id: Optional[str] = None):
    """Get all appointments or appointments for a specific user"""
    try:
        if user_id:
            # Get appointments for specific user
            docs = firestore_db.collection("appointments").where("userId", "==", user_id).stream()
        else:
            # Get all appointments
            docs = firestore_db.collection("appointments").stream()
        
        appointments = []
        for doc in docs:
            data = doc.to_dict()
            appointments.append(AppointmentResponse(id=doc.id, **data))
        
        return appointments
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Delete an appointment"""
    try:
        doc_ref = firestore_db.collection("appointments").document(appointment_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        doc_ref.delete()
        return {"success": True, "message": "Appointment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete appointment")

@api_router.get("/breaks", response_model=List[dict])
async def get_breaks():
    """Get all breaks"""
    try:
        docs = firestore_db.collection("breaks").stream()
        breaks = []
        for doc in docs:
            data = doc.to_dict()
            breaks.append({"id": doc.id, **data})
        
        return breaks
        
    except Exception as e:
        logger.error(f"Error fetching breaks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch breaks")

@api_router.post("/breaks", response_model=dict)
async def create_break(break_request: BreakRequest):
    """Create a new break"""
    try:
        # Validate break data
        if not break_request.fromTime or not break_request.toTime:
            raise HTTPException(status_code=400, detail="Missing required break fields")
        
        # Check for overlapping breaks
        existing_breaks = firestore_db.collection("breaks").stream()
        for doc in existing_breaks:
            existing_break = doc.to_dict()
            if (existing_break.get("fromTime") <= break_request.toTime and 
                existing_break.get("toTime") >= break_request.fromTime and
                existing_break.get("specificDate") == break_request.specificDate):
                raise HTTPException(status_code=409, detail="Break time overlaps with existing break")
        
        # Create break
        break_data = break_request.dict()
        doc_ref = firestore_db.collection("breaks").add(break_data)
        
        return {"id": doc_ref[1].id, **break_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating break: {e}")
        raise HTTPException(status_code=500, detail="Failed to create break")

# --- Serve PDF from Firestore ---
@api_router.get("/users/{user_id}/diet/pdf")
async def get_user_diet_pdf(user_id: str, t: str = None):
    """
    Serves the PDF data from Firebase Storage for viewing.
    t: Cache busting parameter (timestamp)
    """
    try:
        # First, get the user's profile to find the dietPdfUrl
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user_data = user_doc.to_dict()
        diet_pdf_url = user_data.get("dietPdfUrl")
        
        if not diet_pdf_url:
            raise HTTPException(status_code=404, detail="No diet PDF found for this user. Please ask your dietician to upload a diet plan.")
        
        # If it's a Firebase Storage signed URL, download and serve the content directly
        if diet_pdf_url.startswith('https://storage.googleapis.com/'):
            try:
                import requests
                response = requests.get(diet_pdf_url)
                if response.status_code == 200:
                    from fastapi.responses import Response
                    return Response(
                        content=response.content,
                        media_type="application/pdf",
                        headers={
                            "Content-Disposition": f"inline; filename=diet.pdf",
                            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0"
                        }
                    )
                else:
                    raise HTTPException(status_code=404, detail="Failed to fetch PDF from Firebase Storage.")
            except Exception as e:
                print(f"Error fetching from Firebase Storage: {e}")
                raise HTTPException(status_code=404, detail="Failed to fetch PDF from Firebase Storage.")
        
        # If it's a firestore:// URL, try to get from diet_pdfs collection
        if diet_pdf_url.startswith('firestore://'):
            doc = firestore_db.collection("diet_pdfs").document(user_id).get()
            if not doc.exists:
                raise HTTPException(status_code=404, detail="Diet PDF not found in Firestore.")
            
            data = doc.to_dict()
            pdf_data = data.get("pdf_data")
            content_type = data.get("content_type", "application/pdf")
            
            if not pdf_data:
                raise HTTPException(status_code=404, detail="PDF data not found.")
            
            # Decode base64 data
            import base64
            pdf_bytes = base64.b64decode(pdf_data)
            
            # Return PDF as response
            from fastapi.responses import Response
            return Response(
                content=pdf_bytes,
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename={data.get('filename', 'diet.pdf')}"}
            )
        
        # If it's just a filename, try to get from Firebase Storage
        if diet_pdf_url.endswith('.pdf'):
            try:
                # Try to get the blob from Firebase Storage
                blob_path = f"diets/{user_id}/{diet_pdf_url}"
                blob = bucket.blob(blob_path)
                
                if not blob.exists():
                    raise HTTPException(status_code=404, detail="Diet PDF not found in Storage.")
                
                # Download the PDF content and serve it directly with inline disposition
                pdf_content = blob.download_as_bytes()
                
                from fastapi.responses import Response
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                                            headers={
                            "Content-Disposition": f"inline; filename={diet_pdf_url}",
                            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0"
                        }
                )
                
            except Exception as storage_error:
                print(f"Storage error: {storage_error}")
                raise HTTPException(status_code=404, detail="Diet PDF not found in Storage.")
        
        # If we can't handle the URL format, return an error
        raise HTTPException(status_code=400, detail="Invalid diet PDF URL format.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve PDF.")

# --- List All Users Except Dietician (for Dietician Upload Screen) ---
@api_router.get("/users/non-dietician")
async def get_non_dietician_users():
    """
    Returns a list of user profiles where isDietician is not True.
    Only shows users with paid plans (not free plan).
    """
    return list_non_dietician_users()

@api_router.post("/users/refresh-free-plans")
async def refresh_free_plans():
    """
    Refresh all users with "Not set" or missing subscription plans to free plan.
    This is called when the dietician opens the upload diet page.
    """
    try:
        check_firebase_availability()
        
        users_ref = firestore_db.collection("user_profiles")
        all_users = users_ref.stream()
        
        updated_count = 0
        
        for user in all_users:
            user_data = user.to_dict()
            user_id = user.id
            
            # Skip dietician users
            if user_data.get("isDietician"):
                continue
            
            # Check if user has no subscription plan or "Not set" plan
            subscription_plan = user_data.get("subscriptionPlan")
            if not subscription_plan or subscription_plan == "Not set" or subscription_plan == "":
                # Update user to free plan
                update_data = {
                    "subscriptionPlan": "free",
                    "isSubscriptionActive": False,
                    "subscriptionStartDate": None,
                    "subscriptionEndDate": None,
                    "currentSubscriptionAmount": 0.0,
                    "totalAmountPaid": user_data.get("totalAmountPaid", 0.0),
                    "autoRenewalEnabled": True
                }
                
                firestore_db.collection("user_profiles").document(user_id).update(update_data)
                updated_count += 1
                logger.info(f"Updated user {user_id} to free plan")
        
        logger.info(f"Refreshed {updated_count} users to free plan")
        return {
            "success": True,
            "message": f"Successfully updated {updated_count} users to free plan",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error refreshing free plans: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh free plans: {e}")

@api_router.get("/users/all-profiles")
async def get_all_user_profiles():
    """
    Returns a list of all user profiles (including dieticians) for the messages screen.
    This endpoint is used by the dietician messages screen to show all users.
    """
    try:
        check_firebase_availability()
        
        users_ref = firestore_db.collection("user_profiles")
        all_users = users_ref.stream()
        
        user_profiles = []
        
        for user in all_users:
            user_data = user.to_dict()
            user_id = user.id
            
            # Skip placeholder users and test users
            is_placeholder = (
                user_data.get("firstName", "User") == "User" and
                user_data.get("lastName", "") == "" and
                (not user_data.get("email") or user_data.get("email", "").endswith("@example.com"))
            )
            
            is_test_user = (
                user_data.get("firstName", "").lower() == "test" or
                user_data.get("email", "").startswith("test@") or
                user_data.get("userId", "").startswith("test_") or
                "test" in user_data.get("userId", "").lower()
            )
            
            has_proper_name = (
                user_data.get("firstName") and 
                user_data.get("firstName") != "User" and
                user_data.get("firstName") != "Test" and
                user_data.get("firstName").strip() != ""
            )
            
            # Exclude users with active free trials
            subscription_status = user_data.get("subscriptionStatus", "")
            free_trial_end_date = user_data.get("freeTrialEndDate")
            
            has_active_trial = False
            if free_trial_end_date and subscription_status == "trial":
                try:
                    trial_end = datetime.fromisoformat(free_trial_end_date)
                    if datetime.now() < trial_end:
                        has_active_trial = True
                except:
                    pass  # If date parsing fails, assume no active trial
            
            if not is_placeholder and not is_test_user and has_proper_name and not has_active_trial:
                # Add the document ID as userId
                user_data["userId"] = user_id
                user_profiles.append(user_data)
        
        logger.info(f"Retrieved {len(user_profiles)} user profiles for messages screen")
        return user_profiles
        
    except Exception as e:
        logger.error(f"Error getting all user profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profiles")

# --- Diet Notification Endpoints ---
@api_router.post("/users/{user_id}/diet/notifications/extract")
async def extract_diet_notifications(user_id: str):
    """
    Extract timed activities from user's diet PDF and create notifications.
    """
    start_time = time.time()
    logger.info(f"[DIET EXTRACTION] Starting extraction for user {user_id}")
    
    try:
        # Get user profile to find diet PDF URL
        logger.info(f"[DIET EXTRACTION] Getting user profile for {user_id}")
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        diet_pdf_url = user_data.get("dietPdfUrl")
        
        if not diet_pdf_url:
            raise HTTPException(status_code=404, detail="No diet PDF found for this user")
        
        logger.info(f"[DIET EXTRACTION] Found diet PDF URL: {diet_pdf_url}")
        
        # First, cancel all existing scheduled notifications for this user
        try:
            logger.info(f"[DIET EXTRACTION] Cancelling existing notifications for {user_id}")
            scheduler = get_notification_scheduler(firestore_db)
            cancelled_count = await scheduler.cancel_user_notifications(user_id)
            logger.info(f"[DIET EXTRACTION] Cancelled {cancelled_count} existing notifications for user {user_id}")
        except Exception as cancel_error:
            logger.error(f"[DIET EXTRACTION] Error cancelling existing notifications for user {user_id}: {cancel_error}")
            # Continue with extraction even if cancellation fails
        
        # Extract notifications from diet PDF
        logger.info(f"[DIET EXTRACTION] Starting PDF text extraction for {user_id}")
        extraction_start = time.time()
        notifications = diet_notification_service.extract_and_create_notifications(
            user_id, diet_pdf_url, firestore_db
        )
        extraction_time = time.time() - extraction_start
        logger.info(f"[DIET EXTRACTION] PDF extraction completed in {extraction_time:.2f}s for user {user_id}")
        
        if not notifications:
            logger.info(f"[DIET EXTRACTION] No notifications found for user {user_id}")
            return {
                "message": "No timed activities found in diet PDF",
                "notifications": []
            }
        
        # Store notifications in Firestore for the user
        logger.info(f"[DIET EXTRACTION] Storing {len(notifications)} notifications in Firestore for {user_id}")
        user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
        user_notifications_ref.set({
            "diet_notifications": notifications,
            "extracted_at": datetime.now().isoformat(),
            "diet_pdf_url": diet_pdf_url,
        }, merge=True)
        
        # Clear new_diet_received flag when extraction is completed
        user_profile_ref = firestore_db.collection("user_profiles").document(user_id)
        user_profile_ref.update({
            "new_diet_received": False
        })
        
        # DISABLED: Schedule the notifications on the backend to prevent conflicts
        # Manual extraction now uses only local scheduling on the device for reliability
        logger.info(f"[DIET EXTRACTION] Skipping backend scheduling - using local scheduling only for reliability")
        
        total_time = time.time() - start_time
        logger.info(f"[DIET EXTRACTION] Completed extraction in {total_time:.2f}s for user {user_id}: {len(notifications)} notifications")
        
        return {
            "message": f"Successfully extracted and scheduled {len(notifications)} timed activities from diet PDF",
            "notifications": notifications
        }
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"[DIET EXTRACTION] Error extracting diet notifications for user {user_id} after {total_time:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract diet notifications: {e}")

@api_router.get("/users/{user_id}/diet/notifications")
async def get_diet_notifications(user_id: str):
    """
    Get all diet notifications for a user.
    """
    try:
        user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
        doc = user_notifications_ref.get()
        
        if not doc.exists:
            return {"notifications": []}
        
        data = doc.to_dict()
        notifications = data.get("diet_notifications", [])
        
        return {
            "notifications": notifications,
            "extracted_at": data.get("extracted_at"),
            "diet_pdf_url": data.get("diet_pdf_url")
        }
        
    except Exception as e:
        logger.error(f"Error getting diet notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diet notifications: {e}")

@api_router.get("/users/{user_id}/diet/raw-text")
async def get_diet_raw_text(user_id: str):
    """
    Get raw extracted text from diet PDF for debugging.
    """
    try:
        # Get user's diet PDF URL
        user_doc = firestore_db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        diet_pdf_url = user_data.get("dietPdfUrl")
        
        if not diet_pdf_url:
            raise HTTPException(status_code=404, detail="No diet PDF found for user")
        
        # Extract raw text
        raw_text = pdf_rag_service.get_diet_pdf_text(user_id, diet_pdf_url, firestore_db)
        
        if not raw_text:
            raise HTTPException(status_code=404, detail="Failed to extract text from diet PDF")
        
        return {"raw_text": raw_text}
    except Exception as e:
        logger.error(f"Error getting raw diet text for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get raw diet text")



@api_router.post("/users/{user_id}/diet/notifications/test")
async def test_diet_notification(user_id: str):
    """
    Send a test notification to verify the user's notification setup.
    """
    try:
        # Get user's diet notifications
        user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
        doc = user_notifications_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="No diet notifications found for this user")
        
        data = doc.to_dict()
        notifications = data.get("diet_notifications", [])
        
        if not notifications:
            raise HTTPException(status_code=404, detail="No diet notifications found")
        
        # Send test notification using the first notification
        test_notification = notifications[0]
        success = diet_notification_service.send_immediate_notification(user_id, test_notification)
        
        if success:
            return {
                "message": "Test notification sent successfully",
                "notification": test_notification
            }
        else:
            # Return a more informative error message
            return {
                "message": "Test notification prepared but not sent (no notification token found)",
                "notification": test_notification,
                "warning": "User needs to enable notifications in the app settings"
            }
        
    except Exception as e:
        logger.error(f"Error sending test notification for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {e}")

# --- Simple Notification System Endpoints ---
@api_router.post("/notifications/send")
async def send_notification(request: dict):
    """
    Unified notification endpoint - handles all notification types.
    Simple, reliable, based on how popular apps handle notifications.
    """
    try:
        logger.info(f"[SIMPLE NOTIFICATION] ===== NOTIFICATION REQUEST =====")
        logger.info(f"[SIMPLE NOTIFICATION] Request: {json.dumps(request, indent=2)}")
        
        # Validate required fields
        recipient_id = request.get("recipientId")
        notification_type = request.get("type")
        
        if not recipient_id:
            raise HTTPException(status_code=400, detail="recipientId is required")
        
        if not notification_type:
            raise HTTPException(status_code=400, detail="type is required")
        
        # Get notification service
        notification_service = get_notification_service(firestore_db)
        
        # Handle different notification types
        success = False
        
        if notification_type == "new_diet":
            dietician_name = request.get("dieticianName", "Your dietician")
            success = notification_service.send_new_diet_notification(recipient_id, dietician_name)
            
        elif notification_type == "message":
            # This old endpoint is deprecated - use /push-notifications/send instead
            success = True
            
        elif notification_type == "appointment":
            # This old endpoint is deprecated - use /push-notifications/send instead
            success = True
            
        elif notification_type == "diet_reminder":
            user_name = request.get("userName", "User")
            success = notification_service.send_diet_reminder_notification(recipient_id, user_name)
            
        elif notification_type == "dietician_diet_reminder":
            # This old endpoint is deprecated - use scheduled job instead
            success = True
            
        else:
            # Generic notification
            title = request.get("title", "Notification")
            body = request.get("body", "")
            data = request.get("data", {})
            success = notification_service.send_notification(recipient_id, title, body, data)
        
        if success:
            logger.info(f"[SIMPLE NOTIFICATION] ✅ Notification sent successfully to {recipient_id}")
            return {"success": True, "message": "Notification sent successfully"}
        else:
            logger.error(f"[SIMPLE NOTIFICATION] ❌ Failed to send notification to {recipient_id}")
            return {"success": False, "message": "Failed to send notification"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SIMPLE NOTIFICATION] Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {e}")

@api_router.get("/notifications/test/{user_id}")
async def test_notification(user_id: str):
    """
    Test endpoint to verify notification system is working.
    """
    try:
        logger.info(f"[SIMPLE NOTIFICATION] Testing notification for user {user_id}")
        
        notification_service = get_notification_service(firestore_db)
        
        success = notification_service.send_notification(
            recipient_id=user_id,
            title="Test Notification 🧪",
            body="This is a test notification to verify the system is working.",
            data={
                "type": "test",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if success:
            return {"success": True, "message": "Test notification sent successfully"}
        else:
            return {"success": False, "message": "Failed to send test notification"}
            
    except Exception as e:
        logger.error(f"[SIMPLE NOTIFICATION] Error testing notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test notification: {e}")

# --- NEW PUSH NOTIFICATIONS API ---
@api_router.post("/push-notifications/send")
async def send_push_notification_new(request: dict):
    """
    New clean push notification endpoint.
    Handles: messages, appointments, diet_countdown
    """
    try:
        notification_type = request.get("type")
        logger.info(f"[PUSH NOTIFICATION] Received request type: {notification_type}")
        
        if notification_type == "message":
            # Message: user -> dietician OR dietician -> user
            recipient_id = request.get("recipientId")
            sender_name = request.get("senderName")
            message = request.get("message")
            is_from_dietician = request.get("isFromDietician", False)
            
            logger.info(f"[PUSH NOTIFICATION] Message notification: {sender_name} -> {recipient_id}")
            
            notification_service = get_notification_service(firestore_db)
            success = notification_service.send_message_notification(
                recipient_id, sender_name, message, is_from_dietician
            )
            
        elif notification_type == "appointment_scheduled":
            # Appointment scheduled: notify dietician
            user_name = request.get("userName")
            date = request.get("date")
            time_slot = request.get("timeSlot")
            
            logger.info(f"[PUSH NOTIFICATION] Appointment scheduled: {user_name} at {date} {time_slot}")
            
            notification_service = get_notification_service(firestore_db)
            success = notification_service.send_notification(
                recipient_id="dietician",
                title="New Appointment Scheduled",
                body=f"{user_name} scheduled an appointment for {date} at {time_slot}",
                data={"type": "appointment", "userName": user_name, "date": date, "timeSlot": time_slot}
            )
            
        elif notification_type == "appointment_cancelled":
            # Appointment cancelled: notify dietician
            user_name = request.get("userName")
            date = request.get("date")
            time_slot = request.get("timeSlot")
            
            logger.info(f"[PUSH NOTIFICATION] Appointment cancelled: {user_name} at {date} {time_slot}")
            
            notification_service = get_notification_service(firestore_db)
            success = notification_service.send_notification(
                recipient_id="dietician",
                title="Appointment Cancelled",
                body=f"{user_name} cancelled appointment for {date} at {time_slot}",
                data={"type": "appointment_cancelled", "userName": user_name, "date": date, "timeSlot": time_slot}
            )
        
        else:
            logger.error(f"[PUSH NOTIFICATION] Invalid notification type: {notification_type}")
            raise HTTPException(status_code=400, detail="Invalid notification type")
        
        if success:
            logger.info(f"[PUSH NOTIFICATION] ✅ Notification sent successfully")
            return {"success": True}
        else:
            logger.error(f"[PUSH NOTIFICATION] ❌ Failed to send notification")
            return {"success": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUSH NOTIFICATION] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notifications/debug/token/{user_id}")
async def debug_token_status(user_id: str):
    """
    Debug endpoint to check token status for a user or dietician.
    Use 'dietician' as user_id to check dietician token.
    """
    try:
        logger.info(f"[DEBUG TOKEN] Checking token status for: {user_id}")
        
        result = {
            "userId": user_id,
            "timestamp": datetime.now().isoformat(),
            "tokenFound": False,
            "tokenPreview": None,
            "tokenValid": False,
            "platform": None,
            "lastUpdate": None,
            "isDietician": False,
            "errors": []
        }
        
        if user_id == "dietician":
            # Check dietician token
            result["isDietician"] = True
            
            try:
                from services.firebase_client import get_dietician_notification_token
                token = get_dietician_notification_token()
                
                if token:
                    result["tokenFound"] = True
                    result["tokenPreview"] = token[:30] + "..."
                    result["tokenValid"] = token.startswith("ExponentPushToken")
                else:
                    result["errors"].append("No dietician token found in database")
                    
            except Exception as e:
                result["errors"].append(f"Error getting dietician token: {str(e)}")
        else:
            # Check regular user token
            doc = firestore_db.collection("user_profiles").document(user_id).get()
            
            if not doc.exists:
                result["errors"].append(f"User document not found for {user_id}")
                return result
            
            data = doc.to_dict()
            
            # Check if user is actually dietician
            result["isDietician"] = data.get("isDietician", False)
            
            # Get token
            token = data.get("expoPushToken") or data.get("notificationToken")
            
            if token:
                result["tokenFound"] = True
                result["tokenPreview"] = token[:30] + "..."
                result["tokenValid"] = token.startswith("ExponentPushToken")
                result["platform"] = data.get("platform")
                result["lastUpdate"] = data.get("lastTokenUpdate")
            else:
                result["errors"].append("No token found in user document")
                result["errors"].append("User needs to log into mobile app to register for notifications")
        
        logger.info(f"[DEBUG TOKEN] Result: {json.dumps(result, indent=2)}")
        return result
        
    except Exception as e:
        logger.error(f"[DEBUG TOKEN] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to debug token: {e}")

@api_router.post("/users/{user_id}/diet/notifications/schedule")
async def schedule_diet_notifications(user_id: str):
    """
    Schedule diet notifications for a user based on their day preferences.
    This endpoint should be called after notifications are extracted or updated.
    """
    try:
        check_firebase_availability()
        
        # Get the notification scheduler
        scheduler = get_notification_scheduler(firestore_db)
        
        # Schedule notifications for the user
        scheduled_count = await scheduler.schedule_user_notifications(user_id)
        
        return {
            "message": f"Successfully scheduled {scheduled_count} notifications",
            "scheduled": scheduled_count
        }
        
    except Exception as e:
        logger.error(f"Error scheduling notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule notifications: {e}")

@api_router.post("/users/{user_id}/diet/notifications/cancel")
async def cancel_diet_notifications(user_id: str):
    """
    Cancel all scheduled diet notifications for a user.
    """
    try:
        check_firebase_availability()
        
        # Get the notification scheduler
        scheduler = get_notification_scheduler(firestore_db)
        
        # Cancel notifications for the user
        cancelled_count = await scheduler.cancel_user_notifications(user_id)
        
        return {
            "message": f"Successfully cancelled {cancelled_count} notifications",
            "cancelled": cancelled_count
        }
        
    except Exception as e:
        logger.error(f"Error cancelling notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel notifications: {e}")

@api_router.put("/users/{user_id}/diet/notifications/{notification_id}")
async def update_diet_notification(user_id: str, notification_id: str, notification_update: dict):
    """
    Update a specific diet notification including its day preferences.
    """
    try:
        user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
        doc = user_notifications_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User notifications not found")
        
        data = doc.to_dict()
        notifications = data.get("diet_notifications", [])
        
        # Find and update the specific notification
        notification_found = False
        for i, notification in enumerate(notifications):
            if notification.get('id') == notification_id:
                # Update the notification with new data
                notifications[i].update(notification_update)
                notification_found = True
                break
        
        if not notification_found:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Save updated notifications
        user_notifications_ref.set({
            "diet_notifications": notifications,
            "updated_at": datetime.now().isoformat()
        }, merge=True)
        
        # Return immediately, reschedule notifications asynchronously
        # This prevents the API from timing out
        import asyncio
        asyncio.create_task(schedule_diet_notifications(user_id))
        
        return {"message": "Notification updated successfully. Rescheduling in background..."}
        
    except Exception as e:
        logger.error(f"Error updating notification for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update notification: {e}")

@api_router.delete("/users/{user_id}/diet/notifications/{notification_id}")
async def delete_diet_notification(user_id: str, notification_id: str):
    """
    Delete a specific diet notification.
    """
    try:
        user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
        doc = user_notifications_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User notifications not found")
        
        data = doc.to_dict()
        notifications = data.get("diet_notifications", [])
        
        # Remove the specific notification
        original_count = len(notifications)
        notifications = [n for n in notifications if n.get('id') != notification_id]
        
        if len(notifications) == original_count:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Save updated notifications
        user_notifications_ref.set({
            "diet_notifications": notifications,
            "updated_at": datetime.now().isoformat()
        }, merge=True)
        
        # Return immediately, reschedule notifications asynchronously
        # This prevents the API from timing out
        import asyncio
        asyncio.create_task(schedule_diet_notifications(user_id))
        
        return {"message": "Notification deleted successfully. Rescheduling remaining notifications in background..."}
        
    except Exception as e:
        logger.error(f"Error deleting notification for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {e}")



# Add a health check endpoint at root level
@app.get("/health")
async def health_check():
    logger.info("[HEALTH_CHECK] Health check endpoint called")
    try:
        # Basic health check
        firebase_status = "connected" if FIREBASE_AVAILABLE and firestore_db else "disconnected"
        
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow(),
            "firebase": firebase_status,
            "gemini": "configured" if GEMINI_API_KEY else "not_configured",
            "services": {
                "firebase": firebase_status,
                "gemini": "configured" if GEMINI_API_KEY else "not_configured",
                "pdf_rag": "available" if 'pdf_rag_service' in globals() else "not_available",
                "diet_notifications": "available" if 'diet_notification_service' in globals() else "not_available"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow(),
            "firebase": "error",
            "gemini": "error"
        }

# Load workout data
WORKOUTS_DATA = {
    "workouts": [
        {
            "id": "1",
            "name": "Running",
            "caloriesPerMinute": 10,
            "category": "Cardio",
            "description": "Running at a moderate pace",
            "intensity": "High"
        },
        {
            "id": "2",
            "name": "Walking",
            "caloriesPerMinute": 4,
            "category": "Cardio",
            "description": "Walking at a moderate pace",
            "intensity": "Low"
        },
        {
            "id": "3",
            "name": "Cycling",
            "caloriesPerMinute": 8,
            "category": "Cardio",
            "description": "Cycling at a moderate pace",
            "intensity": "Medium"
        },
        {
            "id": "4",
            "name": "Swimming",
            "caloriesPerMinute": 9,
            "category": "Cardio",
            "description": "Swimming at a moderate pace",
            "intensity": "High"
        },
        {
            "id": "5",
            "name": "Push-ups",
            "caloriesPerMinute": 7,
            "category": "Strength",
            "description": "Standard push-ups",
            "intensity": "Medium"
        },
        {
            "id": "6",
            "name": "Squats",
            "caloriesPerMinute": 6,
            "category": "Strength",
            "description": "Bodyweight squats",
            "intensity": "Medium"
        },
        {
            "id": "7",
            "name": "Yoga",
            "caloriesPerMinute": 3,
            "category": "Flexibility",
            "description": "Basic yoga poses",
            "intensity": "Low"
        },
        {
            "id": "8",
            "name": "HIIT",
            "caloriesPerMinute": 12,
            "category": "Cardio",
            "description": "High-intensity interval training",
            "intensity": "High"
        },
        {
            "id": "9",
            "name": "Dancing",
            "caloriesPerMinute": 7,
            "category": "Cardio",
            "description": "Moderate intensity dancing",
            "intensity": "Medium"
        },
        {
            "id": "10",
            "name": "Weight Lifting",
            "caloriesPerMinute": 5,
            "category": "Strength",
            "description": "General weight lifting",
            "intensity": "Medium"
        }
    ]
}

@app.get("/api/workouts")
async def get_workouts():
    """Get all available workouts"""
    return WORKOUTS_DATA["workouts"]

@app.get("/api/workouts/{workout_id}")
async def get_workout(workout_id: str):
    """Get a specific workout by ID"""
    for workout in WORKOUTS_DATA["workouts"]:
        if workout["id"] == workout_id:
            return workout
    raise HTTPException(status_code=404, detail="Workout not found")

@app.post("/api/workouts/log")
async def log_workout(workout: dict):
    """Log a workout session"""
    try:
        workout_id = workout.get("workout_id")
        duration = workout.get("duration", 30)  # Default 30 minutes
        
        # Find the workout in our data
        workout_data = None
        for w in WORKOUTS_DATA["workouts"]:
            if w["id"] == workout_id:
                workout_data = w
                break
        
        if not workout_data:
            raise HTTPException(status_code=404, detail="Workout not found")
        
        # Use Gemini to calculate calories burned with the duration as-is
        nutrition = await get_workout_nutrition_from_gemini(workout_data["name"], duration)
        calories_burned = nutrition["calories"] if nutrition["calories"] != "Error" else 0

        return {
            "workout_name": workout_data["name"],
            "duration": duration,  # Return original duration value
            "calories_burned": calories_burned
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/steps")
async def get_steps(platform: str, date: Optional[str] = None):
    try:
        if date:
            start_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        end_date = start_date + timedelta(days=1)
        
        health_platform = HealthPlatformFactory.get_platform(platform)
        if not health_platform:
            raise HTTPException(status_code=400, detail="Unsupported health platform")

        steps = await health_platform.get_steps(start_date, end_date)
        return {"steps": steps, "date": start_date.strftime("%Y-%m-%d")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/food/scan-photo")
async def scan_food_photo(
    userId: str = Form(...),
    photo: UploadFile = File(...)
):
    if not userId:
        raise HTTPException(status_code=400, detail="userId is required")
    tmp_path = None
    try:
        # Limit file size (e.g., 5MB)
        contents = await photo.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Please upload a photo under 5MB.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            nutrition = await call_gemini_vision(tmp_path)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Gemini API timed out. Please try again.")
        except Exception as e:
            logger.error(f"[GEMINI CALL ERROR] {e}", exc_info=True)
            raise HTTPException(status_code=502, detail="Failed to process image with Gemini. Please try again.")
        if any(nutrition[k] == "Error" for k in ("calories", "protein", "fat")):
            raise HTTPException(status_code=400, detail="Could not recognize food in the photo. Please try another photo.")
        food = FoodItem(
            name="Photo Food",
            calories=float(nutrition["calories"]),
            protein=float(nutrition["protein"]),
            fat=float(nutrition["fat"]),
            per_100g=True
        )
        log_entry = FoodLog(
            userId=userId,
            food=food,
            servingSize="100"
        )
        loop = asyncio.get_event_loop()
        def log_food_in_db():
            log_entry.timestamp = datetime.now()
            firestore_db.collection(f"users/{userId}/food_logs").add(log_entry.dict())
        await loop.run_in_executor(executor, log_food_in_db)
        return log_entry.dict()
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[SCAN PHOTO] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing your request. Please try again.")
    finally:
        # Clean up temp file
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as cleanup_err:
            logger.warning(f"[CLEANUP] Failed to remove temp file: {cleanup_err}")

# --- NEW: Diet Countdown Scheduled Job ---
async def check_diet_countdown_job():
    """
    Daily job to check users with 1 day left in diet.
    Notifies dietician about users needing new diet plan.
    """
    try:
        from datetime import datetime, timedelta, timezone
        
        logger.info("[DIET COUNTDOWN] Starting daily check for users with 1 day left")
        
        # Get all user profiles
        users_ref = firestore_db.collection("user_profiles")
        all_users = users_ref.stream()
        
        users_needing_diet = []
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            
            # Skip dieticians
            if user_data.get("isDietician"):
                continue
            
            last_upload = user_data.get("lastDietUpload")
            if not last_upload:
                continue
            
            # Check if user is on trial (3 days countdown) or regular subscription (7 days countdown)
            subscription_status = user_data.get("subscriptionStatus", "")
            subscription_plan = user_data.get("subscriptionPlan", "")
            is_trial = subscription_status == "trial" or subscription_plan == "trial"
            
            # Set countdown duration: 3 days (72 hours) for trial, 7 days (168 hours) for regular
            countdown_hours = 72 if is_trial else 168
            
            # Parse date
            if last_upload.endswith('Z'):
                last_upload = last_upload.replace('Z', '+00:00')
            last_dt = datetime.fromisoformat(last_upload)
            
            # Calculate days left
            now = datetime.now(timezone.utc)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            
            time_diff = now - last_dt
            total_hours = max(0, countdown_hours - int(time_diff.total_seconds() / 3600))
            days_left = total_hours // 24
            
            # Check if exactly 1 day left (between 24-47 hours)
            if 24 <= total_hours < 48:
                user_name = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip()
                users_needing_diet.append({
                    "id": user_id,
                    "name": user_name or "User",
                    "email": user_data.get("email", "")
                })
                logger.info(f"[DIET COUNTDOWN] Found user with 1 day left: {user_name} ({user_id})")
        
        # Send notification to dietician for each user
        if users_needing_diet:
            notification_service = get_notification_service(firestore_db)
            for user in users_needing_diet:
                try:
                    notification_service.send_notification(
                        recipient_id="dietician",
                        title="Diet Expiring Soon ⏰",
                        body=f"{user['name']} has 1 day left in their diet plan",
                        data={"type": "diet_countdown", "userId": user["id"], "userName": user["name"]}
                    )
                    logger.info(f"[DIET COUNTDOWN] ✅ Sent notification for user: {user['name']}")
                except Exception as notif_error:
                    logger.error(f"[DIET COUNTDOWN] ❌ Failed to send notification for {user['name']}: {notif_error}")
        else:
            logger.info("[DIET COUNTDOWN] No users with 1 day left found")
        
        logger.info(f"[DIET COUNTDOWN] ✅ Daily check completed. Found {len(users_needing_diet)} users with 1 day left")
        
    except Exception as e:
        logger.error(f"[DIET COUNTDOWN] ❌ Error in job: {e}")

async def check_subscription_reminders_job():
    """Check for subscription reminders and send notifications"""
    try:
        check_firebase_availability()
        
        # Get all users with active subscriptions OR active trials
        users_ref = firestore_db.collection("user_profiles")
        # Get users with active subscriptions
        active_subscription_users = users_ref.where("isSubscriptionActive", "==", True).stream()
        # Get users with active trials (have freeTrialEndDate and subscriptionStatus == "trial")
        all_users = users_ref.stream()
        
        current_time = datetime.now()
        processed_user_ids = set()
        
        # Process active subscription users
        for user_doc in active_subscription_users:
            try:
                user_data = user_doc.to_dict()
                user_id = user_doc.id
                
                # Skip if user is a dietician
                if user_data.get("isDietician", False):
                    continue
                
                subscription_end_date = user_data.get("subscriptionEndDate")
                if not subscription_end_date:
                    continue
                
                end_date = datetime.fromisoformat(subscription_end_date)
                time_until_expiry = end_date - current_time
                
                # Check for payment reminders and add payment before plan ends
                # 1 week (7 days) before expiration (165-171 hours remaining)
                if timedelta(hours=165) <= time_until_expiry <= timedelta(hours=171):
                    last_reminders = user_data.get("lastPaymentReminderSent", {})
                    if not last_reminders.get("oneWeek", False):
                        await send_payment_reminder_notification(user_id, user_data, 7)  # 7 days
                        firestore_db.collection("user_profiles").document(user_id).update({
                            "lastPaymentReminderSent": {
                                **last_reminders,
                                "oneWeek": True
                            }
                        })
                
                # 1 day before expiration (23-25 hours remaining) - Add payment here
                elif timedelta(hours=23) <= time_until_expiry <= timedelta(hours=25):
                    # Add payment to totalAmountPaid (only once)
                    last_reminders = user_data.get("lastPaymentReminderSent", {})
                    if not last_reminders.get("oneDay", False):
                        await add_payment_on_plan_end(user_id, user_data)
                        # Mark reminder as sent
                        firestore_db.collection("user_profiles").document(user_id).update({
                            "lastPaymentReminderSent": {
                                **last_reminders,
                                "oneDay": True
                            }
                        })
                    # Send 1 day reminder notification
                    await send_payment_reminder_notification(user_id, user_data, 1)  # 1 day
                
                # Check if subscription has expired
                elif time_until_expiry <= timedelta(0):
                    # First check if there's a pending plan switch - activate it
                    pending_switch = user_data.get("pendingPlanSwitch")
                    if pending_switch:
                        logger.info(f"[SUBSCRIPTION REMINDER] Activating pending plan switch for user {user_id}")
                        switch_activated = await activate_pending_plan_switch(user_id, user_data)
                        if switch_activated:
                            continue  # Plan switch activated, skip renewal/expiry logic
                    
                    # Check if auto-renewal is enabled and handle accordingly
                    auto_renewal_enabled = user_data.get("autoRenewalEnabled", True)  # Default to True
                    
                    if auto_renewal_enabled:
                        # Auto-renew the subscription
                        await auto_renew_subscription(user_id, user_data)
                    else:
                        # Send expiry notification to both user and dietician
                        await send_subscription_expiry_notifications(user_id, user_data)
                    
            except Exception as e:
                logger.error(f"[SUBSCRIPTION REMINDER] Error processing user {user_doc.id}: {e}")
                continue
        
        # Process trial users (users with freeTrialEndDate)
        for user_doc in all_users:
            try:
                user_data = user_doc.to_dict()
                user_id = user_doc.id
                
                # Skip if already processed or if user is a dietician
                if user_id in processed_user_ids or user_data.get("isDietician", False):
                    continue
                
                # Check if user has an active trial
                trial_end_date = user_data.get("freeTrialEndDate")
                subscription_status = user_data.get("subscriptionStatus", "")
                
                if trial_end_date and subscription_status == "trial":
                    end_date = datetime.fromisoformat(trial_end_date)
                    time_until_expiry = end_date - current_time
                    
                    # Check for trial reminders (1 week and 1 day before)
                    # 1 week (7 days) before expiration (165-171 hours remaining)
                    if timedelta(hours=165) <= time_until_expiry <= timedelta(hours=171):
                        last_reminders = user_data.get("lastPaymentReminderSent", {})
                        if not last_reminders.get("oneWeek", False):
                            await send_trial_reminder_notification(user_id, user_data, 7)  # 7 days
                            firestore_db.collection("user_profiles").document(user_id).update({
                                "lastPaymentReminderSent": {
                                    **last_reminders,
                                    "oneWeek": True
                                }
                            })
                    
                    # 1 day before expiration (23-25 hours remaining)
                    elif timedelta(hours=23) <= time_until_expiry <= timedelta(hours=25):
                        last_reminders = user_data.get("lastPaymentReminderSent", {})
                        if not last_reminders.get("oneDay", False):
                            await send_trial_reminder_notification(user_id, user_data, 1)  # 1 day
                            firestore_db.collection("user_profiles").document(user_id).update({
                                "lastPaymentReminderSent": {
                                    **last_reminders,
                                    "oneDay": True
                                }
                            })
                    
                    # Check if trial has expired
                    elif time_until_expiry <= timedelta(0):
                        # Trial expired - remove free trial diet and send expiry notification
                        # Clear diet information (same as when regular diet expires)
                        try:
                            firestore_db.collection("user_profiles").document(user_id).update({
                                "dietPdfUrl": None,
                                "lastDietUpload": None
                            })
                            logger.info(f"[TRIAL EXPIRY] Cleared free trial diet for user {user_id}")
                        except Exception as clear_error:
                            logger.error(f"[TRIAL EXPIRY] Error clearing diet for user {user_id}: {clear_error}")
                        
                        # Send expiry notification
                        await send_trial_expiry_notification(user_id, user_data)
                    
                    processed_user_ids.add(user_id)
                    
            except Exception as e:
                logger.error(f"[TRIAL REMINDER] Error processing user {user_doc.id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"[SUBSCRIPTION REMINDERS JOB] Error: {e}")

async def add_payment_on_plan_end(user_id: str, user_data: dict):
    """Add payment to totalAmountPaid before plan ends (1 day before expiration)"""
    try:
        current_amount = user_data.get("currentSubscriptionAmount", 0.0)
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        if current_amount <= 0:
            logger.warning(f"[PAYMENT ADD] No current subscription amount for user {user_id}")
            return
        
        # Add current plan amount to total
        new_total = current_total + current_amount
        
        # Update total amount paid
        firestore_db.collection("user_profiles").document(user_id).update({
            "totalAmountPaid": new_total
        })
        
        plan_name = get_plan_name(user_data.get("subscriptionPlan", "unknown"))
        logger.info(f"[PAYMENT ADD] Added ₹{current_amount:,.0f} to total for user {user_id} (plan: {plan_name}). New total: ₹{new_total:,.0f}")
        
        # Store payment info in user profile for inclusion in expiry notification
        # Don't send separate payment_added notification - it will be included in subscription_expired notification
        user_name = get_user_first_name(user_data)
        logger.info(f"[PAYMENT ADD] Payment info stored for user {user_id}. Will be included in expiry notification.")
        
    except Exception as e:
        logger.error(f"[PAYMENT ADD] Error adding payment for user {user_id}: {e}")

async def send_payment_reminder_notification(user_id: str, user_data: dict, time_remaining: int):
    """Send payment reminder notification to user
    time_remaining is in days (1 or 7)
    """
    try:
        user_name = get_user_first_name(user_data)
        subscription_plan = user_data.get("subscriptionPlan", "Unknown Plan")
        plan_name = get_plan_name(subscription_plan)
        current_amount = user_data.get("currentSubscriptionAmount", 0.0)
        
        # Handle days-based reminders
        if time_remaining == 7:
            message = f"Hi {user_name}, your {plan_name} will end in 7 days. Payment of ₹{current_amount:,.0f} will be added to your total amount due. Your premium features will continue if auto-renewal is enabled."
                title = "Plan Ending Soon"
        elif time_remaining == 1:
            message = f"Hi {user_name}, your {plan_name} will end in 1 day. Payment of ₹{current_amount:,.0f} will be added to your total amount due. If auto-renewal is off, you'll need to select a new plan to continue."
                title = "Plan Ending Tomorrow"
            else:
                message = f"Hi {user_name}, your {plan_name} will end in {time_remaining} days. Payment of ₹{current_amount:,.0f} will be added to your total amount due."
                title = "Plan Ending Soon"
        
        # Create notification data
        notification_data = {
            "userId": user_id,
            "title": title,
            "body": message,
            "type": "payment_reminder",
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        # Save notification to Firestore
        firestore_db.collection("notifications").add(notification_data)
        
        # Send push notification using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id=user_id,
            title=title,
            body=message,
            data={
                "type": "payment_reminder",
                "time_remaining": time_remaining,
                "subscription_plan": subscription_plan
            }
        )
        
        if not success:
            logger.warning(f"[PAYMENT REMINDER NOTIFICATION] Failed to send push notification to user {user_id}")
            
    except Exception as e:
        logger.error(f"[PAYMENT REMINDER NOTIFICATION] Error: {e}")

async def send_trial_reminder_notification(user_id: str, user_data: dict, time_remaining: int):
    """Send trial reminder notification to user
    time_remaining is in days (1 or 7)
    """
    try:
        user_name = get_user_first_name(user_data)
        
        # Handle days-based reminders
        if time_remaining == 7:
            message = f"Hi {user_name}, your free trial ends in 7 days! Select a plan now to keep enjoying premium features like personalized diets, AI chatbot, and custom notifications."
            title = "Trial Ending Soon"
        elif time_remaining == 1:
            message = f"Hi {user_name}, your free trial ends in 1 day! Select a plan now to keep enjoying premium features like personalized diets, AI chatbot, and custom notifications."
            title = "Trial Ending Tomorrow"
        else:
            message = f"Hi {user_name}, your free trial ends in {time_remaining} days! Select a plan now to keep enjoying premium features."
            title = "Trial Ending Soon"
        
        # Create notification data
        notification_data = {
            "userId": user_id,
            "title": title,
            "body": message,
            "type": "trial_reminder",
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        # Save notification to Firestore
        firestore_db.collection("notifications").add(notification_data)
        
        # Send push notification using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id=user_id,
            title=title,
            body=message,
            data={
                "type": "trial_reminder",
                "time_remaining": time_remaining
            }
        )
        
        if not success:
            logger.warning(f"[TRIAL REMINDER NOTIFICATION] Failed to send push notification to user {user_id}")
            
    except Exception as e:
        logger.error(f"[TRIAL REMINDER NOTIFICATION] Error: {e}")

async def send_trial_expiry_notification(user_id: str, user_data: dict):
    """Send trial expiry notification to user"""
    try:
        user_name = get_user_first_name(user_data)
        
        # Send notification to user
        user_notification = {
            "userId": user_id,
            "title": "Free Trial Ended",
            "body": f"Hi {user_name}, your free trial has ended. Select a plan to continue enjoying premium features like personalized diet plans, AI chatbot, and custom notifications.",
            "type": "trial_expired",
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        firestore_db.collection("notifications").add(user_notification)
        
        # Send push notification to user using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id=user_id,
            title="Free Trial Ended",
            body=f"Hi {user_name}, your free trial has ended. Select a plan to continue!",
            data={"type": "trial_expired"}
            )
        
        if not success:
            logger.warning(f"[TRIAL EXPIRY NOTIFICATION] Failed to send push notification to user {user_id}")
        
        # Send notification to dietician
        await send_dietician_subscription_notification(user_id, user_data, "trial_expired")
            
    except Exception as e:
        logger.error(f"[TRIAL EXPIRY NOTIFICATION] Error: {e}")

async def send_subscription_reminder_notification(user_id: str, user_data: dict):
    """Send reminder notification to user about subscription expiry (legacy - kept for backward compatibility)"""
    try:
        user_name = get_user_first_name(user_data)
        subscription_plan = user_data.get("subscriptionPlan", "Unknown Plan")
        
        # Create notification data
        notification_data = {
            "userId": user_id,
            "title": "Subscription Expiring Soon",
            "body": f"Hi {user_name}, your {subscription_plan} subscription will expire in 1 week. Renew now to continue your fitness journey!",
            "type": "subscription_reminder",
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        # Save notification to Firestore
        firestore_db.collection("notifications").add(notification_data)
        
        # Send push notification if FCM token exists
        fcm_token = user_data.get("fcmToken")
        if fcm_token:
            await send_push_notification(
                fcm_token,
                "Subscription Expiring Soon",
                f"Hi {user_name}, your {subscription_plan} subscription will expire in 1 week. Renew now to continue your fitness journey!"
            )
            
    except Exception as e:
        logger.error(f"[SUBSCRIPTION REMINDER NOTIFICATION] Error: {e}")

async def activate_pending_plan_switch(user_id: str, user_data: dict):
    """Activate a pending plan switch when current plan ends"""
    try:
        pending_switch = user_data.get("pendingPlanSwitch")
        if not pending_switch:
            return False
        
        new_plan_id = pending_switch.get("newPlanId")
        switch_date_str = pending_switch.get("switchDate")
        plan_amount = pending_switch.get("amount", 0.0)
        
        if not new_plan_id or not switch_date_str:
            logger.error(f"[PLAN SWITCH] Invalid pending switch data for user {user_id}")
            return False
        
        # Parse switch date (should be the end date of current plan)
        switch_date = datetime.fromisoformat(switch_date_str)
        now = datetime.now()
        
        # Only activate if we're at or past the switch date
        if now < switch_date:
            return False
        
        # Calculate new plan dates starting from switch date
        if new_plan_id == "1month":
            new_end_date = switch_date + timedelta(days=30)  # 1 month = 30 days
        elif new_plan_id == "2months":
            new_end_date = switch_date + timedelta(days=60)  # 2 months = 60 days
        elif new_plan_id == "3months":
            new_end_date = switch_date + timedelta(days=90)  # 3 months = 90 days
        elif new_plan_id == "6months":
            new_end_date = switch_date + timedelta(days=180)  # 6 months = 180 days
        else:
            logger.error(f"[PLAN SWITCH] Invalid plan ID {new_plan_id} for user {user_id}")
            return False
        
        # Update user profile with new plan
        # NOTE: Do NOT add to totalAmountPaid here - will be added when this plan ends (Phase 4)
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        update_data = {
            "subscriptionPlan": new_plan_id,
            "subscriptionStartDate": switch_date.isoformat(),
            "subscriptionEndDate": new_end_date.isoformat(),
            "currentSubscriptionAmount": plan_amount,
            "totalAmountPaid": current_total,  # Keep existing total, don't add yet
            "isSubscriptionActive": True,
            "subscriptionStatus": "active",
            "pendingPlanSwitch": None,  # Clear pending switch
            "nextPlanId": None,
            "lastPaymentReminderSent": {  # Reset reminder flags for new plan
                "oneWeek": False,
                "twoDays": False,
                "oneDay": False
            }
        }
        
        firestore_db.collection("user_profiles").document(user_id).update(update_data)
        
        # Send notification about plan switch
        user_name = get_user_first_name(user_data)
        old_plan_name = get_plan_name(user_data.get("subscriptionPlan", "Unknown Plan"))
        new_plan_name = get_plan_name(new_plan_id)
        
        notification_data = {
            "userId": user_id,
            "title": "Plan Switched",
            "body": f"Hi {user_name}, your {old_plan_name} has ended. Your subscription has been switched to {new_plan_name}. Your new plan is now active!",
            "type": "plan_switched",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "data": {
                "oldPlan": user_data.get("subscriptionPlan"),
                "newPlan": new_plan_id,
                "oldPlanName": old_plan_name,
                "newPlanName": new_plan_name
            }
        }
        firestore_db.collection("notifications").add(notification_data)
        
        # Send push notification to user using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id=user_id,
            title="Plan Switched",
            body=f"Hi {user_name}, your {old_plan_name} has ended. Switched to {new_plan_name}. Your new plan is now active!",
            data={
                "type": "plan_switched",
                "oldPlan": user_data.get("subscriptionPlan"),
                "newPlan": new_plan_id,
                "oldPlanName": old_plan_name,
                "newPlanName": new_plan_name
            }
        )
        
        if not success:
            logger.warning(f"[PLAN SWITCH] Failed to send push notification to user {user_id}")
        
        # Send notification to dietician
        # Get updated user data to include current totalAmountPaid
        updated_user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if updated_user_doc.exists:
            updated_user_data = updated_user_doc.to_dict()
            await send_dietician_subscription_notification(user_id, updated_user_data, "plan_switched", new_plan_name, 0.0, old_plan_name)
        
        logger.info(f"[PLAN SWITCH] Successfully activated {new_plan_id} plan for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"[PLAN SWITCH] Error activating pending plan switch for user {user_id}: {e}")
        return False

async def auto_renew_subscription(user_id: str, user_data: dict):
    """Automatically renew a user's subscription when it expires"""
    try:
        # First check if there's a pending plan switch - activate that instead
        switch_activated = await activate_pending_plan_switch(user_id, user_data)
        if switch_activated:
            logger.info(f"[AUTO RENEWAL] Activated pending plan switch for user {user_id} instead of renewing")
            return
        
        user_name = get_user_first_name(user_data)
        current_plan = user_data.get("subscriptionPlan")
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        if not current_plan:
            logger.error(f"[AUTO RENEWAL] No current plan found for user {user_id}")
            return
        
        # Get plan details
        plan_prices = {
            "1month": 5000.0,
            "2months": 9000.0,
            "3months": 12000.0,
            "6months": 20000.0
        }
        
        if current_plan not in plan_prices:
            logger.error(f"[AUTO RENEWAL] Invalid plan {current_plan} for user {user_id}")
            return
        
        # Calculate new subscription dates
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        if current_plan == "1month":
            end_date = start_date + timedelta(days=30)  # 1 month = 30 days
        elif current_plan == "2months":
            end_date = start_date + timedelta(days=60)  # 2 months = 60 days
        elif current_plan == "3months":
            end_date = start_date + timedelta(days=90)  # 3 months = 90 days
        elif current_plan == "6months":
            end_date = start_date + timedelta(days=180)  # 6 months = 180 days
        
        # NOTE: Do NOT add to totalAmountPaid here - will be added when plan ends (Phase 4)
        # Keep existing total for now
        new_total = current_total  # Payment will be added at plan end
        
        # Update user profile with renewed subscription
        update_data = {
            "subscriptionStartDate": start_date.isoformat(),
            "subscriptionEndDate": end_date.isoformat(),
            "currentSubscriptionAmount": plan_prices[current_plan],
            "totalAmountPaid": new_total,  # Keep existing total
            "isSubscriptionActive": True,
            "subscriptionStatus": "active",
            "lastPaymentReminderSent": {  # Reset reminder flags for renewed plan
                "oneWeek": False,
                "twoDays": False,
                "oneDay": False
            }
        }
        
        firestore_db.collection("user_profiles").document(user_id).update(update_data)
        
        # Send renewal notifications to both user and dietician
        await send_subscription_renewal_notifications(user_id, user_data, current_plan, plan_prices[current_plan])
        
        logger.info(f"[AUTO RENEWAL] Successfully renewed {current_plan} subscription for user {user_id}")
        
    except Exception as e:
        logger.error(f"[AUTO RENEWAL] Error renewing subscription for user {user_id}: {e}")

async def send_dietician_subscription_notification(user_id: str, user_data: dict, event_type: str, plan_name: str = "", amount: float = 0.0, old_plan_name: str = ""):
    """Send subscription event notification to dietician
    event_type: 'trial_started', 'plan_started', 'plan_renewed', 'plan_switched', 'plan_expired', 'trial_expired'
    """
    try:
        user_name = get_user_first_name(user_data)
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        # Build clear notification messages with user info, old/new plans, and amount due
        if event_type == "trial_started":
            title = "User Started Free Trial"
            body = f"{user_name} started a free trial.\n\nAmount Due: ₹{current_total:,.0f}"
        elif event_type == "plan_started":
            title = "User Started Plan"
            body = f"{user_name} started {plan_name}.\n\nPlan: {plan_name}\nAmount Due: ₹{current_total:,.0f}"
        elif event_type == "plan_renewed":
            title = "User Plan Auto-Renewed"
            body = f"{user_name} plan auto-renewed.\n\nPlan: {plan_name}\nRenewal Amount: ₹{amount:,.0f}\nTotal Amount Due: ₹{current_total:,.0f}"
        elif event_type == "plan_switched":
            title = "User Plan Switched"
            body = f"{user_name} switched plans.\n\nOld Plan: {old_plan_name}\nNew Plan: {plan_name}\nAmount Due: ₹{current_total:,.0f}"
        elif event_type == "plan_expired":
            title = "User Plan Expired"
            body = f"{user_name} plan expired.\n\nExpired Plan: {plan_name}\nAmount Due: ₹{current_total:,.0f}"
        elif event_type == "trial_expired":
            title = "User Trial Expired"
            body = f"{user_name} free trial expired.\n\nAmount Due: ₹{current_total:,.0f}"
        else:
            return  # Unknown event type
        
        # Prepare notification data for push notification
        notification_data = {
            "type": f"user_{event_type}",
            "userId": user_id,
            "userName": user_name,
            "planName": plan_name,
            "oldPlanName": old_plan_name if old_plan_name else "",
            "amount": amount,
            "totalAmountDue": current_total
        }
        
        # Send notification to dietician (Firestore)
        dietician_notification = {
            "userId": "dietician",  # Special ID for dietician
            "title": title,
            "body": body,
            "type": f"user_{event_type}",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "data": notification_data
        }
        
        firestore_db.collection("notifications").add(dietician_notification)
        
        # Send push notification to dietician using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id="dietician",  # Special ID for dietician
            title=title,
            body=body,
            data=notification_data
        )
        
        if not success:
            logger.warning(f"[DIETICIAN SUBSCRIPTION NOTIFICATION] Failed to send push notification to dietician for event: {event_type}")
            
    except Exception as e:
        logger.error(f"[DIETICIAN SUBSCRIPTION NOTIFICATION] Error: {e}")

async def send_subscription_renewal_notifications(user_id: str, user_data: dict, plan_id: str, amount: float):
    """Send renewal notifications to both user and dietician"""
    try:
        user_name = get_user_first_name(user_data)
        plan_name = get_plan_name(plan_id)
        
        # Send notification to user
        user_notification = {
            "userId": user_id,
            "title": "Subscription Auto-Renewed",
            "body": f"Hi {user_name}, your {plan_name} has ended. Automatically renewed to {plan_name}. Your subscription continues seamlessly! Amount: ₹{amount:,.0f}",
            "type": "subscription_renewed",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "data": {
                "planId": plan_id,
                "planName": plan_name,
                "amount": amount,
                "oldPlan": plan_id,
                "newPlan": plan_id
            }
        }
        
        firestore_db.collection("notifications").add(user_notification)
        
        # Send push notification to user using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id=user_id,
            title="Subscription Auto-Renewed",
            body=f"Hi {user_name}, your {plan_name} has ended. Automatically renewed to {plan_name}. Your subscription continues seamlessly!",
            data={
                "type": "subscription_renewed",
                "planId": plan_id,
                "planName": plan_name,
                "amount": amount
            }
        )
        
        if not success:
            logger.warning(f"[SUBSCRIPTION RENEWAL] Failed to send push notification to user {user_id}")
        
        # Send notification to dietician
        await send_dietician_subscription_notification(user_id, user_data, "plan_renewed", plan_name, amount)
            
    except Exception as e:
        logger.error(f"[SUBSCRIPTION RENEWAL NOTIFICATIONS] Error: {e}")

async def send_subscription_expiry_notifications(user_id: str, user_data: dict):
    """Send expiry notifications to both user and dietician and mark subscription as expired"""
    try:
        user_name = get_user_first_name(user_data)
        subscription_plan = user_data.get("subscriptionPlan", "Unknown Plan")
        
        # Get plan name for better messaging
        plan_name = get_plan_name(subscription_plan) if subscription_plan else "subscription"
        
        # Get payment amount that was added (if any)
        current_amount = user_data.get("currentSubscriptionAmount", 0.0)
        payment_info = ""
        if current_amount > 0:
            payment_info = f" ₹{current_amount:,.0f} has been added to your total amount due."
        
        # IMPORTANT: Mark subscription as expired and inactive when auto-renewal is disabled
        # This ensures the subscription doesn't remain "active" after expiry
        firestore_db.collection("user_profiles").document(user_id).update({
            "isSubscriptionActive": False,
            "subscriptionStatus": "expired"
        })
        logger.info(f"[SUBSCRIPTION EXPIRY] Marked subscription as expired for user {user_id} (auto-renewal disabled)")
        
        # Send notification to user
        user_notification = {
            "userId": user_id,
            "title": "Plan Ended",
            "body": f"Hi {user_name}, your {plan_name} has ended.{payment_info} Select a new plan to continue enjoying premium features like personalized diet plans, AI chatbot, and custom notifications.",
            "type": "subscription_expired",
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "data": {
                "planId": subscription_plan,
                "planName": plan_name,
                "paymentAmount": current_amount
            }
        }
        
        firestore_db.collection("notifications").add(user_notification)
        
        # Send push notification to user using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        user_success = notification_service.send_notification(
            recipient_id=user_id,
            title="Subscription Expired",
            body=f"Hi {user_name}, your {plan_name} has ended. Select a new plan to continue!",
            data={
                "type": "subscription_expired",
                "planId": subscription_plan,
                "planName": plan_name,
                "paymentAmount": current_amount
            }
        )
        
        if not user_success:
            logger.warning(f"[SUBSCRIPTION EXPIRY] Failed to send push notification to user {user_id}")
        
        # Send notification to dietician
        await send_dietician_subscription_notification(user_id, user_data, "plan_expired", plan_name)
            
    except Exception as e:
        logger.error(f"[SUBSCRIPTION EXPIRY NOTIFICATIONS] Error: {e}")

async def send_new_subscription_notification(user_id: str, user_data: dict, plan_id: str):
    """Send notification to dietician about new subscription"""
    try:
        user_name = get_user_first_name(user_data)
        plan_name = get_plan_name(plan_id)
        
        # Send notification to dietician
        dietician_notification = {
            "userId": "dietician",  # Special ID for dietician
            "title": "New Subscription",
            "body": f"User {user_name} ({user_id}) has subscribed to {plan_name}.",
            "type": "new_subscription",
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        firestore_db.collection("notifications").add(dietician_notification)
        
        # Send push notification to dietician using SimpleNotificationService (same as messages/appointments)
        notification_service = get_notification_service(firestore_db)
        success = notification_service.send_notification(
            recipient_id="dietician",  # Special ID for dietician
            title="New Subscription",
            body=f"User {user_name} ({user_id}) has subscribed to {plan_name}.",
            data={
                "type": "new_subscription",
                "userId": user_id,
                "userName": user_name,
                "planName": plan_name
            }
        )
        
        if not success:
            logger.warning(f"[NEW SUBSCRIPTION NOTIFICATION] Failed to send push notification to dietician")
            
    except Exception as e:
        logger.error(f"[NEW SUBSCRIPTION NOTIFICATION] Error: {e}")

def get_plan_name(plan_id: str) -> str:
    """Get plan name from plan ID"""
    plan_names = {
        "1month": "1 Month Plan",
        "2months": "2 Months Plan",
        "3months": "3 Months Plan",
        "6months": "6 Months Plan"
    }
    return plan_names.get(plan_id, "Unknown Plan")

# Start scheduled job (check every 6 hours)
import asyncio
import threading
import time

async def notification_scheduler_job():
    """
    Scheduled job to send due notifications and clean up old ones.
    This runs every minute to check for notifications that need to be sent.
    """
    try:
        if FIREBASE_AVAILABLE and firestore_db:
            scheduler = get_notification_scheduler(firestore_db)
            
            # Send due notifications
            sent_count = await scheduler.send_due_notifications()
            
            # Clean up old notifications (run once per hour)
            if datetime.now().minute == 0:  # Only run at the top of each hour
                await scheduler.cleanup_old_notifications()
                
    except Exception as e:
        print(f"[Notification Scheduler] Error: {e}")

# --- Subscription Endpoints ---

@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    try:
        plans = [
            {
                "planId": "free",
                "name": "Free Plan",
                "duration": "Forever",
                "price": 0.0,
                "description": "Basic features to get you started",
                "features": [
                    "Basic food logging",
                    "Basic workout tracking",
                    "Step counting",
                    "Basic progress tracking"
                ],
                "isFree": True
            },
            {
                "planId": "1month", 
                "name": "1 Month Plan",
                "duration": "1 month",
                "price": 5000.0,
                "description": "Access to premium features for 1 month",
                "features": [
                    "Personalized diet plans",
                    "AI Chatbot support",
                    "Advanced notifications",
                    "Priority support",
                    "Detailed analytics",
                    "Custom meal planning",
                    "Progress reports"
                ],
                "isFree": False
            },
            {
                "planId": "2months", 
                "name": "2 Months Plan",
                "duration": "2 months",
                "price": 9000.0,
                "description": "Access to premium features for 2 months",
                "features": [
                    "Personalized diet plans",
                    "AI Chatbot support",
                    "Advanced notifications",
                    "Priority support",
                    "Detailed analytics",
                    "Custom meal planning",
                    "Progress reports"
                ],
                "isFree": False
            },
            {
                "planId": "3months", 
                "name": "3 Months Plan",
                "duration": "3 months",
                "price": 12000.0,
                "description": "Access to premium features for 3 months",
                "features": [
                    "Personalized diet plans",
                    "AI Chatbot support",
                    "Advanced notifications",
                    "Priority support",
                    "Detailed analytics",
                    "Custom meal planning",
                    "Progress reports",
                    "Nutritional counseling"
                ],
                "isFree": False
            },
            {
                "planId": "6months", 
                "name": "6 Months Plan",
                "duration": "6 months",
                "price": 20000.0,
                "description": "Access to premium features for 6 months",
                "features": [
                    "Personalized diet plans",
                    "AI Chatbot support",
                    "Advanced notifications",
                    "Priority support",
                    "Detailed analytics",
                    "Custom meal planning",
                    "Progress reports",
                    "Nutritional counseling",
                    "Monthly check-ins",
                    "Priority customer support"
                ],
                "isFree": False
            }
        ]
        return {"plans": plans}
    except Exception as e:
        logger.error(f"[GET SUBSCRIPTION PLANS] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription plans")

@api_router.post("/subscription/select")
async def select_subscription(request: SelectSubscriptionRequest):
    """Select a subscription plan for a user"""
    try:
        check_firebase_availability()
        
        # Get plan details
        plan_prices = {
            "1month": 5000.0,
            "2months": 9000.0,
            "3months": 12000.0,
            "6months": 20000.0
        }
        
        if request.planId not in plan_prices:
            raise HTTPException(status_code=400, detail="Invalid plan ID")
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(request.userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        # Check if user is a dietician (prevent dieticians from subscribing)
        user_email = user_data.get("email", "")
        if user_email == "dietician@nutricious4u.com" or "dietician" in user_email.lower():
            raise HTTPException(status_code=403, detail="Dieticians cannot subscribe to plans")
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        # Calculate subscription dates
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        if request.planId == "1month":
            end_date = start_date + timedelta(days=30)  # 1 month = 30 days
        elif request.planId == "2months":
            end_date = start_date + timedelta(days=60)  # 2 months = 60 days
        elif request.planId == "3months":
            end_date = start_date + timedelta(days=90)  # 3 months = 90 days
        elif request.planId == "6months":
            end_date = start_date + timedelta(days=180)  # 6 months = 180 days
        
        # Check if user already has an active subscription
        has_active_subscription = user_data.get("isSubscriptionActive", False)
        current_subscription_end = user_data.get("subscriptionEndDate")
        current_plan = user_data.get("subscriptionPlan")
        
        # If user has active subscription, store as pending plan switch (deferred activation)
        if has_active_subscription and current_subscription_end and current_plan and current_plan != "trial":
            # Parse current end date
            current_end_date = datetime.fromisoformat(current_subscription_end)
            
            # If switching to the same plan, treat it as renewal and enable auto-renewal
            if request.planId == current_plan:
                # Enable auto-renewal and clear any pending switch
                firestore_db.collection("user_profiles").document(request.userId).update({
                    "autoRenewalEnabled": True,
                    "pendingPlanSwitch": None,
                    "nextPlanId": None,
                    "subscriptionStatus": "active"
                })
                
                plan_name = get_plan_name(request.planId)
                message = f"Auto-renewal enabled! Your {plan_name} will automatically renew when it expires."
                
                return SubscriptionResponse(
                    success=True,
                    message=message,
                    subscription={
                        "planId": request.planId,
                        "autoRenewalEnabled": True,
                        "isRenewal": True
                    }
                )
            
            # Calculate new plan dates starting from current plan end
            if request.planId == "1month":
                new_end_date = current_end_date + timedelta(days=30)  # 1 month = 30 days
            elif request.planId == "2months":
                new_end_date = current_end_date + timedelta(days=60)  # 2 months = 60 days
            elif request.planId == "3months":
                new_end_date = current_end_date + timedelta(days=90)  # 3 months = 90 days
            elif request.planId == "6months":
                new_end_date = current_end_date + timedelta(days=180)  # 6 months = 180 days
            else:
                new_end_date = current_end_date
            
            # Store as pending plan switch
            # Use autoRenewalEnabled from request, default to True if not provided
            auto_renewal = request.autoRenewalEnabled if request.autoRenewalEnabled is not None else True
            
            pending_switch = {
                "newPlanId": request.planId,
                "switchDate": current_end_date.isoformat(),  # When current plan ends
                "amount": plan_prices[request.planId]
            }
            
            update_data = {
                "pendingPlanSwitch": pending_switch,
                "nextPlanId": request.planId,
                "subscriptionStatus": "pending_switch",
                "autoRenewalEnabled": auto_renewal  # Set auto-renewal for the new plan
            }
            
            firestore_db.collection("user_profiles").document(request.userId).update(update_data)
            
            plan_name = get_plan_name(request.planId)
            message = f"Plan switch scheduled! Your {plan_name} will activate after your current plan ends on {current_end_date.strftime('%B %d, %Y')}."
            
            return SubscriptionResponse(
                success=True,
                message=message,
                subscription={
                    "planId": request.planId,
                    "switchDate": current_end_date.isoformat(),
                    "amountPaid": plan_prices[request.planId],
                    "isPendingSwitch": True
                }
            )
        
        # User has NO active subscription - activate immediately
        # NOTE: Do NOT add to totalAmountPaid here - will be added when plan ends (Phase 4)
        # Use autoRenewalEnabled from request, default to True if not provided
        auto_renewal = request.autoRenewalEnabled if request.autoRenewalEnabled is not None else True
        
        update_data = {
            "subscriptionPlan": request.planId,
            "subscriptionStartDate": start_date.isoformat(),
            "subscriptionEndDate": end_date.isoformat(),
            "currentSubscriptionAmount": plan_prices[request.planId],
            "totalAmountPaid": current_total,  # Keep existing total, don't add yet
            "isSubscriptionActive": True,
            "subscriptionStatus": "active",
            "autoRenewalEnabled": auto_renewal,  # Set auto-renewal preference
            "pendingPlanSwitch": None,  # Clear any pending switch
            "nextPlanId": None
        }
        
        firestore_db.collection("user_profiles").document(request.userId).update(update_data)
        
        # Send notification to dietician about new subscription
        # Get updated user data to include current totalAmountPaid
        updated_user_doc = firestore_db.collection("user_profiles").document(request.userId).get()
        if updated_user_doc.exists:
            updated_user_data = updated_user_doc.to_dict()
            plan_name = get_plan_name(request.planId)
            await send_dietician_subscription_notification(request.userId, updated_user_data, "plan_started", plan_name)
        
        message = f"Successfully subscribed to {get_plan_name(request.planId)}. Your plan is now active!"
        
        return SubscriptionResponse(
            success=True,
            message=message,
            subscription={
                "planId": request.planId,
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "amountPaid": plan_prices[request.planId],
                "totalAmountPaid": current_total
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[SELECT SUBSCRIPTION] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to select subscription")

@api_router.get("/subscription/status/{userId}")
async def get_subscription_status(userId: str):
    """Get subscription status for a user"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        # Check trial status
        free_trial_used = user_data.get("freeTrialUsed", False)
        trial_end_date = user_data.get("freeTrialEndDate")
        is_trial_active = False
        requires_plan_selection = False
        
        # Check subscription status
        subscription_status = user_data.get("subscriptionStatus")
        is_subscription_active = user_data.get("isSubscriptionActive", False)
        subscription_plan = user_data.get("subscriptionPlan")
        
        # Determine if plan selection is required
        # 1. If subscription was cancelled
        if subscription_status == "cancelled":
            requires_plan_selection = True
        # 2. If trial expired and no active plan
        elif trial_end_date:
            trial_end = datetime.fromisoformat(trial_end_date)
            if datetime.now() < trial_end:
                is_trial_active = True
            else:
                # Trial expired, check if user has selected a plan
                if not is_subscription_active or subscription_plan == "trial":
                    requires_plan_selection = True
        # 3. If subscription expired and no active plan (and not cancelled)
        elif not is_subscription_active and subscription_status != "cancelled":
            # Check if user had a paid plan that expired
            if subscription_plan and subscription_plan not in ["free", "trial", None]:
                requires_plan_selection = True
        
        subscription_data = {
            "subscriptionPlan": user_data.get("subscriptionPlan"),
            "subscriptionStartDate": user_data.get("subscriptionStartDate"),
            "subscriptionEndDate": user_data.get("subscriptionEndDate"),
            "currentSubscriptionAmount": user_data.get("currentSubscriptionAmount", 0.0),
            "totalAmountPaid": user_data.get("totalAmountPaid", 0.0),
            "isSubscriptionActive": user_data.get("isSubscriptionActive", False),
            "isFreeUser": not user_data.get("isSubscriptionActive", False),
            "autoRenewalEnabled": user_data.get("autoRenewalEnabled", True),  # Default to True
            # New subscription system fields
            "freeTrialUsed": free_trial_used,
            "isTrialActive": is_trial_active,
            "trialEndDate": trial_end_date,
            "pendingPlanSwitch": user_data.get("pendingPlanSwitch"),
            "nextPlanId": user_data.get("nextPlanId"),
            "subscriptionStatus": user_data.get("subscriptionStatus"),
            "requiresPlanSelection": requires_plan_selection
        }
        
        # Log the data being returned for debugging
        logger.info(f"[GET SUBSCRIPTION STATUS] User: {userId}, Total Amount: {subscription_data['totalAmountPaid']}, End Date: {subscription_data['subscriptionEndDate']}, Trial Active: {is_trial_active}")
        
        # Check if subscription is still active
        if subscription_data["subscriptionEndDate"]:
            end_date = datetime.fromisoformat(subscription_data["subscriptionEndDate"])
            if datetime.now() > end_date:
                # Update subscription status to inactive
                firestore_db.collection("user_profiles").document(userId).update({
                    "isSubscriptionActive": False,
                    "subscriptionStatus": "expired"
                })
                subscription_data["isSubscriptionActive"] = False
                subscription_data["subscriptionStatus"] = "expired"
                # If subscription expired and no plan selected, require plan selection
                # Check if it was a paid plan (not free or trial)
                if subscription_data["subscriptionPlan"] in ["trial"] or (
                    subscription_data["subscriptionPlan"] and 
                    subscription_data["subscriptionPlan"] not in ["free", None]
                ):
                    subscription_data["requiresPlanSelection"] = True
                    requires_plan_selection = True  # Update local variable too
        
        return subscription_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[GET SUBSCRIPTION STATUS] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

@api_router.post("/subscription/cancel/{userId}")
async def cancel_subscription(userId: str):
    """Cancel a user's subscription and revert to free plan"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        # Check if user has an active subscription to cancel
        if not user_data.get("isSubscriptionActive", False):
            raise HTTPException(status_code=400, detail="No active subscription to cancel")
        
        # Cancel diet notifications when subscription is cancelled
        cancelled_notifications_count = 0
        try:
            logger.info(f"[CANCEL SUBSCRIPTION] Marking diet notifications as cancelled for user {userId}")
            
            # Since backend scheduler is disabled, mark notifications as cancelled in Firestore
            user_notifications_ref = firestore_db.collection("user_notifications").document(userId)
            user_notifications_doc = user_notifications_ref.get()
            
            if user_notifications_doc.exists:
                notifications_data = user_notifications_doc.to_dict()
                diet_notifications = notifications_data.get("diet_notifications", [])
                
                # Mark all notifications as cancelled
                for notification in diet_notifications:
                    notification["status"] = "cancelled"
                    notification["cancelled_at"] = datetime.now().isoformat()
                
                # Update the document
                user_notifications_ref.update({
                    "diet_notifications": diet_notifications,
                    "cancelled_at": datetime.now().isoformat()
                })
                
                cancelled_notifications_count = len(diet_notifications)
                logger.info(f"[CANCEL SUBSCRIPTION] Marked {cancelled_notifications_count} diet notifications as cancelled in Firestore for user {userId}")
            else:
                logger.info(f"[CANCEL SUBSCRIPTION] No diet notifications found for user {userId}")
                
        except Exception as e:
            logger.error(f"[CANCEL SUBSCRIPTION] Error cancelling diet notifications for user {userId}: {e}")
            # Don't fail the subscription cancellation if notification cancellation fails
        
        # Cancel subscription by setting it to inactive and clearing plan
        # NOTE: Do NOT set subscriptionPlan to "free" - keep it as None so requiresPlanSelection is triggered
        cancel_data = {
            "isSubscriptionActive": False,
            "subscriptionPlan": None,  # Keep as None (not "free") to trigger plan selection popup
            "subscriptionStartDate": None,
            "subscriptionEndDate": None,
            "currentSubscriptionAmount": 0.0,
            "subscriptionStatus": "cancelled",  # Mark as cancelled to trigger mandatory popup
            "pendingPlanSwitch": None,  # Clear any pending plan switch
            "nextPlanId": None
        }
        
        firestore_db.collection("user_profiles").document(userId).update(cancel_data)
        
        # Include notification count in success message
        message = f"Subscription cancelled successfully. Please select a new plan to continue."
        if cancelled_notifications_count > 0:
            message += f" {cancelled_notifications_count} diet notifications have been cancelled."
        
        return {
            "success": True, 
            "message": message,
            "cancelled_notifications": cancelled_notifications_count
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[CANCEL SUBSCRIPTION] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@api_router.post("/subscription/cancel-plan-switch/{userId}")
async def cancel_plan_switch(userId: str):
    """Cancel a pending plan switch"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        pending_switch = user_data.get("pendingPlanSwitch")
        
        if not pending_switch:
            raise HTTPException(status_code=400, detail="No pending plan switch found")
        
        # Clear pending plan switch
        firestore_db.collection("user_profiles").document(userId).update({
            "pendingPlanSwitch": None,
            "nextPlanId": None,
            "subscriptionStatus": "active"  # Revert to active status
        })
        
        logger.info(f"[CANCEL PLAN SWITCH] Cancelled pending plan switch for user {userId}")
        
        return {
            "success": True,
            "message": "Plan switch cancelled successfully. Your current plan will continue."
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[CANCEL PLAN SWITCH] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel plan switch")

@api_router.post("/subscription/toggle-auto-renewal/{userId}")
async def toggle_auto_renewal(userId: str, enabled: bool = True):
    """Toggle auto-renewal setting for a user"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update auto-renewal setting
        firestore_db.collection("user_profiles").document(userId).update({
            "autoRenewalEnabled": enabled
        })
        
        status = "enabled" if enabled else "disabled"
        return {"success": True, "message": f"Auto-renewal {status} successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[TOGGLE AUTO RENEWAL] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle auto-renewal")

@api_router.post("/subscription/reset/{userId}")
async def reset_subscription(userId: str):
    """Reset subscription data for a user (for testing purposes)"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Reset subscription data
        reset_data = {
            "subscriptionPlan": None,
            "subscriptionStartDate": None,
            "subscriptionEndDate": None,
            "currentSubscriptionAmount": 0.0,
            "totalAmountPaid": 0.0,
            "isSubscriptionActive": False
        }
        
        firestore_db.collection("user_profiles").document(userId).update(reset_data)
        
        return {"success": True, "message": "Subscription data reset successfully"}
        
    except Exception as e:
        logger.error(f"[RESET SUBSCRIPTION] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset subscription")

@api_router.post("/user/{userId}/reset-daily")
async def reset_daily_data(userId: str):
    """Reset daily tracking data for a user"""
    try:
        check_firebase_availability()
        
        # Get user profile to update lastFoodLogDate
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get today's date in UTC
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today.strftime('%Y-%m-%d')
        
        # Clear today's food logs to reset daily nutritional values
        food_logs_ref = firestore_db.collection(f"users/{userId}/food_logs")
        today_logs = food_logs_ref.where("timestamp", ">=", today).stream()
        
        deleted_count = 0
        for doc in today_logs:
            doc.reference.delete()
            deleted_count += 1
        
        # Update the lastFoodLogDate to today
        firestore_db.collection("user_profiles").document(userId).update({
            "lastFoodLogDate": today_str
        })
        
        logger.info(f"[DAILY RESET] Reset daily data for user {userId} on {today_str}. Deleted {deleted_count} food logs.")
        
        return {
            "success": True, 
            "message": f"Daily data reset successfully. Deleted {deleted_count} food logs.",
            "deleted_logs": deleted_count
        }
        
    except Exception as e:
        logger.error(f"[DAILY RESET] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset daily data")

@api_router.post("/subscription/add-amount/{userId}")
async def add_subscription_amount(userId: str, planId: str):
    """Add subscription amount to total due (only called from popup)"""
    try:
        check_firebase_availability()
        
        # Get plan details
        plan_prices = {
            "1month": 5000.0,
            "2months": 9000.0,
            "3months": 12000.0,
            "6months": 20000.0
        }
        
        if planId not in plan_prices:
            raise HTTPException(status_code=400, detail="Invalid plan ID")
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        current_total = user_data.get("totalAmountPaid", 0.0)
        
        # Add the plan amount to total
        new_total = current_total + plan_prices[planId]
        
        # Update only the total amount
        firestore_db.collection("user_profiles").document(userId).update({
            "totalAmountPaid": new_total
        })
        
        logger.info(f"[ADD SUBSCRIPTION AMOUNT] User: {userId}, Plan: {planId}, Amount Added: {plan_prices[planId]}, New Total: {new_total}")
        
        return {
            "success": True, 
            "message": f"Added ₹{plan_prices[planId]:,.0f} to total amount due",
            "amountAdded": plan_prices[planId],
            "newTotal": new_total
        }
        
    except Exception as e:
        logger.error(f"[ADD SUBSCRIPTION AMOUNT] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add subscription amount")

@api_router.delete("/users/{userId}/account")
async def delete_user_account(userId: str):
    """Delete a user account completely. Dietician accounts cannot be deleted."""
    try:
        check_firebase_availability()
        loop = asyncio.get_event_loop()
        
        # Get user profile to check if dietician and get diet PDF info
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_email = user_data.get("email", "")
        diet_pdf_filename = user_data.get("dietPdfUrl")  # Get filename before deletion
        
        # Check if user is dietician - prevent deletion
        is_dietician = (
            user_data.get("isDietician", False) or 
            user_email == "nutricious4u@gmail.com"
        )
        
        if is_dietician:
            logger.warning(f"[DELETE ACCOUNT] Attempted to delete dietician account: {userId}")
            raise HTTPException(status_code=403, detail="Dietician accounts cannot be deleted")
        
        logger.info(f"[DELETE ACCOUNT] Starting account deletion for user: {userId}")
        
        # Delete all user data from Firestore collections
        deleted_items = {}
        OPERATION_TIMEOUT = 10.0  # 10 seconds per operation
        
        # Helper function to delete with timeout
        async def delete_with_timeout(operation_name, operation_func):
            try:
                logger.info(f"[DELETE ACCOUNT] Starting: {operation_name} for {userId}")
                result = await asyncio.wait_for(operation_func(), timeout=OPERATION_TIMEOUT)
                logger.info(f"[DELETE ACCOUNT] Completed: {operation_name} for {userId}")
                return result
            except asyncio.TimeoutError:
                logger.warning(f"[DELETE ACCOUNT] Timeout ({OPERATION_TIMEOUT}s) for {operation_name} for {userId}")
                return None
        except Exception as e:
                logger.error(f"[DELETE ACCOUNT] Error in {operation_name} for {userId}: {e}")
                return None
        
        # Helper function to delete collection with batch operations
        async def delete_collection_batch(collection_ref, batch_size=500):
        try:
                docs = await loop.run_in_executor(executor, lambda: list(collection_ref.stream()))
            count = 0
                # Use batch operations for efficiency
                batch = firestore_db.batch()
                batch_count = 0
                for doc in docs:
                    batch.delete(doc.reference)
                    batch_count += 1
                    if batch_count >= batch_size:
                        await loop.run_in_executor(executor, batch.commit)
                        count += batch_count
                        batch = firestore_db.batch()
                        batch_count = 0
                if batch_count > 0:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                return count
            except Exception as e:
                logger.error(f"[DELETE ACCOUNT] Error in batch delete: {e}")
                return 0
        
        # 1. Delete food logs subcollection (parallel with routines)
        async def delete_food_logs():
            food_logs_ref = firestore_db.collection(f"users/{userId}/food_logs")
            count = await delete_collection_batch(food_logs_ref)
            deleted_items["food_logs"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} food logs for {userId}")
            return count
        
        # 2. Delete routines subcollection (parallel with food logs)
        async def delete_routines():
            routines_ref = firestore_db.collection(f"users/{userId}/routines")
            count = await delete_collection_batch(routines_ref)
            deleted_items["routines"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} routines for {userId}")
            return count
        
        # 3. Delete workout logs (parallel with notifications and appointments)
        async def delete_workout_logs():
            workout_logs_ref = firestore_db.collection("workout_logs")
            workout_logs = await loop.run_in_executor(
                executor, 
                lambda: list(workout_logs_ref.where("userId", "==", userId).stream())
            )
            count = 0
            batch = firestore_db.batch()
            batch_count = 0
            for doc in workout_logs:
                batch.delete(doc.reference)
                batch_count += 1
                if batch_count >= 500:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                    batch = firestore_db.batch()
                    batch_count = 0
            if batch_count > 0:
                await loop.run_in_executor(executor, batch.commit)
                count += batch_count
            deleted_items["workout_logs"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} workout logs for {userId}")
            return count
        
        # 4. Delete notifications (parallel with workout logs and appointments)
        async def delete_notifications():
            notifications_ref = firestore_db.collection("notifications")
            notifications = await loop.run_in_executor(
                executor,
                lambda: list(notifications_ref.where("userId", "==", userId).stream())
            )
            count = 0
            batch = firestore_db.batch()
            batch_count = 0
            for doc in notifications:
                batch.delete(doc.reference)
                batch_count += 1
                if batch_count >= 500:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                    batch = firestore_db.batch()
                    batch_count = 0
            if batch_count > 0:
                await loop.run_in_executor(executor, batch.commit)
                count += batch_count
            deleted_items["notifications"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} notifications for {userId}")
            return count
        
        # 5. Delete appointments (parallel with workout logs and notifications)
        async def delete_appointments():
            appointments_ref = firestore_db.collection("appointments")
            appointments = await loop.run_in_executor(
                executor,
                lambda: list(appointments_ref.where("userId", "==", userId).stream())
            )
            count = 0
            batch = firestore_db.batch()
            batch_count = 0
            for doc in appointments:
                batch.delete(doc.reference)
                batch_count += 1
                if batch_count >= 500:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                    batch = firestore_db.batch()
                    batch_count = 0
            if batch_count > 0:
                await loop.run_in_executor(executor, batch.commit)
                count += batch_count
            deleted_items["appointments"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} appointments for {userId}")
            return count
        
        # 6. Delete user_notifications collection (diet notifications)
        async def delete_user_notifications():
            user_notifications_ref = firestore_db.collection("user_notifications").document(userId)
            doc = await loop.run_in_executor(executor, user_notifications_ref.get)
            if doc.exists:
                await loop.run_in_executor(executor, user_notifications_ref.delete)
                deleted_items["user_notifications"] = True
                logger.info(f"[DELETE ACCOUNT] Deleted user_notifications for {userId}")
                return True
            else:
                deleted_items["user_notifications"] = False
                logger.info(f"[DELETE ACCOUNT] No user_notifications found for {userId}")
                return False
        
        # 7. Delete scheduled_notifications (where userId matches)
        async def delete_scheduled_notifications():
            scheduled_ref = firestore_db.collection("scheduled_notifications")
            scheduled = await loop.run_in_executor(
                executor,
                lambda: list(scheduled_ref.where("userId", "==", userId).stream())
            )
            count = 0
            batch = firestore_db.batch()
            batch_count = 0
            for doc in scheduled:
                batch.delete(doc.reference)
                batch_count += 1
                if batch_count >= 500:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                    batch = firestore_db.batch()
                    batch_count = 0
            if batch_count > 0:
                await loop.run_in_executor(executor, batch.commit)
                count += batch_count
            deleted_items["scheduled_notifications"] = count
            logger.info(f"[DELETE ACCOUNT] Deleted {count} scheduled notifications for {userId}")
            return count
        
        # 8. Delete diet PDF from Firebase Storage
        async def delete_diet_pdf():
            if diet_pdf_filename and bucket:
                try:
                    blob_path = f"diets/{userId}/{diet_pdf_filename}"
                    blob = bucket.blob(blob_path)
                    if blob.exists():
                        await loop.run_in_executor(executor, blob.delete)
                        deleted_items["diet_pdf_storage"] = True
                        logger.info(f"[DELETE ACCOUNT] Deleted diet PDF from Storage for {userId}: {blob_path}")
                        return True
                    else:
                        deleted_items["diet_pdf_storage"] = False
                        logger.info(f"[DELETE ACCOUNT] Diet PDF not found in Storage for {userId}: {blob_path}")
                        return False
                except Exception as e:
                    logger.warning(f"[DELETE ACCOUNT] Error deleting diet PDF from Storage for {userId}: {e}")
                    deleted_items["diet_pdf_storage"] = False
                    return False
            else:
                deleted_items["diet_pdf_storage"] = False
                return False
        
        # 9. Delete chat messages
        async def delete_chat_messages():
            chats_ref = firestore_db.collection("chats").document(userId)
            chat_doc = await loop.run_in_executor(executor, chats_ref.get)
            if chat_doc.exists:
                # Delete messages subcollection
                messages_ref = chats_ref.collection("messages")
                messages = await loop.run_in_executor(executor, lambda: list(messages_ref.stream()))
                count = 0
                batch = firestore_db.batch()
                batch_count = 0
                for doc in messages:
                    batch.delete(doc.reference)
                    batch_count += 1
                    if batch_count >= 500:
                        await loop.run_in_executor(executor, batch.commit)
                        count += batch_count
                        batch = firestore_db.batch()
                        batch_count = 0
                if batch_count > 0:
                    await loop.run_in_executor(executor, batch.commit)
                    count += batch_count
                # Delete chat document
                await loop.run_in_executor(executor, chats_ref.delete)
                deleted_items["chat_messages"] = count
                deleted_items["chat_document"] = True
                logger.info(f"[DELETE ACCOUNT] Deleted chat document and {count} messages for {userId}")
                return count
            else:
                deleted_items["chat_messages"] = 0
                deleted_items["chat_document"] = False
                return 0
        
        # Execute deletions in parallel groups for efficiency
        # Group 1: Subcollections (can run in parallel)
        logger.info(f"[DELETE ACCOUNT] Starting parallel deletion of subcollections for {userId}")
        await asyncio.gather(
            delete_with_timeout("food_logs", delete_food_logs),
            delete_with_timeout("routines", delete_routines),
            return_exceptions=True
        )
        
        # Group 2: Global collections (can run in parallel)
        logger.info(f"[DELETE ACCOUNT] Starting parallel deletion of global collections for {userId}")
        await asyncio.gather(
            delete_with_timeout("workout_logs", delete_workout_logs),
            delete_with_timeout("notifications", delete_notifications),
            delete_with_timeout("appointments", delete_appointments),
            return_exceptions=True
        )
        
        # Group 3: Notification-related data (can run in parallel)
        logger.info(f"[DELETE ACCOUNT] Starting parallel deletion of notification data for {userId}")
        await asyncio.gather(
            delete_with_timeout("user_notifications", delete_user_notifications),
            delete_with_timeout("scheduled_notifications", delete_scheduled_notifications),
            return_exceptions=True
        )
        
        # Group 4: Chat and storage (can run in parallel)
        logger.info(f"[DELETE ACCOUNT] Starting parallel deletion of chat and storage for {userId}")
        await asyncio.gather(
            delete_with_timeout("chat_messages", delete_chat_messages),
            delete_with_timeout("diet_pdf_storage", delete_diet_pdf),
            return_exceptions=True
        )
        
        # 10. Delete Firebase Auth user (before profile deletion)
        logger.info(f"[DELETE ACCOUNT] Starting Firebase Auth user deletion for {userId}")
        try:
            if firebase_auth is None:
                logger.warning(f"[DELETE ACCOUNT] Firebase Auth not available, skipping auth user deletion for {userId}")
                deleted_items["auth_user"] = False
            else:
                async def delete_auth():
                await loop.run_in_executor(executor, lambda: firebase_auth.delete_user(userId))
                await delete_with_timeout("auth_user", delete_auth)
                deleted_items["auth_user"] = True
                logger.info(f"[DELETE ACCOUNT] Deleted Firebase Auth user for {userId}")
        except Exception as e:
            logger.error(f"[DELETE ACCOUNT] Error deleting Firebase Auth user for {userId}: {e}")
            deleted_items["auth_user"] = False
            # Don't fail completely if auth deletion fails - data is already deleted
        
        # 11. Delete user profile LAST (after all data is deleted)
        logger.info(f"[DELETE ACCOUNT] Starting user profile deletion for {userId} (final step)")
        try:
            async def delete_profile():
                await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(userId).delete())
            await delete_with_timeout("user_profile", delete_profile)
            deleted_items["user_profile"] = True
            logger.info(f"[DELETE ACCOUNT] Deleted user profile for {userId}")
        except Exception as e:
            logger.error(f"[DELETE ACCOUNT] Error deleting user profile for {userId}: {e}")
            deleted_items["user_profile"] = False
        
        logger.info(f"[DELETE ACCOUNT] Account deletion completed for user: {userId}. Deleted items: {deleted_items}")
        
        return {
            "success": True,
            "message": "Account deleted successfully",
            "deleted_items": deleted_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE ACCOUNT] Error deleting account: {e}")
        import traceback
        logger.error(f"[DELETE ACCOUNT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to delete account")

# --- Free Trial Endpoints ---

@api_router.post("/subscription/activate-trial/{userId}")
async def activate_free_trial(userId: str):
    """Activate free trial for a user (one-time only)"""
    try:
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        # Check if user is a dietician (prevent dieticians from using trial)
        if user_data.get("isDietician", False):
            raise HTTPException(status_code=403, detail="Dieticians cannot activate free trials")
        
        # Check if trial was already used
        if user_data.get("freeTrialUsed", False):
            raise HTTPException(status_code=400, detail="Free trial has already been used. You can only use it once.")
        
        # Check if user is on a paid plan - only free plan users can activate trial
        is_subscription_active = user_data.get("isSubscriptionActive", False)
        subscription_plan = user_data.get("subscriptionPlan")
        # User is on paid plan if they have active subscription and plan is not "free" or "trial"
        if is_subscription_active and subscription_plan and subscription_plan not in ["free", "trial"]:
            raise HTTPException(status_code=400, detail="You already have an active paid subscription. Free trial is only available for free plan users.")
        
        # Calculate trial dates (3 days)
        from datetime import datetime, timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=3)  # 3 days trial period
        
        # Assign default diet to user
        default_diet_assigned = await assign_default_diet_to_user(userId, user_data)
        
        # Update user profile with trial information
        # Note: Do NOT set subscriptionStartDate/subscriptionEndDate for trial users
        # Only set freeTrialStartDate and freeTrialEndDate
        update_data = {
            "freeTrialUsed": True,
            "freeTrialStartDate": start_date.isoformat(),
            "freeTrialEndDate": end_date.isoformat(),
            "subscriptionPlan": "trial",
            "subscriptionStatus": "trial",
            "isSubscriptionActive": True,  # Active for feature access during trial
            # Do NOT set subscriptionStartDate/subscriptionEndDate for trial users
            # These should only be set for paid subscriptions
            "new_diet_received": True  # Trigger new diet popup
        }
        
        firestore_db.collection("user_profiles").document(userId).update(update_data)
        
        # Send notification to dietician
        await send_dietician_subscription_notification(userId, user_data, "trial_started")
        
        logger.info(f"[ACTIVATE TRIAL] Successfully activated free trial for user {userId}, ends at {end_date.isoformat()}")
        
        return {
            "success": True,
            "message": "Free trial activated successfully! You now have access to all premium features for 3 days.",
            "trial": {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "defaultDietAssigned": default_diet_assigned
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[ACTIVATE TRIAL] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate free trial")

@api_router.get("/subscription/trial-status/{userId}")
async def get_trial_status(userId: str):
    """Get free trial status for a user"""
    try:
        check_firebase_availability()
        
        user_doc = firestore_db.collection("user_profiles").document(userId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        free_trial_used = user_data.get("freeTrialUsed", False)
        trial_start = user_data.get("freeTrialStartDate")
        trial_end = user_data.get("freeTrialEndDate")
        
        # Check if trial is currently active
        is_trial_active = False
        time_remaining = 0
        
        if trial_end:
            from datetime import datetime
            end_date = datetime.fromisoformat(trial_end)
            now = datetime.now()
            if now < end_date:
                is_trial_active = True
                time_remaining = int((end_date - now).total_seconds())
        
        return {
            "hasUsedTrial": free_trial_used,
            "isTrialActive": is_trial_active,
            "trialStartDate": trial_start,
            "trialEndDate": trial_end,
            "timeRemaining": time_remaining  # seconds
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[TRIAL STATUS] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trial status")

async def assign_default_diet_to_user(user_id: str, user_data: dict):
    """Assign the free trial diet PDF to a user during free trial"""
    try:
        from datetime import datetime, timezone
        import os
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # Path to free trial diet PDF (relative to backend directory)
        # The PDF is in mobileapp/FREE TRIAL DIET.pdf
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)  # Go up one level from backend/
        trial_diet_path = os.path.join(project_root, "mobileapp", "FREE TRIAL DIET.pdf")
        
        if not os.path.exists(trial_diet_path):
            logger.error(f"[DEFAULT DIET] Free trial diet PDF not found at {trial_diet_path}")
            return False
        
        # Read the PDF file
        logger.info(f"[DEFAULT DIET] Reading free trial diet PDF from {trial_diet_path}")
        with open(trial_diet_path, 'rb') as f:
            pdf_data = f.read()
        
        # Create filename for the uploaded diet
        default_diet_filename = f"free_trial_diet_{user_id}_{datetime.now(timezone.utc).timestamp()}.pdf"
        
        # Upload PDF to Firebase Storage
        logger.info(f"[DEFAULT DIET] Uploading free trial diet PDF to Firebase Storage for user {user_id}")
        pdf_url = upload_diet_pdf(user_id, pdf_data, default_diet_filename)
        
        # Get current timestamp for lastDietUpload (trial start time)
        trial_start_time = datetime.now(timezone.utc).isoformat()
        
        # Update user profile with diet information
        diet_info = {
            "dietPdfUrl": default_diet_filename,  # Store filename, not signed URL (same as regular uploads)
            "lastDietUpload": trial_start_time,  # Set to trial start time for 3-day countdown
            "dieticianId": "system",  # System-assigned default diet
            "dietCacheVersion": datetime.now(timezone.utc).timestamp(),
            "new_diet_received": True
        }
        
        firestore_db.collection("user_profiles").document(user_id).update(diet_info)
        logger.info(f"[DEFAULT DIET] Updated user profile with diet info for user {user_id}")
        
        # Extract notifications from the diet PDF (same as when dietician uploads)
        try:
            logger.info(f"[DEFAULT DIET] Extracting notifications from free trial diet PDF for user {user_id}")
            notifications = diet_notification_service.extract_and_create_notifications(
                user_id, default_diet_filename, firestore_db
            )
            
            if notifications:
                # Store notifications in Firestore
                user_notifications_ref = firestore_db.collection("user_notifications").document(user_id)
                user_notifications_ref.set({
                    "diet_notifications": notifications,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "diet_pdf_url": default_diet_filename,
                }, merge=True)
                logger.info(f"[DEFAULT DIET] Extracted and stored {len(notifications)} notifications for user {user_id}")
            else:
                logger.warning(f"[DEFAULT DIET] No notifications found in free trial diet PDF for user {user_id}")
        except Exception as extract_error:
            logger.error(f"[DEFAULT DIET] Error extracting notifications: {extract_error}")
            # Continue even if extraction fails - diet is still assigned
        
        # Send notification about new diet (same as when dietician uploads)
        try:
            from services.simple_notification_service import get_notification_service
            notification_service = get_notification_service(firestore_db)
            notification_service.send_new_diet_notification(user_id, "System")
        except Exception as notif_error:
            logger.warning(f"[DEFAULT DIET] Failed to send notification: {notif_error}")
        
        logger.info(f"[DEFAULT DIET] Successfully assigned free trial diet to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"[DEFAULT DIET] Error assigning default diet to user {user_id}: {e}")
        import traceback
        logger.error(f"[DEFAULT DIET] Traceback: {traceback.format_exc()}")
        return False

@api_router.get("/notifications/{userId}")
async def get_user_notifications(userId: str):
    """Get notifications for a user"""
    try:
        check_firebase_availability()
        
        # Get notifications for the user (including dietician notifications if user is dietician)
        notifications_ref = firestore_db.collection("notifications")
        
        if userId == "dietician":
            # For dietician, get all notifications sent to dietician
            notifications = notifications_ref.where("userId", "==", "dietician").order_by("timestamp", direction="DESCENDING").limit(50).stream()
        else:
            # For regular users, get their notifications
            notifications = notifications_ref.where("userId", "==", userId).order_by("timestamp", direction="DESCENDING").limit(50).stream()
        
        notifications_list = []
        for notification in notifications:
            notification_data = notification.to_dict()
            notification_data["id"] = notification.id
            notifications_list.append(notification_data)
        
        return {"notifications": notifications_list}
        
    except Exception as e:
        logger.error(f"[GET NOTIFICATIONS] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@api_router.put("/notifications/{notificationId}/read")
async def mark_notification_read(notificationId: str):
    """Mark a notification as read"""
    try:
        check_firebase_availability()
        
        firestore_db.collection("notifications").document(notificationId).update({
            "read": True
        })
        
        return {"success": True, "message": "Notification marked as read"}
        
    except Exception as e:
        logger.error(f"[MARK NOTIFICATION READ] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@api_router.delete("/notifications/{notificationId}")
async def delete_notification(notificationId: str):
    """Delete a notification"""
    try:
        check_firebase_availability()
        
        firestore_db.collection("notifications").document(notificationId).delete()
        
        return {"success": True, "message": "Notification deleted"}
        
    except Exception as e:
        logger.error(f"[DELETE NOTIFICATION] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")



def run_scheduled_jobs():
    """Run scheduled jobs in a separate thread
    Runs every 6 hours to check for subscription reminders (1 week and 1 day before expiration)
    """
    # Run every 6 hours (21600 seconds) to check for reminders
    JOB_INTERVAL_SECONDS = 21600  # 6 hours
    
    while True:
        try:
            # Run the subscription reminders job
            asyncio.run(check_subscription_reminders_job())
        except Exception as e:
            print(f"[Scheduled Jobs] Error: {e}")
        
        # Wait before next check
        time.sleep(JOB_INTERVAL_SECONDS)

def run_diet_countdown_job():
    """Run diet countdown job separately (every 6 hours)"""
    while True:
        try:
            # Run the NEW diet countdown job (every 6 hours)
            asyncio.run(check_diet_countdown_job())
        except Exception as e:
            print(f"[Diet Countdown Job] Error: {e}")
        
        # Wait for 6 hours
        time.sleep(6 * 60 * 60)

def run_notification_scheduler():
    """Run notification scheduler in a separate thread (every minute)"""
    while True:
        try:
            # Run the notification scheduler job
            asyncio.run(notification_scheduler_job())
        except Exception as e:
            print(f"[Notification Scheduler] Error: {e}")
        
        # Wait for 1 minute
        time.sleep(60)

# Start the scheduled job threads
# Subscription reminders run every 6 hours to check for 1 week and 1 day reminders
scheduler_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
scheduler_thread.start()

# Diet countdown job runs separately every 6 hours
diet_countdown_thread = threading.Thread(target=run_diet_countdown_job, daemon=True)
diet_countdown_thread.start()

# DISABLED: Backend notification scheduler to prevent conflicts with local scheduling
# notification_scheduler_thread = threading.Thread(target=run_notification_scheduler, daemon=True)
# notification_scheduler_thread.start()
print("🔕 Backend notification scheduler DISABLED - using local scheduling only")

# Include the router in the main app (after all endpoints are defined)
# Add new endpoints for dietician user management
@api_router.get("/users/{user_id}/details")
async def get_user_details(user_id: str):
    """Get detailed user information for dietician view"""
    try:
        logger.info(f"[GET USER DETAILS] Request for user_id: {user_id}")
        check_firebase_availability()
        
        # Get user profile
        logger.info(f"[GET USER DETAILS] Fetching user profile from Firestore")
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        
        if not user_doc.exists:
            logger.warning(f"[GET USER DETAILS] User {user_id} not found in Firestore")
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        logger.info(f"[GET USER DETAILS] User data retrieved: {user_data}")
        
        # Calculate amount due (totalAmountPaid is the amount due, not paid)
        amount_due = user_data.get("totalAmountPaid", 0.0)
        
        # Get subscription details
        subscription_plan = user_data.get("subscriptionPlan")
        subscription_start_date = user_data.get("subscriptionStartDate")
        subscription_end_date = user_data.get("subscriptionEndDate")
        is_app_locked = user_data.get("isAppLocked", False)
        
        # Format plan name for display
        plan_names = {
            "2months": "2 Months Plan",
            "3months": "3 Months Plan",
            "6months": "6 Months Plan"
        }
        plan_display_name = plan_names.get(subscription_plan, subscription_plan or "No Plan")
        
        response_data = {
            "userId": user_id,
            "firstName": user_data.get("firstName", ""),
            "lastName": user_data.get("lastName", ""),
            "email": user_data.get("email", ""),
            "plan": plan_display_name,
            "startDate": subscription_start_date,
            "endDate": subscription_end_date,
            "amountDue": amount_due,
            "isAppLocked": is_app_locked
        }
        
        logger.info(f"[GET USER DETAILS] Returning response: {response_data}")
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[GET USER DETAILS] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user details")

@api_router.post("/users/{user_id}/mark-paid")
async def mark_user_paid(user_id: str):
    """Mark user's amount as paid (set totalAmountPaid to 0)"""
    try:
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update totalAmountPaid to 0 (marking as paid)
        firestore_db.collection("user_profiles").document(user_id).update({
            "totalAmountPaid": 0.0
        })
        
        logger.info(f"[MARK PAID] User {user_id} marked as paid")
        
        return {
            "success": True,
            "message": "User marked as paid successfully",
            "amountDue": 0.0
        }
        
    except Exception as e:
        logger.error(f"[MARK PAID] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark user as paid")

@api_router.post("/users/{user_id}/lock-app")
async def lock_user_app(user_id: str):
    """Lock user's app"""
    try:
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Lock the app
        firestore_db.collection("user_profiles").document(user_id).update({
            "isAppLocked": True
        })
        
        logger.info(f"[LOCK APP] User {user_id} app locked")
        
        return {
            "success": True,
            "message": "User app locked successfully",
            "isAppLocked": True
        }
        
    except Exception as e:
        logger.error(f"[LOCK APP] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to lock user app")

@api_router.post("/users/{user_id}/unlock-app")
async def unlock_user_app(user_id: str):
    """Unlock user's app"""
    try:
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
       
        
        # Unlock the app
        firestore_db.collection("user_profiles").document(user_id).update({
            "isAppLocked": False
        })
        
        logger.info(f"[UNLOCK APP] User {user_id} app unlocked")
        
        return {
            "success": True,
            "message": "User app unlocked successfully",
            "isAppLocked": False
        }
        
    except Exception as e:
        logger.error(f"[UNLOCK APP] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unlock user app")

@api_router.get("/users/{user_id}/lock-status")
async def get_user_lock_status(user_id: str):
    """Get user's app lock status"""
    try:
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        is_app_locked = user_data.get("isAppLocked", False)
        amount_due = user_data.get("totalAmountPaid", 0.0)
        
        return {
            "isAppLocked": is_app_locked,
            "amountDue": amount_due
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET LOCK STATUS] Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user lock status")

@api_router.get("/users/{user_id}/test")
async def test_user_exists(user_id: str):
    """Test endpoint to check if user exists in Firestore"""
    try:
        logger.info(f"[TEST USER] Checking if user {user_id} exists")
        check_firebase_availability()
        
        # Get user profile
        user_doc = firestore_db.collection("user_profiles").document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            logger.info(f"[TEST USER] User exists with data: {user_data}")
            return {
                "exists": True,
                "userId": user_id,
                "email": user_data.get("email", "No email"),
                "firstName": user_data.get("firstName", "No first name"),
                "lastName": user_data.get("lastName", "No last name")
            }
        else:
            logger.warning(f"[TEST USER] User {user_id} does not exist")
            return {
                "exists": False,
                "userId": user_id,
                "message": "User not found in Firestore"
            }
        
    except Exception as e:
        logger.error(f"[TEST USER] Error: {e}")
        return {
            "exists": False,
            "userId": user_id,
            "error": str(e)
        }

# Add a comprehensive test endpoint for iOS connection and diet functionality
@api_router.get("/test-ios-diet")
async def test_ios_diet_functionality():
    """Test endpoint for iOS diet functionality"""
    try:
        # Test Firebase connection
        if not FIREBASE_AVAILABLE:
            return {"status": "error", "message": "Firebase not available"}
        
        # Test basic Firestore operation
        test_doc = firestore_db.collection("test").document("ios_test")
        test_doc.set({"timestamp": datetime.now().isoformat()})
        
        return {
            "status": "success",
            "message": "iOS diet functionality test passed",
            "firebase_available": FIREBASE_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/recipes")
async def get_recipes():
    """Get all recipes from Firestore"""
    try:
        check_firebase_availability()
        
        # Use ThreadPoolExecutor for async Firestore operations
        with ThreadPoolExecutor() as executor:
            future = executor.submit(get_recipes_from_firestore)
            recipes = await asyncio.wrap_future(future)
        
        return {"recipes": recipes}
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recipes: {str(e)}")

@api_router.get("/debug-recipes")
async def debug_recipes():
    """Debug endpoint to check recipes collection"""
    try:
        check_firebase_availability()
        
        # Use ThreadPoolExecutor for async Firestore operations
        with ThreadPoolExecutor() as executor:
            future = executor.submit(debug_recipes_from_firestore)
            result = await asyncio.wrap_future(future)
        
        return result
    except Exception as e:
        logger.error(f"Error in debug recipes: {e}")
        return {"error": str(e), "firebase_available": FIREBASE_AVAILABLE}

def debug_recipes_from_firestore():
    """Debug function to check recipes collection"""
    if not FIREBASE_AVAILABLE:
        return {"error": "Firebase not available", "firebase_available": False}
    
    try:
        # Check if recipes collection exists
        recipes_ref = firestore_db.collection('recipes')
        docs = list(recipes_ref.stream())
        
        result = {
            "firebase_available": FIREBASE_AVAILABLE,
            "collection_exists": True,
            "total_docs": len(docs),
            "sample_docs": []
        }
        
        # Get sample documents
        for i, doc in enumerate(docs[:3]):  # First 3 documents
            doc_data = doc.to_dict()
            result["sample_docs"].append({
                "id": doc.id,
                "fields": list(doc_data.keys()),
                "has_createdAt": "createdAt" in doc_data,
                "title": doc_data.get("title", "No title"),
                "type": doc_data.get("type", "No type")
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in debug_recipes_from_firestore: {e}")
        return {"error": str(e), "firebase_available": FIREBASE_AVAILABLE}

def get_recipes_from_firestore():
    """Helper function to get recipes from Firestore"""
    if not FIREBASE_AVAILABLE:
        return []
    
    try:
        # First try without ordering to see if there are any recipes
        recipes_ref = firestore_db.collection('recipes')
        docs = recipes_ref.stream()
        recipes = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        
        logger.info(f"Found {len(recipes)} recipes in Firestore")
        
        # If we have recipes, try to sort them by createdAt if the field exists
        if recipes and any('createdAt' in recipe for recipe in recipes):
            try:
                recipes_ref = firestore_db.collection('recipes').order_by('createdAt', direction=firestore_db.Query.DESCENDING)
                docs = recipes_ref.stream()
                recipes = [{"id": doc.id, **doc.to_dict()} for doc in docs]
                logger.info(f"Successfully ordered {len(recipes)} recipes by createdAt")
            except Exception as sort_error:
                logger.warning(f"Could not order by createdAt, using unordered results: {sort_error}")
        
        return recipes
    except Exception as e:
        logger.error(f"Error in get_recipes_from_firestore: {e}")
        return []

# --- Notification Scheduler Endpoints ---
@api_router.post("/notifications/check-due")
async def check_due_notifications():
    """
    Check and send due notifications.
    This endpoint can be called by a scheduled job (cron, etc.) to send notifications.
    """
    try:
        check_firebase_availability()
        
        # Get the notification scheduler
        scheduler = get_notification_scheduler(firestore_db)
        
        # Send due notifications
        sent_count = await scheduler.send_due_notifications()
        
        return {
            "success": True,
            "sent_count": sent_count,
            "message": f"Successfully sent {sent_count} due notifications"
        }
        
    except Exception as e:
        logger.error(f"Error checking due notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check due notifications: {str(e)}")

@api_router.post("/notifications/schedule-user/{user_id}")
async def schedule_user_notifications_manual(user_id: str):
    """
    Manually trigger notification scheduling for a specific user.
    Useful for testing or manual scheduling.
    """
    try:
        check_firebase_availability()
        
        # Get the notification scheduler
        scheduler = get_notification_scheduler(firestore_db)
        
        # Schedule notifications for the user
        scheduled_count = await scheduler.schedule_user_notifications(user_id)
        
        return {
            "success": True,
            "scheduled_count": scheduled_count,
            "message": f"Successfully scheduled {scheduled_count} notifications for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule notifications: {str(e)}")

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    print("🎉 Server initialization complete!")
    print("🌐 Starting server on http://0.0.0.0:8000")
    print("⏰ Diet countdown scheduler started (checking every 6 hours)")
    print("📬 Push notification system enabled")
    uvicorn.run(app, host="0.0.0.0", port=8000)