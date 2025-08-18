import React, { createContext, useContext, useState } from 'react';
import { auth } from '../services/firebase';

interface SubscriptionContextType {
  showUpgradeModal: boolean;
  setShowUpgradeModal: (show: boolean) => void;
  isFreeUser: boolean;
  setIsFreeUser: (isFree: boolean) => void;
  refreshSubscriptionStatus: () => void;
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

  const refreshSubscriptionStatus = async () => {
    try {
      // Add delay to prevent conflict with login sequence
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const { getSubscriptionStatus } = await import('../services/api');
      const user = auth.currentUser;
      if (user) {
        const subscriptionStatus = await getSubscriptionStatus(user.uid);
        setIsFreeUser(subscriptionStatus.isFreeUser || !subscriptionStatus.isSubscriptionActive);
      }
    } catch (error) {
      console.log('Error refreshing subscription status:', error);
      setIsFreeUser(true);
    }
  };

  return (
    <SubscriptionContext.Provider value={{
      showUpgradeModal,
      setShowUpgradeModal,
      isFreeUser,
      setIsFreeUser,
      refreshSubscriptionStatus,
    }}>
      {children}
    </SubscriptionContext.Provider>
  );
};
