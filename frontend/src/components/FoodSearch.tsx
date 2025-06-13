import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, Check } from 'lucide-react';
import axios from 'axios';

interface FoodItem {
  id: number;
  name: string;
  calories: number;
  protein: number;
  fat: number;
  per_100g: boolean;
}

interface FoodSearchProps {
  onAddFood: (food: { name: string; calories: number; protein: number; fat: number }) => void;
}

const FoodSearch: React.FC<FoodSearchProps> = ({ onAddFood }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FoodItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null);
  const [portion, setPortion] = useState('100');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const searchFood = async () => {
    if (!searchQuery.trim()) {
      alert('Please enter a food item to search');
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
      alert('Failed to search food. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectFood = (food: FoodItem) => {
    setSelectedFood(food);
  };

  const addFoodToLog = () => {
    if (!selectedFood) {
      alert('Please select a food item');
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
    
    alert(`${foodEntry.name} added to your food log! 🎉`);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchFood();
    }
  };

  return (
    <div className="food-search">
      <motion.h1 
        className="search-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Search Food
      </motion.h1>
      
      <motion.div 
        className="search-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <input
          className="search-input"
          placeholder="Enter food name (e.g., apple, chicken breast)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <motion.button 
          className="search-button" 
          onClick={searchFood}
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
          <div>🔍 Searching food database...</div>
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
          {searchResults.map((food, index) => (
            <motion.div
              key={food.id}
              className={`food-item ${selectedFood?.id === food.id ? 'selected' : ''}`}
              onClick={() => selectFood(food)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="food-info">
                <h4>{food.name}</h4>
                <div className="food-nutrition">
                  {food.calories} kcal | {food.protein}g protein | {food.fat}g fat
                </div>
              </div>
              {selectedFood?.id === food.id && (
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

      {selectedFood && (
        <motion.div 
          className="portion-container"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="section-title">Select Portion</h2>
          <div className="portion-input">
            <input
              className="portion-field"
              value={portion}
              onChange={(e) => setPortion(e.target.value)}
              type="number"
              placeholder="100"
            />
            <span>grams</span>
          </div>
          
          <div className="nutrition-preview">
            <div className="preview-title">Nutrition Preview:</div>
            <div className="preview-item">
              <span>Calories:</span>
              <span>{Math.round(selectedFood.calories * parseFloat(portion) / 100)} kcal</span>
            </div>
            <div className="preview-item">
              <span>Protein:</span>
              <span>{Math.round(selectedFood.protein * parseFloat(portion) / 100 * 10) / 10}g</span>
            </div>
            <div className="preview-item">
              <span>Fat:</span>
              <span>{Math.round(selectedFood.fat * parseFloat(portion) / 100 * 10) / 10}g</span>
            </div>
          </div>

          <motion.button 
            className="add-button" 
            onClick={addFoodToLog}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Plus size={20} />
            Add to Food Log
          </motion.button>
        </motion.div>
      )}
    </div>
  );
};

export default FoodSearch;
