import React from 'react';

export const AppContext = React.createContext({
  hasCompletedQuiz: false,
  setHasCompletedQuiz: (value: boolean) => {},
}); 