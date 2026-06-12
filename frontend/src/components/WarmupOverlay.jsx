/**
 * WarmupOverlay Component
 *
 * Shows an overlay while waking up the Render backend. Polls /health and
 * stays up until the backend actually responds (instead of a fixed timer),
 * and skips entirely when the backend is already warm. Re-checks when the
 * tab becomes visible again after 5+ minutes away.
 */

import { useState, useEffect, useRef } from 'react';
import { api, waitForBackend, resetBackendWait } from '../api/client';
import './WarmupOverlay.css';

const SHOW_DELAY = 600; // Only show if the backend hasn't answered this fast
const READY_LINGER = 900; // How long to show the "ready" state before hiding
const HIDDEN_THRESHOLD = 5 * 60 * 1000; // Re-check after 5 minutes away

export function WarmupOverlay() {
  const [visible, setVisible] = useState(false);
  const [backendReady, setBackendReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const lastVisibleTime = useRef(Date.now());
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const waitUntilReady = () => {
    setFailed(false);
    setBackendReady(false);

    // Only show the overlay if the backend doesn't answer almost immediately
    const showTimer = setTimeout(() => setVisible(true), SHOW_DELAY);

    waitForBackend()
      .then(() => {
        if (!mountedRef.current) return;
        clearTimeout(showTimer);
        setBackendReady(true);
        setTimeout(() => {
          if (mountedRef.current) setVisible(false);
        }, READY_LINGER);
      })
      .catch(() => {
        if (!mountedRef.current) return;
        setFailed(true);
      });
  };

  // Initial warmup on mount
  useEffect(() => {
    waitUntilReady();
  }, []);

  // Re-check when returning to the tab after a long absence
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.hidden) {
        lastVisibleTime.current = Date.now();
        return;
      }

      const hiddenDuration = Date.now() - lastVisibleTime.current;
      if (hiddenDuration < HIDDEN_THRESHOLD) return;

      try {
        // Still warm? Then no overlay needed.
        await api.getHealth();
      } catch {
        resetBackendWait();
        waitUntilReady();
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

        <h2>{backendReady ? "We're good to go!" : 'Waking up the server...'}</h2>

        <p className="warmup-explanation">
          Hey! This is a student project, so I'm using Render's free tier for the backend.
          It goes to sleep after 15 minutes of inactivity to save resources.
        </p>

        <p className="warmup-status">
          {failed
            ? "Hmm, it's taking unusually long. Check back in a minute?"
            : backendReady
              ? 'Connected.'
              : "Give it a few seconds (or up to a minute if it's really sleepy)..."
          }
        </p>

        {failed && (
          <button className="warmup-retry" onClick={waitUntilReady}>
            Try again
          </button>
        )}

        {backendReady && (
          <div className="warmup-ready-icon">✓</div>
        )}
      </div>
    </div>
  );
}

export default WarmupOverlay;
