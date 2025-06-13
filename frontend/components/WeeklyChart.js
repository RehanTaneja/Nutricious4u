import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

export default function WeeklyChart({ data }) {
  // Mock data for the last 7 days
  const mockData = [
    { day: 'Mon', calories: 1800 },
    { day: 'Tue', calories: 2100 },
    { day: 'Wed', calories: 1950 },
    { day: 'Thu', calories: 2200 },
    { day: 'Fri', calories: 1750 },
    { day: 'Sat', calories: 2400 },
    { day: 'Sun', calories: 2000 },
  ];

  const chartData = data.length > 0 ? data : mockData;
  const maxCalories = Math.max(...chartData.map(d => d.calories));
  const targetCalories = 2000;

  const renderBar = (item, index) => {
    const height = (item.calories / maxCalories) * 120;
    const isToday = index === chartData.length - 1;
    
    return (
      <View key={index} style={styles.barContainer}>
        <View style={styles.barWrapper}>
          <LinearGradient
            colors={isToday ? ['#FF6B6B', '#FF8E8E'] : ['#4ECDC4', '#44A08D']}
            style={[styles.bar, { height }]}
          />
          <View style={styles.targetLine} />
        </View>
        <Text style={styles.dayLabel}>{item.day}</Text>
        <Text style={styles.calorieLabel}>{item.calories}</Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#FFFFFF', '#F8F9FA']}
        style={styles.card}
      >
        <Text style={styles.cardTitle}>7-Day Calorie History</Text>
        
        <View style={styles.chartContainer}>
          <View style={styles.yAxis}>
            <Text style={styles.yAxisLabel}>{maxCalories}</Text>
            <Text style={styles.yAxisLabel}>{Math.round(maxCalories * 0.75)}</Text>
            <Text style={styles.yAxisLabel}>{Math.round(maxCalories * 0.5)}</Text>
            <Text style={styles.yAxisLabel}>{Math.round(maxCalories * 0.25)}</Text>
            <Text style={styles.yAxisLabel}>0</Text>
          </View>
          
          <View style={styles.chart}>
            <View style={styles.barsContainer}>
              {chartData.map((item, index) => renderBar(item, index))}
            </View>
          </View>
        </View>
        
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#4ECDC4' }]} />
            <Text style={styles.legendText}>Past days</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendColor, { backgroundColor: '#FF6B6B' }]} />
            <Text style={styles.legendText}>Today</Text>
          </View>
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
  chartContainer: {
    flexDirection: 'row',
    height: 160,
    marginBottom: 20,
  },
  yAxis: {
    width: 40,
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    paddingRight: 10,
  },
  yAxisLabel: {
    fontSize: 12,
    color: '#666',
  },
  chart: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  barsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-end',
    height: 120,
  },
  barContainer: {
    alignItems: 'center',
    flex: 1,
  },
  barWrapper: {
    position: 'relative',
    height: 120,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  bar: {
    width: 20,
    borderRadius: 10,
    minHeight: 5,
  },
  targetLine: {
    position: 'absolute',
    top: 20,
    left: -10,
    right: -10,
    height: 1,
    backgroundColor: '#999',
    opacity: 0.5,
  },
  dayLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  calorieLabel: {
    fontSize: 10,
    color: '#666',
    marginTop: 2,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 5,
  },
  legendText: {
    fontSize: 12,
    color: '#666',
  },
});
