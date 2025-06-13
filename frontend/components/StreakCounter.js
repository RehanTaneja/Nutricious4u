import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export default function StreakCounter({ streak }) {
  const getStreakMessage = () => {
    if (streak === 0) return "Start your journey today!";
    if (streak === 1) return "Great start! Keep it up!";
    if (streak < 7) return "Building momentum!";
    if (streak < 30) return "You're on fire! 🔥";
    if (streak < 100) return "Incredible dedication!";
    return "Legendary streak! 🏆";
  };

  const getStreakEmoji = () => {
    if (streak === 0) return "🌱";
    if (streak < 7) return "🔥";
    if (streak < 30) return "💪";
    if (streak < 100) return "🚀";
    return "👑";
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#FF6B6B', '#FF8E8E']}
        style={styles.card}
      >
        <View style={styles.streakContainer}>
          <View style={styles.flameContainer}>
            <Ionicons name="flame" size={40} color="#FFFFFF" />
            <Text style={styles.streakNumber}>{streak}</Text>
          </View>
          
          <View style={styles.textContainer}>
            <Text style={styles.streakTitle}>Day Streak</Text>
            <Text style={styles.streakMessage}>
              {getStreakMessage()} {getStreakEmoji()}
            </Text>
          </View>
        </View>
        
        <View style={styles.motivationContainer}>
          <Text style={styles.motivationText}>
            {streak > 0 
              ? `You've been consistent for ${streak} ${streak === 1 ? 'day' : 'days'}!`
              : "Log your first meal or workout to start your streak!"
            }
          </Text>
        </View>
        
        <View style={styles.progressIndicator}>
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill, 
                { width: `${Math.min((streak % 7) / 7 * 100, 100)}%` }
              ]} 
            />
          </View>
          <Text style={styles.progressText}>
            {streak % 7}/7 days to next milestone
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
    padding: 25,
    borderRadius: 20,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
  },
  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  flameContainer: {
    position: 'relative',
    marginRight: 20,
  },
  streakNumber: {
    position: 'absolute',
    top: 8,
    left: 0,
    right: 0,
    textAlign: 'center',
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  textContainer: {
    flex: 1,
  },
  streakTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 5,
  },
  streakMessage: {
    fontSize: 16,
    color: '#FFFFFF',
    opacity: 0.9,
  },
  motivationContainer: {
    marginBottom: 20,
  },
  motivationText: {
    fontSize: 14,
    color: '#FFFFFF',
    opacity: 0.8,
    textAlign: 'center',
    lineHeight: 20,
  },
  progressIndicator: {
    alignItems: 'center',
  },
  progressBar: {
    width: '100%',
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 3,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.8,
  },
});
