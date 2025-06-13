import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const ConfettiAnimation: React.FC = () => {
  const [pieces, setPieces] = useState<Array<{
    id: number;
    x: number;
    color: string;
    delay: number;
  }>>([]);

  useEffect(() => {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'];
    const newPieces = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: colors[Math.floor(Math.random() * colors.length)],
      delay: Math.random() * 2,
    }));
    setPieces(newPieces);
  }, []);

  return (
    <div className="confetti">
      {pieces.map((piece) => (
        <motion.div
          key={piece.id}
          className="confetti-piece"
          style={{
            backgroundColor: piece.color,
            left: `${piece.x}%`,
          }}
          initial={{ y: -100, rotate: 0, opacity: 1 }}
          animate={{ 
            y: window.innerHeight + 100, 
            rotate: 360,
            opacity: 0 
          }}
          transition={{
            duration: 3,
            delay: piece.delay,
            ease: "easeOut"
          }}
        />
      ))}
    </div>
  );
};

export default ConfettiAnimation;
