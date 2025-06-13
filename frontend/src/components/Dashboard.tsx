import React from 'react';
import { motion } from 'framer-motion';
import { Camera, Search, Dumbbell, Flame, Activity, Target, Footprints } from 'lucide-react';

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
  foodEntries: any[];
  workoutEntries: any[];
}

interface DashboardProps {
  userProfile: UserProfile;
  todayData: TodayData;
  streak: number;
  onCameraClick: () => void;
  onFoodSearchClick: () => void;
  onWorkoutClick: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  userProfile,
  todayData,
  streak,
  onCameraClick,
  onFoodSearchClick,
  onWorkoutClick
}) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  const calorieProgress = Math.min((todayData.calories / userProfile.dailyCalorieGoal) * 100, 100);
  const proteinProgress = Math.min((todayData.protein / userProfile.dailyProteinGoal) * 100, 100);
  const fatProgress = Math.min((todayData.fat / userProfile.dailyFatGoal) * 100, 100);

  // Mock weekly data
  const weeklyData = [
    { day: 'Mon', calories: 1800 },
    { day: 'Tue', calories: 2100 },
    { day: 'Wed', calories: 1950 },
    { day: 'Thu', calories: 2200 },
    { day: 'Fri', calories: 1750 },
    { day: 'Sat', calories: 2400 },
    { day: 'Sun', calories: todayData.calories },
  ];

  const maxCalories = Math.max(...weeklyData.map(d => d.calories), 2500);

  return (
    <div className="dashboard">
      {/* Header */}
      <motion.div 
        className="dashboard-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="greeting">
          <h1>{getGreeting()}</h1>
          <h2>{userProfile.name}! 👋</h2>
        </div>
        
        <motion.div 
          className="streak-badge"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Flame className="flame" size={20} />
          <span className="streak-number">{streak}</span>
        </motion.div>
      </motion.div>

      {/* Calorie Tracking Card */}
      <motion.div 
        className="calorie-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <h3>Today's Progress</h3>
        
        <div className="progress-grid">
          <div className="progress-item">
            <div className="progress-circle">
              <div 
                className="progress-fill calories" 
                style={{ height: `${calorieProgress}%` }}
              />
              <Flame className="progress-icon" size={20} />
            </div>
            <div className="progress-label">Calories</div>
            <div className="progress-value">
              {Math.round(todayData.calories)}/{userProfile.dailyCalorieGoal} kcal
            </div>
          </div>
          
          <div className="progress-item">
            <div className="progress-circle">
              <div 
                className="progress-fill protein" 
                style={{ height: `${proteinProgress}%` }}
              />
              <Activity className="progress-icon" size={20} />
            </div>
            <div className="progress-label">Protein</div>
            <div className="progress-value">
              {Math.round(todayData.protein)}/{userProfile.dailyProteinGoal}g
            </div>
          </div>
          
          <div className="progress-item">
            <div className="progress-circle">
              <div 
                className="progress-fill fat" 
                style={{ height: `${fatProgress}%` }}
              />
              <Target className="progress-icon" size={20} />
            </div>
            <div className="progress-label">Fat</div>
            <div className="progress-value">
              {Math.round(todayData.fat)}/{userProfile.dailyFatGoal}g
            </div>
          </div>
        </div>
        
        <div className="steps-tracker">
          <Footprints size={24} color="#667eea" />
          <span className="steps-number">{todayData.steps.toLocaleString()}</span>
          <span>steps today</span>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div 
        className="quick-actions"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <motion.button 
          className="camera-button"
          onClick={onCameraClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Camera size={32} />
          <div>Snap Food</div>
        </motion.button>
        
        <motion.button 
          className="quick-action-btn"
          onClick={onFoodSearchClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Search size={20} />
          <div>Search Food</div>
        </motion.button>
        
        <motion.button 
          className="quick-action-btn workout"
          onClick={onWorkoutClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Dumbbell size={20} />
          <div>Log Workout</div>
        </motion.button>
      </motion.div>

      {/* Weekly Chart */}
      <motion.div 
        className="weekly-chart"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <h3 className="chart-title">7-Day Calorie History</h3>
        
        <div className="chart-container">
          {weeklyData.map((day, index) => (
            <motion.div 
              key={day.day}
              className="chart-bar-container"
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
            >
              <motion.div
                className={`chart-bar ${index === weeklyData.length - 1 ? 'today' : ''}`}
                style={{ height: `${(day.calories / maxCalories) * 100}px` }}
                whileHover={{ scale: 1.1 }}
              />
              <div className="chart-day">{day.day}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Streak Counter */}
      <motion.div 
        className="streak-counter"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <div className="streak-content">
          <div className="streak-flame">
            <Flame size={40} />
            <span className="streak-count">{streak}</span>
          </div>
          <div className="streak-text">
            <h3>Day Streak</h3>
            <p>{streak > 0 ? `You're on fire! 🔥` : 'Start your journey today! 🌱'}</p>
          </div>
        </div>
        
        <div className="motivation-text">
          {streak > 0 
            ? `You've been consistent for ${streak} ${streak === 1 ? 'day' : 'days'}!`
            : "Log your first meal or workout to start your streak!"
          }
        </div>
        
        <div className="progress-bar">
          <motion.div 
            className="progress-bar-fill"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min((streak % 7) / 7 * 100, 100)}%` }}
            transition={{ duration: 1, delay: 0.5 }}
          />
        </div>
        <div className="progress-text">
          {streak % 7}/7 days to next milestone
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;
