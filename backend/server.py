from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Form, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import asyncio
import json
from services.health_platform import HealthPlatformFactory
from services.firebase_client import db as firestore_db, bucket
# Add import for diet PDF upload
from services.firebase_client import upload_diet_pdf, list_non_dietician_users, get_user_notification_token, send_push_notification, check_users_with_one_day_remaining
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
import requests
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure
from google.generativeai.types import ContentDict
import tempfile

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

class ChatMessageRequest(BaseModel):
    userId: str
    chat_history: list
    user_profile: dict
    user_message: str

class ChatMessageResponse(BaseModel):
    bot_message: str

# Define app before any usage
app = FastAPI(title="Fitness Tracker API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define api_router before any usage
api_router = APIRouter(prefix='/api')

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
load_dotenv(env_path)

# USDA API Key only
USDA_API_KEY = os.environ.get('USDA_API_KEY')

# Vertex AI Gemini setup
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)

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

@api_router.get("/food/search", response_model=FoodSearchResponse)
async def usda_food_search(query: str = Query(..., min_length=1)):
    """Search for foods using the USDA FoodData Central API."""
    api_key = USDA_API_KEY
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": api_key,
        "query": query,
        "pageSize": 10
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    foods = []
    for item in data.get("foods", []):
        nutrients = {n["nutrientName"].lower(): n["value"] for n in item.get("foodNutrients", [])}
        food_item = FoodItem(
            name=item["description"].title(),
            calories=nutrients.get("energy", 0),
            protein=nutrients.get("protein", 0),
            fat=nutrients.get("total lipid (fat)", 0),
            per_100g=True
        )
        foods.append(food_item)
    return FoodSearchResponse(foods=foods)

@api_router.post("/food/log", response_model=FoodLog)
async def log_food_item(request: FoodLogRequest):
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"[FOOD LOG] Incoming request: {request}")
        user_id = request.userId
        if not user_id:
            logger.error("[FOOD LOG] userId missing in request")
            raise HTTPException(status_code=400, detail="userId is required")
        # Use Gemini to get nutrition
        nutrition = await get_nutrition_from_gemini(request.foodName, request.servingSize)
        logger.info(f"[FOOD LOG] Gemini nutrition response: {nutrition}")
        food = FoodItem(
            name=request.foodName,
            calories=float(nutrition["calories"]) if nutrition["calories"] != "Error" else 0,
            protein=float(nutrition["protein"]) if nutrition["protein"] != "Error" else 0,
            fat=float(nutrition["fat"]) if nutrition["fat"] != "Error" else 0,
            per_100g=True
        )
        log_entry = FoodLog(
            userId=user_id,
            food=food,
            servingSize=request.servingSize
        )
        def log_food_in_db():
            log_entry.timestamp = datetime.utcnow()
            firestore_db.collection(f"users/{user_id}/food_logs").add(log_entry.dict())
            logger.info(f"[FOOD LOG] Written to Firestore: {log_entry.dict()}")
            # Delete food logs older than 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
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
    loop = asyncio.get_event_loop()
    try:
        logger.info(f"[SUMMARY] Fetching summary for user: {user_id}")
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=6)
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
                serving_size_num = float(serving_size)
            except Exception:
                serving_size_num = 100
            calories = food_item.get("calories", 0)
            protein = food_item.get("protein", 0)
            fat = food_item.get("fat", 0)
            history[log_date]["calories"] += (calories * serving_size_num) / 100
            history[log_date]["protein"] += (protein * serving_size_num) / 100
            history[log_date]["fat"] += (fat * serving_size_num) / 100
        logger.info(f"[SUMMARY DEBUG] All logs fetched for user {user_id}: {all_logs}")
        today_str = today.strftime('%Y-%m-%d')
        if today_str not in history:
            history[today_str] = {"calories": 0, "protein": 0, "fat": 0}
        sorted_dates = sorted(history.keys(), reverse=True)
        formatted_history = [{"day": date, **history[date]} for date in sorted_dates]
        logger.info(f"[SUMMARY] Returning summary for user {user_id}: {formatted_history}")
        return LogSummaryResponse(history=formatted_history)
    except Exception as e:
        logger.error(f"[SUMMARY] Error getting food log summary for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve summary.")

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
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
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

        await loop.run_in_executor(executor, lambda: doc_ref.set(profile_dict))
        logger.info(f"Created profile for user {user_id}")
        return profile_dict
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user profile.")

