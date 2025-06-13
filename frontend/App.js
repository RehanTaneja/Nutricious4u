import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Dimensions, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

// Import custom components
import DashboardHeader from './components/DashboardHeader';
import CalorieTracking from './components/CalorieTracking';
import FoodSearch from './components/FoodSearch';
import WorkoutLogger from './components/WorkoutLogger';
import WeeklyChart from './components/WeeklyChart';
import StreakCounter from './components/StreakCounter';
import ConfettiAnimation from './components/ConfettiAnimation';

const { width, height } = Dimensions.get('window');

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showConfetti, setShowConfetti] = useState(false);
  const [userProfile, setUserProfile] = useState({
    name: 'User',
    dailyCalorieGoal: 2000,
    dailyProteinGoal: 120,
    dailyFatGoal: 65
  });
  
  const [todayData, setTodayData] = useState({
    calories: 0,
    protein: 0,
    fat: 0,
    steps: 0,
    foodEntries: [],
    workoutEntries: []
  });

  const [streak, setStreak] = useState(0);
  const [weeklyData, setWeeklyData] = useState([]);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userProfile');
      const todayKey = new Date().toDateString();
      const todayStoredData = await AsyncStorage.getItem(`day_${todayKey}`);
      const streakData = await AsyncStorage.getItem('streak');
      const weeklyStoredData = await AsyncStorage.getItem('weeklyData');

      if (userData) {
        setUserProfile(JSON.parse(userData));
      }
      
      if (todayStoredData) {
        setTodayData(JSON.parse(todayStoredData));
      }
      
      if (streakData) {
        setStreak(parseInt(streakData));
      }
      
      if (weeklyStoredData) {
        setWeeklyData(JSON.parse(weeklyStoredData));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const saveUserData = async (data, key) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving data:', error);
    }
  };

  const addFoodEntry = (foodItem) => {
    const newEntry = {
      id: Date.now(),
      name: foodItem.name,
      calories: foodItem.calories,
      protein: foodItem.protein,
      fat: foodItem.fat,
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
    saveUserData(updatedData, `day_${new Date().toDateString()}`);
    
    // Show confetti if goal is reached
    if (updatedData.calories >= userProfile.dailyCalorieGoal * 0.8) {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 3000);
    }
  };

  const addWorkoutEntry = (workout) => {
    const newEntry = {
      id: Date.now(),
      name: workout.name,
      caloriesBurned: workout.caloriesBurned,
      duration: workout.duration,
      timestamp: new Date().toISOString()
    };

    const updatedData = {
      ...todayData,
      calories: todayData.calories - workout.caloriesBurned, // Subtract burned calories
      workoutEntries: [...todayData.workoutEntries, newEntry]
    };

    setTodayData(updatedData);
    saveUserData(updatedData, `day_${new Date().toDateString()}`);
  };

  const openCamera = async () => {
    try {
      const permissionResult = await ImagePicker.requestCameraPermissionsAsync();
      
      if (permissionResult.granted === false) {
        Alert.alert('Permission required', 'Camera permission is required to take photos of food');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled) {
        Alert.alert(
          'Photo Captured!', 
          'AI food recognition will be available in the next update. For now, please use manual food search.',
          [{ text: 'OK', onPress: () => setActiveTab('food') }]
        );
      }
    } catch (error) {
      console.error('Error opening camera:', error);
      Alert.alert('Error', 'Failed to open camera');
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            <DashboardHeader 
              userProfile={userProfile}
              todayData={todayData}
              streak={streak}
            />
            
            <CalorieTracking 
              todayData={todayData}
              userProfile={userProfile}
            />
            
            <View style={styles.quickActions}>
              <TouchableOpacity 
                style={styles.cameraButton}
                onPress={openCamera}
              >
                <LinearGradient
                  colors={['#FF6B6B', '#FF8E8E']}
                  style={styles.cameraGradient}
                >
                  <Ionicons name="camera" size={32} color="#FFF" />
                  <Text style={styles.cameraText}>Snap Food</Text>
                </LinearGradient>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.quickActionButton}
                onPress={() => setActiveTab('food')}
              >
                <LinearGradient
                  colors={['#4ECDC4', '#44A08D']}
                  style={styles.quickActionGradient}
                >
                  <Ionicons name="search" size={24} color="#FFF" />
                  <Text style={styles.quickActionText}>Search Food</Text>
                </LinearGradient>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.quickActionButton}
                onPress={() => setActiveTab('workout')}
              >
                <LinearGradient
                  colors={['#A8E6CF', '#7FCDCD']}
                  style={styles.quickActionGradient}
                >
                  <Ionicons name="fitness" size={24} color="#FFF" />
                  <Text style={styles.quickActionText}>Log Workout</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
            
            <WeeklyChart data={weeklyData} />
            
            <StreakCounter streak={streak} />
          </ScrollView>
        );
      
      case 'food':
        return (
          <FoodSearch onAddFood={addFoodEntry} />
        );
      
      case 'workout':
        return (
          <WorkoutLogger onAddWorkout={addWorkoutEntry} />
        );
      
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.gradient}
      >
        {renderContent()}
        
        {/* Bottom Navigation */}
        <View style={styles.bottomNav}>
          <TouchableOpacity 
            style={[styles.navItem, activeTab === 'dashboard' && styles.activeNavItem]}
            onPress={() => setActiveTab('dashboard')}
          >
            <Ionicons 
              name="home" 
              size={24} 
              color={activeTab === 'dashboard' ? '#667eea' : '#8E8E93'} 
            />
            <Text style={[styles.navText, activeTab === 'dashboard' && styles.activeNavText]}>
              Dashboard
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.navItem, activeTab === 'food' && styles.activeNavItem]}
            onPress={() => setActiveTab('food')}
          >
            <Ionicons 
              name="restaurant" 
              size={24} 
              color={activeTab === 'food' ? '#667eea' : '#8E8E93'} 
            />
            <Text style={[styles.navText, activeTab === 'food' && styles.activeNavText]}>
              Food
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.navItem, activeTab === 'workout' && styles.activeNavItem]}
            onPress={() => setActiveTab('workout')}
          >
            <Ionicons 
              name="barbell" 
              size={24} 
              color={activeTab === 'workout' ? '#667eea' : '#8E8E93'} 
            />
            <Text style={[styles.navText, activeTab === 'workout' && styles.activeNavText]}>
              Workout
            </Text>
          </TouchableOpacity>
        </View>
        
        {showConfetti && <ConfettiAnimation />}
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingTop: 50,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginHorizontal: 20,
    marginVertical: 20,
  },
  cameraButton: {
    flex: 1,
    marginHorizontal: 5,
  },
  cameraGradient: {
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  cameraText: {
    color: '#FFF',
    fontWeight: 'bold',
    marginTop: 5,
  },
  quickActionButton: {
    flex: 1,
    marginHorizontal: 5,
  },
  quickActionGradient: {
    padding: 15,
    borderRadius: 15,
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  quickActionText: {
    color: '#FFF',
    fontWeight: 'bold',
    marginTop: 5,
    fontSize: 12,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
  },
  activeNavItem: {
    backgroundColor: '#F0F0F0',
    borderRadius: 10,
  },
  navText: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 5,
  },
  activeNavText: {
    color: '#667eea',
    fontWeight: 'bold',
  },
});
