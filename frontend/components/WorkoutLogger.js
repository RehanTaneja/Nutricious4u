import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  TouchableOpacity, 
  FlatList, 
  Alert,
  ActivityIndicator 
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function WorkoutLogger({ onAddWorkout }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [duration, setDuration] = useState('30');

  const searchWorkouts = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Please enter a workout to search');
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
      Alert.alert('Error', 'Failed to search workouts. Please try again.');
      
      // Fallback mock data for testing
      setSearchResults([
        {
          id: 1,
          name: 'Running',
          calories_per_minute: 10,
          type: 'cardio'
        },
        {
          id: 2,
          name: 'Push-ups',
          calories_per_minute: 7,
          type: 'strength'
        },
        {
          id: 3,
          name: 'Cycling',
          calories_per_minute: 8,
          type: 'cardio'
        },
        {
          id: 4,
          name: 'Yoga',
          calories_per_minute: 3,
          type: 'flexibility'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const selectWorkout = (workout) => {
    setSelectedWorkout(workout);
  };

  const addWorkoutToLog = () => {
    if (!selectedWorkout) {
      Alert.alert('Please select a workout');
      return;
    }

    const workoutEntry = {
      name: selectedWorkout.name,
      caloriesBurned: Math.round(selectedWorkout.calories_per_minute * parseFloat(duration)),
      duration: parseFloat(duration),
      type: selectedWorkout.type
    };

    onAddWorkout(workoutEntry);
    
    // Reset form
    setSelectedWorkout(null);
    setSearchQuery('');
    setSearchResults([]);
    setDuration('30');
    
    Alert.alert('Success!', `${workoutEntry.name} workout logged successfully!`);
  };

  const getWorkoutIcon = (type) => {
    switch (type) {
      case 'cardio':
        return 'heart';
      case 'strength':
        return 'barbell';
      case 'flexibility':
        return 'body';
      default:
        return 'fitness';
    }
  };

  const getWorkoutColor = (type) => {
    switch (type) {
      case 'cardio':
        return '#FF6B6B';
      case 'strength':
        return '#4ECDC4';
      case 'flexibility':
        return '#45B7D1';
      default:
        return '#98D8C8';
    }
  };

  const renderWorkoutItem = ({ item }) => (
    <TouchableOpacity 
      style={[
        styles.workoutItem,
        selectedWorkout?.id === item.id && styles.selectedWorkoutItem
      ]}
      onPress={() => selectWorkout(item)}
    >
      <View style={styles.workoutIcon}>
        <Ionicons 
          name={getWorkoutIcon(item.type)} 
          size={24} 
          color={getWorkoutColor(item.type)} 
        />
      </View>
      <View style={styles.workoutInfo}>
        <Text style={styles.workoutName}>{item.name}</Text>
        <Text style={styles.workoutDetails}>
          {item.calories_per_minute} cal/min • {item.type}
        </Text>
      </View>
      {selectedWorkout?.id === item.id && (
        <Ionicons name="checkmark-circle" size={24} color="#4ECDC4" />
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#FFFFFF', '#F8F9FA']}
        style={styles.content}
      >
        <Text style={styles.title}>Log Workout</Text>
        
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Enter workout name (e.g., running, push-ups)"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={searchWorkouts}
          />
          <TouchableOpacity style={styles.searchButton} onPress={searchWorkouts}>
            <Ionicons name="search" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#667eea" />
            <Text style={styles.loadingText}>Searching workout database...</Text>
          </View>
        )}

        {searchResults.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Search Results</Text>
            <FlatList
              data={searchResults}
              renderItem={renderWorkoutItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.resultsList}
            />
          </>
        )}

        {selectedWorkout && (
          <View style={styles.durationContainer}>
            <Text style={styles.sectionTitle}>Workout Duration</Text>
            <View style={styles.durationInput}>
              <TextInput
                style={styles.durationTextInput}
                value={duration}
                onChangeText={setDuration}
                keyboardType="numeric"
                placeholder="30"
              />
              <Text style={styles.durationUnit}>minutes</Text>
            </View>
            
            <View style={styles.caloriesPreview}>
              <Text style={styles.previewTitle}>Calories Burned:</Text>
              <Text style={styles.previewCalories}>
                {Math.round(selectedWorkout.calories_per_minute * parseFloat(duration))} kcal
              </Text>
            </View>

            <TouchableOpacity style={styles.addButton} onPress={addWorkoutToLog}>
              <LinearGradient
                colors={['#A8E6CF', '#7FCDCD']}
                style={styles.addButtonGradient}
              >
                <Ionicons name="add-circle" size={24} color="#FFFFFF" />
                <Text style={styles.addButtonText}>Log Workout</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        )}
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
    paddingTop: 50,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 30,
    textAlign: 'center',
  },
  searchContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  searchInput: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    paddingHorizontal: 20,
    paddingVertical: 15,
    fontSize: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  searchButton: {
    backgroundColor: '#667eea',
    borderRadius: 15,
    paddingHorizontal: 20,
    paddingVertical: 15,
    marginLeft: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  resultsList: {
    maxHeight: 300,
    marginBottom: 20,
  },
  workoutItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    padding: 15,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  selectedWorkoutItem: {
    borderColor: '#4ECDC4',
    borderWidth: 2,
  },
  workoutIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  workoutInfo: {
    flex: 1,
  },
  workoutName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  workoutDetails: {
    fontSize: 14,
    color: '#666',
  },
  durationContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    padding: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  durationInput: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  durationTextInput: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    width: 100,
    textAlign: 'center',
  },
  durationUnit: {
    fontSize: 16,
    color: '#666',
    marginLeft: 10,
  },
  caloriesPreview: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
    alignItems: 'center',
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  previewCalories: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF6B6B',
  },
  addButton: {
    borderRadius: 15,
  },
  addButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 15,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});
