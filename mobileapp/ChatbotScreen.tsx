import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  TouchableOpacity,
  SafeAreaView,
  FlatList,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Send } from 'lucide-react-native';
import Markdown from 'react-native-markdown-display';
import { sendChatbotMessage } from './services/api';
import { getUserProfile, UserProfile } from './services/api';
import { auth } from './services/firebase';
import { ActivityIndicator } from 'react-native';

export const ChatbotScreen = () => {
  const [messages, setMessages] = useState([
    { id: '1', text: 'Hello! I am NutriBot, your personal nutrition assistant. I can provide diet and nutrition advice based on your profile. Please note: I am not a substitute for professional medical advice. Always consult a healthcare provider for medical decisions.', sender: 'bot' }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const flatListRef = useRef<FlatList>(null);
  const [inputHeight, setInputHeight] = useState(40);

  useEffect(() => {
    const fetchProfile = async () => {
      const userId = auth.currentUser?.uid;
      if (userId) {
        const profile = await getUserProfile(userId);
        setUserProfile(profile);
      }
    };
    fetchProfile();
  }, []);

  useEffect(() => {
    if (flatListRef.current) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  const buildSystemPrompt = () => {
    let prompt = `You are NutriBot, a cautious and helpful nutrition assistant. You provide diet and nutrition advice based on the user's profile. Never give medical advice, and always recommend consulting a healthcare professional for medical concerns. If you are unsure, say so.\n`;
    if (userProfile) {
      prompt += `\nUser Profile:\n`;
      if (userProfile.age) prompt += `Age: ${userProfile.age}\n`;
      if (userProfile.gender) prompt += `Gender: ${userProfile.gender}\n`;
      if (userProfile.currentWeight) prompt += `Current Weight: ${userProfile.currentWeight} kg\n`;
      if (userProfile.goalWeight) prompt += `Goal Weight: ${userProfile.goalWeight} kg\n`;
      if (userProfile.height) prompt += `Height: ${userProfile.height} cm\n`;
      if (userProfile.dietaryPreference) prompt += `Dietary Preference: ${userProfile.dietaryPreference}\n`;
      if (userProfile.favouriteCuisine) prompt += `Favourite Cuisine: ${userProfile.favouriteCuisine}\n`;
      if (userProfile.allergies) prompt += `Allergies: ${userProfile.allergies}\n`;
      if (userProfile.medicalConditions) prompt += `Medical Conditions: ${userProfile.medicalConditions}\n`;
      if (userProfile.targetCalories) prompt += `Calories Goal: ${userProfile.targetCalories} kcal\n`;
      if (userProfile.stepGoal) prompt += `Steps Goal: ${userProfile.stepGoal}\n`;
      if (userProfile.caloriesBurnedGoal) prompt += `Calories Burned Goal: ${userProfile.caloriesBurnedGoal}\n`;
    }
    prompt += '\nNever change or update user information. Only use it for context.';
    return prompt;
  };

  const handleSend = async () => {
    if (inputText.trim().length === 0) return;
    const newMessage = { id: Date.now().toString(), text: inputText, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, newMessage]);
    setInputText('');
    setLoading(true);
    // Add Typing... animation
    setMessages(prevMessages => [...prevMessages, { id: 'typing', text: 'Typing...', sender: 'bot' }]);
    try {
      const userId = auth.currentUser?.uid || '';
      // Prepare chat history for backend (array of { sender, text })
      const chat_history = [
        ...messages.filter(m => m.sender !== 'bot' || m.text !== 'Typing...').map(m => ({
          sender: m.sender,
          text: m.text
        }))
      ];
      const botText = await sendChatbotMessage(
        userId,
        chat_history,
        userProfile,
        inputText
      );
      setMessages(prevMessages => [
        ...prevMessages.filter(m => m.id !== 'typing'),
        { id: Date.now().toString(), text: botText, sender: 'bot' }
      ]);
    } catch (err) {
      setMessages(prevMessages => [
        ...prevMessages.filter(m => m.id !== 'typing'),
        { id: Date.now().toString(), text: 'Sorry, there was an error connecting to the nutrition assistant.', sender: 'bot' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = ({ item }: { item: { id: string; text: string; sender: string } }) => {
    const isUserMessage = item.sender === 'user';
    if (item.id === 'typing') {
      return (
        <View style={[styles.messageBubble, styles.botMessage, { flexDirection: 'row', alignItems: 'center' }]}> 
          <ActivityIndicator size="small" color="#6EE7B7" style={{ marginRight: 8 }} />
          <Text style={styles.messageText}>{item.text}</Text>
        </View>
      );
    }
    return (
      <View style={[
        styles.messageBubble,
        isUserMessage ? styles.userMessage : styles.botMessage
      ]}>
        {isUserMessage ? (
          <Text style={styles.messageText}>{item.text}</Text>
        ) : (
          <Markdown style={{ body: styles.messageText }}>{item.text}</Markdown>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.chatbotContainer}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={item => item.id}
          contentContainerStyle={{ paddingVertical: 10, paddingHorizontal: 10 }}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={[styles.chatInput, { height: Math.max(40, Math.min(inputHeight, 120)) }]}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type a message..."
            placeholderTextColor="#A1A1AA"
            editable={!loading}
            multiline
            onContentSizeChange={e => setInputHeight(e.nativeEvent.contentSize.height)}
            textAlignVertical="top"
          />
          <TouchableOpacity onPress={handleSend} style={styles.sendButton} disabled={loading}>
            <Send color="#6EE7B7" size={24} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  chatbotContainer: {
    flex: 1,
    backgroundColor: '#F0FFF4', // Using direct color value from COLORS
    paddingTop: 60,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  chatInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    backgroundColor: '#F0FFF4',
    borderRadius: 20,
    paddingHorizontal: 15,
    marginRight: 10,
    fontSize: 16,
    color: '#27272A',
  },
  sendButton: {
    padding: 5,
  },
  messageBubble: {
    padding: 12,
    borderRadius: 18,
    marginVertical: 4,
    maxWidth: '90%',
    flexWrap: 'wrap',
  },
  userMessage: {
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  botMessage: {
    backgroundColor: '#E6F8F0',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    color: '#27272A',
    flexWrap: 'wrap',
    width: 'auto',
    alignSelf: 'flex-start',
  },
}); 