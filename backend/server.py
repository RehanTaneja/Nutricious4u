from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import httpx
import asyncio


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class FoodItem(BaseModel):
    id: int
    name: str
    calories: float
    protein: float
    fat: float
    per_100g: bool = True

class FoodSearchResponse(BaseModel):
    foods: List[FoodItem]

class WorkoutItem(BaseModel):
    id: int
    name: str
    calories_per_minute: float
    type: str

class WorkoutSearchResponse(BaseModel):
    exercises: List[WorkoutItem]

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.get("/food/search", response_model=FoodSearchResponse)
async def search_food(query: str = Query(..., min_length=1)):
    """Search for food items using USDA FoodData Central API"""
    try:
        # For now, using mock data - will be replaced with actual USDA API
        mock_foods = [
            FoodItem(id=1, name="Apple", calories=52, protein=0.3, fat=0.2),
            FoodItem(id=2, name="Banana", calories=89, protein=1.1, fat=0.3),
            FoodItem(id=3, name="Chicken Breast", calories=165, protein=31, fat=3.6),
            FoodItem(id=4, name="Brown Rice", calories=123, protein=2.6, fat=0.9),
            FoodItem(id=5, name="Salmon", calories=208, protein=20, fat=12),
            FoodItem(id=6, name="Broccoli", calories=34, protein=2.8, fat=0.4),
            FoodItem(id=7, name="Greek Yogurt", calories=59, protein=10, fat=0.4),
            FoodItem(id=8, name="Almonds", calories=579, protein=21, fat=50),
            FoodItem(id=9, name="Sweet Potato", calories=86, protein=1.6, fat=0.1),
            FoodItem(id=10, name="Eggs", calories=155, protein=13, fat=11),
        ]
        
        # Filter foods based on search query
        filtered_foods = [
            food for food in mock_foods 
            if query.lower() in food.name.lower()
        ]
        
        return FoodSearchResponse(foods=filtered_foods)
        
    except Exception as e:
        logger.error(f"Error searching food: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search food")

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
        logger.error(f"Error searching workouts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search workouts")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
