import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, Check, Heart, Dumbbell, Zap } from 'lucide-react';
import axios from 'axios';

interface WorkoutItem {
  id: number;
  name: string;
  calories_per_minute: number;
  type: string;
}

interface WorkoutLoggerProps {
  onAddWorkout: (workout: { name: string; caloriesBurned: number; duration: number }) => void;
}

const WorkoutLogger: React.FC<WorkoutLoggerProps> = ({ onAddWorkout }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<WorkoutItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedWorkout, setSelectedWorkout] = useState<WorkoutItem | null>(null);
  const [duration, setDuration] = useState('30');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const searchWorkouts = async () => {
    if (!searchQuery.trim()) {
      alert('Please enter a workout to search');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/workout/search`, {
        params: { query: searchQuery }
      });
      
      setSearchResults(response.data.exercises || []);
    } catch (error) {
      console.error('Error searching workouts:', error);
      alert('Failed to search workouts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectWorkout = (workout: WorkoutItem) => {
    setSelectedWorkout(workout);
  };

  const addWorkoutToLog = () => {
    if (!selectedWorkout) {
      alert('Please select a workout');
      return;
    }

    const workoutEntry = {
      name: selectedWorkout.name,
      caloriesBurned: Math.round(selectedWorkout.calories_per_minute * parseFloat(duration)),
      duration: parseFloat(duration),
    };

    onAddWorkout(workoutEntry);
    
    // Reset form
    setSelectedWorkout(null);
    setSearchQuery('');
    setSearchResults([]);
    setDuration('30');
    
    alert(`${workoutEntry.name} workout logged successfully! 💪`);
  };

  const getWorkoutIcon = (type: string) => {
    switch (type) {
      case 'cardio':
        return <Heart size={24} />;
      case 'strength':
        return <Dumbbell size={24} />;
      case 'flexibility':
        return <Zap size={24} />;
      default:
        return <Dumbbell size={24} />;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchWorkouts();
    }
  };

  return (
    <div className="workout-logger">
      <motion.h1 
        className="search-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Log Workout
      </motion.h1>
      
      <motion.div 
        className="search-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <input
          className="search-input"
          placeholder="Enter workout name (e.g., running, push-ups)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <motion.button 
          className="search-button" 
          onClick={searchWorkouts}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Search size={20} />
        </motion.button>
      </motion.div>

      {loading && (
        <motion.div 
          className="loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div>🔍 Searching workout database...</div>
        </motion.div>
      )}

      {searchResults.length > 0 && (
        <motion.div 
          className="food-results"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="section-title">Search Results</h2>
          {searchResults.map((workout, index) => (
            <motion.div
              key={workout.id}
              className={`workout-item ${selectedWorkout?.id === workout.id ? 'selected' : ''}`}
              onClick={() => selectWorkout(workout)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className={`workout-icon ${workout.type}`}>
                {getWorkoutIcon(workout.type)}
              </div>
              <div className="food-info">
                <h4>{workout.name}</h4>
                <div className="food-nutrition">
                  {workout.calories_per_minute} cal/min • {workout.type}
                </div>
              </div>
              {selectedWorkout?.id === workout.id && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                >
                  <Check size={24} color="#4ECDC4" />
                </motion.div>
              )}
            </motion.div>
          ))}
        </motion.div>
      )}

      {selectedWorkout && (
        <motion.div 
          className="duration-container"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="section-title">Workout Duration</h2>
          <div className="duration-input">
            <input
              className="duration-field"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              type="number"
              placeholder="30"
            />
            <span>minutes</span>
          </div>
          
          <div className="calories-preview">
            <div className="preview-title">Calories Burned:</div>
            <div className="calories-number">
              {Math.round(selectedWorkout.calories_per_minute * parseFloat(duration))}
            </div>
            <div>kcal</div>
          </div>

          <motion.button 
            className="add-button" 
            onClick={addWorkoutToLog}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{ 
              background: 'linear-gradient(135deg, #A8E6CF, #7FCDCD)' 
            }}
          >
            <Plus size={20} />
            Log Workout
          </motion.button>
        </motion.div>
      )}
    </div>
  );
};

export default WorkoutLogger;
