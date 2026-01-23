import React, { createContext, useContext, useState } from 'react';
import { auth } from '../services/firebase';
import { getSubscriptionStatus } from '../services/api';

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
      
      const user = auth.currentUser;
      if (user) {
        const subscriptionStatus = await getSubscriptionStatus(user.uid);
        // Trial users should NOT be treated as free users - they have premium access
        // Logic:
        // 1. If user is on trial (isTrialActive = true), they are NOT free
        // 2. If subscription is active, user is NOT free (regardless of trial status)
        // 3. Otherwise, use backend's isFreeUser flag
        const isTrialActive = subscriptionStatus.isTrialActive === true;
        const isSubscriptionActive = subscriptionStatus.isSubscriptionActive === true;
        
        // User is free only if: NOT on trial AND subscription not active AND backend says free
        const shouldBeFreeUser = !isTrialActive && 
                                  !isSubscriptionActive && 
                                  (subscriptionStatus.isFreeUser !== false); // Default to free if undefined
        setIsFreeUser(shouldBeFreeUser);
        console.log('[SubscriptionContext] Updated isFreeUser:', shouldBeFreeUser, {
          isTrialActive: subscriptionStatus.isTrialActive,
          isFreeUser: subscriptionStatus.isFreeUser,
          isSubscriptionActive: subscriptionStatus.isSubscriptionActive
        });
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
