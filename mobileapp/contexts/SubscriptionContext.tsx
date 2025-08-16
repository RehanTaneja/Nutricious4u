import React, { createContext, useContext, useState } from 'react';

interface SubscriptionContextType {
  showUpgradeModal: boolean;
  setShowUpgradeModal: (show: boolean) => void;
  isFreeUser: boolean;
  setIsFreeUser: (isFree: boolean) => void;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

export const SubscriptionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isFreeUser, setIsFreeUser] = useState(true); // Default to free user

  return (
    <SubscriptionContext.Provider value={{
      showUpgradeModal,
      setShowUpgradeModal,
      isFreeUser,
      setIsFreeUser,
    }}>
      {children}
    </SubscriptionContext.Provider>
  );
};
