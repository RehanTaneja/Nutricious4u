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

export default function FoodSearch({ onAddFood }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFood, setSelectedFood] = useState(null);
  const [portion, setPortion] = useState('100');

  const searchFood = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Please enter a food item to search');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/food/search`, {
        params: { query: searchQuery }
      });
      
      setSearchResults(response.data.foods || []);
    } catch (error) {
      console.error('Error searching food:', error);
      Alert.alert('Error', 'Failed to search food. Please try again.');
      
      // Fallback mock data for testing
      setSearchResults([
        {
          id: 1,
          name: 'Apple',
          calories: 52,
          protein: 0.3,
          fat: 0.2,
          per_100g: true
        },
        {
          id: 2,
          name: 'Banana',
          calories: 89,
          protein: 1.1,
          fat: 0.3,
          per_100g: true
        },
        {
          id: 3,
          name: 'Chicken Breast',
          calories: 165,
          protein: 31,
          fat: 3.6,
          per_100g: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const selectFood = (food) => {
    setSelectedFood(food);
  };

  const addFoodToLog = () => {
    if (!selectedFood) {
      Alert.alert('Please select a food item');
      return;
    }

    const portionMultiplier = parseFloat(portion) / 100;
    const foodEntry = {
      name: `${selectedFood.name} (${portion}g)`,
      calories: Math.round(selectedFood.calories * portionMultiplier),
      protein: Math.round(selectedFood.protein * portionMultiplier * 10) / 10,
      fat: Math.round(selectedFood.fat * portionMultiplier * 10) / 10,
    };

    onAddFood(foodEntry);
    
    // Reset form
    setSelectedFood(null);
    setSearchQuery('');
    setSearchResults([]);
    setPortion('100');
    
    Alert.alert('Success!', `${foodEntry.name} added to your food log`);
  };

  const renderFoodItem = ({ item }) => (
    <TouchableOpacity 
      style={[
        styles.foodItem,
        selectedFood?.id === item.id && styles.selectedFoodItem
      ]}
      onPress={() => selectFood(item)}
    >
      <View style={styles.foodInfo}>
        <Text style={styles.foodName}>{item.name}</Text>
        <Text style={styles.foodNutrition}>
          {item.calories} kcal | {item.protein}g protein | {item.fat}g fat
        </Text>
      </View>
      {selectedFood?.id === item.id && (
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
        <Text style={styles.title}>Search Food</Text>
        
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Enter food name (e.g., apple, chicken breast)"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={searchFood}
          />
          <TouchableOpacity style={styles.searchButton} onPress={searchFood}>
            <Ionicons name="search" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#667eea" />
            <Text style={styles.loadingText}>Searching food database...</Text>
          </View>
        )}

        {searchResults.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Search Results</Text>
            <FlatList
              data={searchResults}
              renderItem={renderFoodItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.resultsList}
            />
          </>
        )}

        {selectedFood && (
          <View style={styles.portionContainer}>
            <Text style={styles.sectionTitle}>Select Portion</Text>
            <View style={styles.portionInput}>
              <TextInput
                style={styles.portionTextInput}
                value={portion}
                onChangeText={setPortion}
                keyboardType="numeric"
                placeholder="100"
              />
              <Text style={styles.portionUnit}>grams</Text>
            </View>
            
            <View style={styles.nutritionPreview}>
              <Text style={styles.previewTitle}>Nutrition Preview:</Text>
              <Text style={styles.previewText}>
                Calories: {Math.round(selectedFood.calories * parseFloat(portion) / 100)} kcal
              </Text>
              <Text style={styles.previewText}>
                Protein: {Math.round(selectedFood.protein * parseFloat(portion) / 100 * 10) / 10}g
              </Text>
              <Text style={styles.previewText}>
                Fat: {Math.round(selectedFood.fat * parseFloat(portion) / 100 * 10) / 10}g
              </Text>
            </View>

            <TouchableOpacity style={styles.addButton} onPress={addFoodToLog}>
              <LinearGradient
                colors={['#4ECDC4', '#44A08D']}
                style={styles.addButtonGradient}
              >
                <Ionicons name="add-circle" size={24} color="#FFFFFF" />
                <Text style={styles.addButtonText}>Add to Food Log</Text>
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
  foodItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    padding: 15,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  selectedFoodItem: {
    borderColor: '#4ECDC4',
    borderWidth: 2,
  },
  foodInfo: {
    flex: 1,
  },
  foodName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  foodNutrition: {
    fontSize: 14,
    color: '#666',
  },
  portionContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 15,
    padding: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  portionInput: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  portionTextInput: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    width: 100,
    textAlign: 'center',
  },
  portionUnit: {
    fontSize: 16,
    color: '#666',
    marginLeft: 10,
  },
  nutritionPreview: {
    backgroundColor: '#F8F9FA',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  previewText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
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
