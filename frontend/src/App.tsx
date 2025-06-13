import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Search, Dumbbell, Home, TrendingUp, Flame } from 'lucide-react';
import './App.css';
import Dashboard from './components/Dashboard';
import FoodSearch from './components/FoodSearch';
import WorkoutLogger from './components/WorkoutLogger';
import ConfettiAnimation from './components/ConfettiAnimation';

interface UserProfile {
  name: string;
  dailyCalorieGoal: number;
  dailyProteinGoal: number;
  dailyFatGoal: number;
}

interface TodayData {
  calories: number;
  protein: number;
  fat: number;
  steps: number;
  foodEntries: FoodEntry[];
  workoutEntries: WorkoutEntry[];
}

interface FoodEntry {
  id: number;
  name: string;
  calories: number;
  protein: number;
  fat: number;
  timestamp: string;
}

interface WorkoutEntry {
  id: number;
  name: string;
  caloriesBurned: number;
  duration: number;
  timestamp: string;
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showConfetti, setShowConfetti] = useState(false);
  const [userProfile] = useState<UserProfile>({
    name: 'Alex',
    dailyCalorieGoal: 2000,
    dailyProteinGoal: 120,
    dailyFatGoal: 65
  });
  
  const [todayData, setTodayData] = useState<TodayData>({
    calories: 0,
    protein: 0,
    fat: 0,
    steps: 0,
    foodEntries: [],
    workoutEntries: []
  });

  const [streak, setStreak] = useState(0);

  useEffect(() => {
    loadUserData();
    // Simulate steps counter update
    const interval = setInterval(() => {
      setTodayData(prev => ({
        ...prev,
        steps: prev.steps + Math.floor(Math.random() * 10)
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadUserData = () => {
    const stored = localStorage.getItem('calorieTrackerData');
    if (stored) {
      const data = JSON.parse(stored);
      setTodayData(data.todayData || todayData);
      setStreak(data.streak || 0);
    }
  };

  const saveUserData = (data: any) => {
    localStorage.setItem('calorieTrackerData', JSON.stringify({
      todayData: data,
      streak: streak,
      lastUpdate: new Date().toDateString()
    }));
  };

  const addFoodEntry = (foodItem: Omit<FoodEntry, 'id' | 'timestamp'>) => {
    const newEntry: FoodEntry = {
      id: Date.now(),
      ...foodItem,
      timestamp: new Date().toISOString()
    };

    const updatedData = {
      ...todayData,
      calories: todayData.calories + foodItem.calories,
      protein: todayData.protein + foodItem.protein,
      fat: todayData.fat + foodItem.fat,
      foodEntries: [...todayData.foodEntries, newEntry]
    };

    setTodayData(updatedData);
    saveUserData(updatedData);
    
    // Show confetti if goal is reached
    if (updatedData.calories >= userProfile.dailyCalorieGoal * 0.8) {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 3000);
    }
  };

  const addWorkoutEntry = (workout: Omit<WorkoutEntry, 'id' | 'timestamp'>) => {
    const newEntry: WorkoutEntry = {
      id: Date.now(),
      ...workout,
      timestamp: new Date().toISOString()
    };

    const updatedData = {
      ...todayData,
      calories: Math.max(0, todayData.calories - workout.caloriesBurned),
      workoutEntries: [...todayData.workoutEntries, newEntry]
    };

    setTodayData(updatedData);
    saveUserData(updatedData);
  };

  const openCamera = () => {
    if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(() => {
          alert('📸 Camera opened! AI food recognition coming soon. For now, please use the search feature.');
          setActiveTab('food');
        })
        .catch(() => {
          alert('📸 Camera feature will be available in the mobile app. For now, please use the search feature.');
          setActiveTab('food');
        });
    } else {
      alert('📸 Camera feature will be available in the mobile app. For now, please use the search feature.');
      setActiveTab('food');
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard 
            userProfile={userProfile}
            todayData={todayData}
            streak={streak}
            onCameraClick={openCamera}
            onFoodSearchClick={() => setActiveTab('food')}
            onWorkoutClick={() => setActiveTab('workout')}
          />
        );
      case 'food':
        return <FoodSearch onAddFood={addFoodEntry} />;
      case 'workout':
        return <WorkoutLogger onAddWorkout={addWorkoutEntry} />;
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <div className="mobile-container">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="content"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>

        {/* Bottom Navigation */}
        <nav className="bottom-nav">
          <button
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Home size={24} />
            <span>Home</span>
          </button>
          
          <button
            className={`nav-item ${activeTab === 'food' ? 'active' : ''}`}
            onClick={() => setActiveTab('food')}
          >
            <Search size={24} />
            <span>Food</span>
          </button>
          
          <button
            className={`nav-item ${activeTab === 'workout' ? 'active' : ''}`}
            onClick={() => setActiveTab('workout')}
          >
            <Dumbbell size={24} />
            <span>Workout</span>
          </button>
        </nav>

        {showConfetti && <ConfettiAnimation />}
      </div>
    </div>
  );
}

export default App;
