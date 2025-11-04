/**
 * User ID Manager
 * Manages user_id for memory system with support for:
 * - Microsoft authenticated users (actual MS user ID)
 * - Guest users (browser-persistent unique ID)
 */

import { useState, useEffect } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const GUEST_ID_KEY = "guest_user_id";

/**
 * Generate a unique guest ID for browsers without authentication
 * Format: guest_<timestamp>_<random>
 */
function generateGuestId() {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 10);
  return `guest_${timestamp}_${randomPart}`;
}

/**
 * Get or create guest ID from localStorage
 */
function getGuestId() {
  let guestId = localStorage.getItem(GUEST_ID_KEY);

  if (!guestId) {
    guestId = generateGuestId();
    localStorage.setItem(GUEST_ID_KEY, guestId);
    console.log('[UserID] Generated new guest ID:', guestId);
  }

  return guestId;
}

/**
 * Get current user ID - only authenticated MS ID, no guest fallback
 * @returns {Promise<{userId: string|null, isAuthenticated: boolean, displayName: string|null}>}
 */
export async function getCurrentUserId() {
  try {
    // Get session_id from sessionStorage (set after OAuth redirect)
    const sessionId = sessionStorage.getItem('user_session_id');

    // Call backend with session_id in body
    const response = await fetch(`${API_BASE}/auth/me`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
      credentials: 'include' // Still send cookies for backward compatibility
    });
    const data = await response.json();

    if (data.authenticated && data.user_id) {
      console.log('[UserID] Authenticated user:', data.user_id, data.display_name);
      // Update sessionStorage with confirmed user_id
      sessionStorage.setItem('user_session_id', data.user_id);
      return {
        userId: data.user_id, // Actual Microsoft user ID
        isAuthenticated: true,
        displayName: data.display_name,
        email: data.email
      };
    }
  } catch (error) {
    console.warn('[UserID] Failed to get authenticated user:', error);
  }

  // No guest fallback - return null if not authenticated
  console.debug('[UserID] Not authenticated - no user ID');
  return {
    userId: null,
    isAuthenticated: false,
    displayName: null,
    email: null
  };
}

/**
 * Clear guest ID (useful for logout or reset)
 */
export function clearGuestId() {
  localStorage.removeItem(GUEST_ID_KEY);
  console.log('[UserID] Guest ID cleared');
}

/**
 * React hook for using user ID in components
 * Usage:
 * ```
 * const { userId, isAuthenticated, loading } = useUserId();
 * ```
 */
export function useUserId() {
  const [userInfo, setUserInfo] = useState({
    userId: null,
    isAuthenticated: false,
    displayName: null,
    email: null,
    loading: true
  });

  useEffect(() => {
    getCurrentUserId().then(info => {
      setUserInfo({ ...info, loading: false });
    });
  }, []);

  return userInfo;
}