@api_router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get a user's profile."""
    loop = asyncio.get_event_loop()
    try:
        doc_ref = firestore_db.collection("user_profiles").document(user_id)
        doc = await loop.run_in_executor(executor, doc_ref.get)
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")
        profile = doc.to_dict()
        # Filter out placeholder profiles
        is_placeholder = (
            profile.get("firstName", "User") == "User" and
            profile.get("lastName", "") == "" and
            (not profile.get("email") or profile.get("email", "").endswith("@example.com"))
        )
        if is_placeholder:
            logger.warning(f"Filtered out placeholder profile for user {user_id}: {profile}")
            raise HTTPException(status_code=404, detail="User profile not found (placeholder)")
        return profile
    except Exception as e:
        # Re-raise HTTPException so FastAPI can handle it, otherwise convert to 500
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@api_router.patch("/users/{user_id}/profile", response_model=UserProfile)
async def update_user_profile(user_id: str, profile_update: UpdateUserProfile):
    """Update a user's profile. If not found, create it with defaults."""
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
        # Fill any missing required fields with defaults
        for k, v in defaults.items():
            if profile.get(k) is None:
                profile[k] = v
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
            "date": date or datetime.utcnow().isoformat(),
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
        model = GenerativeModel('models/gemini-2.5-flash')
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
    try:
        print(f"Starting diet upload for user {user_id} by dietician {dietician_id}")
        print(f"File: {file.filename}, Size: {file.size} bytes")
        
        # Read file data
        file_data = await file.read()
        print(f"Read {len(file_data)} bytes from file")
        
        # Upload to Firebase Storage
        print(f"Calling upload_diet_pdf with user_id={user_id}, filename={file.filename}")
        pdf_url = upload_diet_pdf(user_id, file_data, file.filename)
        print(f"Upload completed. PDF URL: {pdf_url}")
        
        # Store the filename in Firestore instead of the signed URL (which expires)
        # The signed URL will be generated when needed by the PDF serving endpoint
        diet_info = {
            "dietPdfUrl": file.filename,  # Store filename, not signed URL
            "lastDietUpload": datetime.now().isoformat(),
            "dieticianId": dietician_id
        }
        
        print(f"Updating Firestore with diet info: {diet_info}")
        try:
            # Use executor for Firestore operations
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                # Update the document
                await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id).update(diet_info))
                print(f"Successfully updated Firestore for user {user_id}")
                
                # Verify the update
                updated_doc = await loop.run_in_executor(executor, lambda: firestore_db.collection("user_profiles").document(user_id).get())
                if updated_doc.exists:
                    updated_data = updated_doc.to_dict()
                    print(f"Verified Firestore update - dietPdfUrl: {updated_data.get('dietPdfUrl')}")
                else:
                    print(f"ERROR: User document {user_id} not found after update")
        except Exception as firestore_error:
            print(f"ERROR updating Firestore: {firestore_error}")
            raise firestore_error
        
        # Send push notification to user
        user_token = get_user_notification_token(user_id)
        if user_token:
            send_push_notification(
                user_token,
                "New Diet Has Arrived!",
                "Your dietician has uploaded a new diet plan for you.",
                {"type": "new_diet", "userId": user_id}
            )
            print(f"Sent new diet notification to user {user_id}")
        
        return {"success": True, "pdf_url": pdf_url, "message": "Diet uploaded successfully"}
        
    except Exception as e:
        print(f"Error uploading diet: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- Check Users with 1 Day Remaining (for scheduled jobs) ---
@api_router.post("/diet/check-reminders")
async def check_diet_reminders():
    """
    Check all users and notify dietician if any user has 1 day remaining.
    This endpoint can be called by a scheduled job (cron, etc.)
    """
    try:
        one_day_users = check_users_with_one_day_remaining()
        return {
            "success": True,
            "users_with_one_day": len(one_day_users),
            "users": one_day_users
        }
    except Exception as e:
        print(f"Error checking diet reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Get User Diet PDF and Countdown ---
@api_router.get("/users/{user_id}/diet")
async def get_user_diet(user_id: str):
    """
    Returns the user's diet PDF URL and days left until new diet (7-day countdown).
    """
    doc = firestore_db.collection("user_profiles").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found.")
    data = doc.to_dict()
    pdf_url = data.get("dietPdfUrl")
    last_upload = data.get("lastDietUpload")
    days_left = None
    if last_upload:
        try:
            # Handle timezone-aware datetime strings
            if last_upload.endswith('Z'):
                # Convert UTC timezone to naive datetime
                last_upload = last_upload.replace('Z', '+00:00')
            last_dt = datetime.fromisoformat(last_upload)
            days_left = max(0, 7 - (datetime.utcnow() - last_dt).days)
        except ValueError as e:
            print(f"Error parsing lastDietUpload date: {e}")
            days_left = None
    return {
        "dietPdfUrl": pdf_url, 
        "daysLeft": days_left, 
        "lastDietUpload": last_upload,
        "hasDiet": pdf_url is not None
    }

# --- Serve PDF from Firestore ---
@api_router.get("/users/{user_id}/diet/pdf")
async def get_user_diet_pdf(user_id: str):
    """
    Serves the PDF data from Firebase Storage for viewing.
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
                            "Cache-Control": "public, max-age=3600"
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
                        "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
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
    """
    return list_non_dietician_users()

# Include the router in the main app
app.include_router(api_router)

# Add a health check endpoint at root level
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

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
            log_entry.timestamp = datetime.utcnow()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)