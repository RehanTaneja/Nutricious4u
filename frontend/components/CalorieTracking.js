import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

export default function CalorieTracking({ todayData, userProfile }) {
  const calorieProgress = Math.min((todayData.calories / userProfile.dailyCalorieGoal) * 100, 100);
  const proteinProgress = Math.min((todayData.protein / userProfile.dailyProteinGoal) * 100, 100);
  const fatProgress = Math.min((todayData.fat / userProfile.dailyFatGoal) * 100, 100);

  const ProgressCircle = ({ progress, color, label, current, goal, unit, icon }) => (
    <View style={styles.progressContainer}>
      <View style={styles.circleContainer}>
        <View style={[styles.circle, { borderColor: color }]}>
          <View style={[styles.progressFill, { 
            width: `${progress}%`, 
            backgroundColor: color 
          }]} />
        </View>
        <View style={styles.iconContainer}>
          <Ionicons name={icon} size={24} color={color} />
        </View>
      </View>
      <Text style={styles.progressLabel}>{label}</Text>
      <Text style={styles.progressValue}>
        {Math.round(current)}/{goal} {unit}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#FFFFFF', '#F8F9FA']}
        style={styles.card}
      >
        <Text style={styles.cardTitle}>Today's Progress</Text>
        
        <View style={styles.progressGrid}>
          <ProgressCircle
            progress={calorieProgress}
            color="#FF6B6B"
            label="Calories"
            current={todayData.calories}
            goal={userProfile.dailyCalorieGoal}
            unit="kcal"
            icon="flame"
          />
          
          <ProgressCircle
            progress={proteinProgress}
            color="#4ECDC4"
            label="Protein"
            current={todayData.protein}
            goal={userProfile.dailyProteinGoal}
            unit="g"
            icon="fitness"
          />
          
          <ProgressCircle
            progress={fatProgress}
            color="#45B7D1"
            label="Fat"
            current={todayData.fat}
            goal={userProfile.dailyFatGoal}
            unit="g"
            icon="water"
          />
        </View>
        
        <View style={styles.stepCounter}>
          <Ionicons name="walk" size={24} color="#98D8C8" />
          <Text style={styles.stepText}>
            {todayData.steps.toLocaleString()} steps today
          </Text>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  card: {
    padding: 20,
    borderRadius: 20,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  progressGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  progressContainer: {
    alignItems: 'center',
    flex: 1,
  },
  circleContainer: {
    position: 'relative',
    width: 80,
    height: 80,
    marginBottom: 10,
  },
  circle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    backgroundColor: '#F0F0F0',
    overflow: 'hidden',
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    position: 'absolute',
    bottom: 0,
    left: 0,
    borderRadius: 40,
  },
  iconContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  progressValue: {
    fontSize: 12,
    color: '#666',
  },
  stepCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8F9FA',
    padding: 15,
    borderRadius: 15,
  },
  stepText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 10,
  },
});
