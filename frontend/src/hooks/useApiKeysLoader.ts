/**
 * Loads user API keys into the store when userId is available.
 * This ensures API keys persist across app restarts.
 */

import { useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { getUserApiKeys } from '@/utils/api';

export function useApiKeysLoader() {
  const userId = useChatStore((state) => state.userId);
  const setApiKeys = useChatStore((state) => state.setApiKeys);

  useEffect(() => {
    async function loadApiKeys() {
      if (!userId) return;
      
      try {
        const keys = await getUserApiKeys(userId);
        // Update store with masked keys (they're already masked from the API)
        // The store tracks existence, not the actual key values
        setApiKeys({
          openai: keys.openai_key || null,
          anthropic: keys.anthropic_key || null,
        });
      } catch (err) {
        console.error('Failed to load API keys:', err);
        // On error, set to null so the warning modal can show
        setApiKeys({ openai: null, anthropic: null });
      }
    }

    loadApiKeys();
  }, [userId, setApiKeys]);
}

