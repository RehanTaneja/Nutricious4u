import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Dimensions } from 'react-native';

const { width, height } = Dimensions.get('window');

const ConfettiPiece = ({ delay, color }) => {
  const animatedValue = useRef(new Animated.Value(0)).current;
  const rotateValue = useRef(new Animated.Value(0)).current;
  const swayValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const fallAnimation = Animated.timing(animatedValue, {
      toValue: 1,
      duration: 3000,
      delay: delay,
      useNativeDriver: true,
    });

    const rotateAnimation = Animated.loop(
      Animated.timing(rotateValue, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      })
    );

    const swayAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(swayValue, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(swayValue, {
          toValue: -1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    );

    Animated.parallel([fallAnimation, rotateAnimation, swayAnimation]).start();
  }, []);

  const translateY = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [-100, height + 100],
  });

  const translateX = swayValue.interpolate({
    inputRange: [-1, 1],
    outputRange: [-50, 50],
  });

  const rotate = rotateValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Animated.View
      style={[
        styles.confettiPiece,
        {
          backgroundColor: color,
          transform: [
            { translateY },
            { translateX },
            { rotate },
          ],
        },
      ]}
    />
  );
};

export default function ConfettiAnimation() {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'];
  
  const confettiPieces = Array.from({ length: 50 }, (_, index) => (
    <ConfettiPiece
      key={index}
      delay={Math.random() * 2000}
      color={colors[Math.floor(Math.random() * colors.length)]}
    />
  ));

  return (
    <View style={styles.container} pointerEvents="none">
      {confettiPieces}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
  },
  confettiPiece: {
    position: 'absolute',
    width: 10,
    height: 10,
    borderRadius: 5,
    left: Math.random() * width,
  },
});
