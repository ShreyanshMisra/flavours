/**
 * WarmupOverlay Component
 *
 * Shows a friendly overlay while waking up the Render backend.
 * Displays for 5 seconds on initial load or when returning after 5+ minutes.
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import './WarmupOverlay.css';

const OVERLAY_DURATION = 5000; // 5 seconds
const HIDDEN_THRESHOLD = 5 * 60 * 1000; // 5 minutes in ms

export function WarmupOverlay() {
  const [visible, setVisible] = useState(true);
  const [backendReady, setBackendReady] = useState(false);
  const lastVisibleTime = useRef(Date.now());
  const hasShownInitial = useRef(false);

  // Warm up the backend
  const warmupBackend = async () => {
    try {
      await api.getHealth();
      setBackendReady(true);
    } catch (error) {
      // Backend might still be waking up, that's okay
      console.log('Backend warming up...', error.message);
    }
  };

  // Initial warmup on mount
  useEffect(() => {
    if (!hasShownInitial.current) {
      hasShownInitial.current = true;
      warmupBackend();

      // Hide overlay after 5 seconds regardless of backend status
      const timer = setTimeout(() => {
        setVisible(false);
      }, OVERLAY_DURATION);

      return () => clearTimeout(timer);
    }
  }, []);

  // Track tab visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab is now hidden, record the time
        lastVisibleTime.current = Date.now();
      } else {
        // Tab is now visible, check how long it was hidden
        const hiddenDuration = Date.now() - lastVisibleTime.current;

        if (hiddenDuration >= HIDDEN_THRESHOLD) {
          // Been away for 5+ minutes, show overlay and warm up again
          setVisible(true);
          setBackendReady(false);
          warmupBackend();

          setTimeout(() => {
            setVisible(false);
          }, OVERLAY_DURATION);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  if (!visible) return null;

  return (
    <div className={`warmup-overlay ${backendReady ? 'ready' : ''}`}>
      <div className="warmup-content">
        <div className="warmup-spinner"></div>

        <h2>Waking up the server...</h2>

        <p className="warmup-explanation">
          Hey! This is a student project, so I'm using Render's free tier for the backend.
          It goes to sleep after 15 minutes of inactivity to save resources.
        </p>

        <p className="warmup-status">
          {backendReady
            ? "We're good to go!"
            : "Give it a few seconds (or up to a minute if it's really sleepy)..."
          }
        </p>

        {backendReady && (
          <div className="warmup-ready-icon">✓</div>
        )}
      </div>
    </div>
  );
}

export default WarmupOverlay;
