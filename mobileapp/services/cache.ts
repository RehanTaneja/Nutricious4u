import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
}

class DashboardCache {
  private memoryCache = new Map<string, CacheEntry>();
  private readonly TTL = {
    userProfile: 5 * 60 * 1000,    // 5 minutes
    logSummary: 2 * 60 * 1000,      // 2 minutes  
    workoutSummary: 2 * 60 * 1000,  // 2 minutes
    dietData: 10 * 60 * 1000        // 10 minutes
  };

  // Safe cache key generation
  private getCacheKey(key: string, userId: string): string {
    return `cache_${key}_${userId}`;
  }

  // Safe memory cache get
  async getCachedData(key: string, userId: string, fetchFn: () => Promise<any>): Promise<any> {
    try {
      const cacheKey = this.getCacheKey(key, userId);
      
      // Check memory cache first
      const memoryEntry = this.memoryCache.get(cacheKey);
      if (memoryEntry && Date.now() - memoryEntry.timestamp < memoryEntry.ttl) {
        console.log(`[Cache] Memory hit for ${key}`);
        return memoryEntry.data;
      }

      // Check disk cache
      const diskData = await AsyncStorage.getItem(cacheKey);
      if (diskData) {
        const diskEntry: CacheEntry = JSON.parse(diskData);
        if (Date.now() - diskEntry.timestamp < diskEntry.ttl) {
          console.log(`[Cache] Disk hit for ${key}`);
          // Update memory cache
          this.memoryCache.set(cacheKey, diskEntry);
          return diskEntry.data;
        }
      }

      // Fetch fresh data
      console.log(`[Cache] Cache miss for ${key}, fetching fresh data`);
      const freshData = await fetchFn();
      
      // Store in both caches
      const cacheEntry: CacheEntry = {
        data: freshData,
        timestamp: Date.now(),
        ttl: this.TTL[key] || 5 * 60 * 1000
      };

      this.memoryCache.set(cacheKey, cacheEntry);
      await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheEntry));

      return freshData;
    } catch (error) {
      console.error(`[Cache] Error in getCachedData for ${key}:`, error);
      // Fallback to direct fetch
      return await fetchFn();
    }
  }

  // Safe cache invalidation
  async invalidateCache(key: string, userId: string): Promise<void> {
    try {
      const cacheKey = this.getCacheKey(key, userId);
      this.memoryCache.delete(cacheKey);
      await AsyncStorage.removeItem(cacheKey);
      console.log(`[Cache] Invalidated cache for ${key}`);
    } catch (error) {
      console.error(`[Cache] Error invalidating cache for ${key}:`, error);
    }
  }

  // Safe cache cleanup
  async cleanupExpiredCache(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith('cache_'));
      
      for (const key of cacheKeys) {
        const data = await AsyncStorage.getItem(key);
        if (data) {
          const entry: CacheEntry = JSON.parse(data);
          if (Date.now() - entry.timestamp >= entry.ttl) {
            await AsyncStorage.removeItem(key);
            console.log(`[Cache] Cleaned up expired cache: ${key}`);
          }
        }
      }
    } catch (error) {
      console.error('[Cache] Error cleaning up cache:', error);
    }
  }

  // Clear all cache for a user (useful for logout)
  async clearUserCache(userId: string): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const userCacheKeys = keys.filter(key => key.includes(`_${userId}`));
      
      for (const key of userCacheKeys) {
        await AsyncStorage.removeItem(key);
        this.memoryCache.delete(key);
      }
      console.log(`[Cache] Cleared all cache for user ${userId}`);
    } catch (error) {
      console.error('[Cache] Error clearing user cache:', error);
    }
  }
}

// Export singleton instance
export const dashboardCache = new DashboardCache();
