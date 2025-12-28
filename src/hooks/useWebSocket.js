/**
 * useWebSocket Hook
 *
 * Provides real-time WebSocket connection with automatic reconnection,
 * channel subscriptions, and message handling.
 *
 * Usage:
 * ```
 * const { connected, messages, send, subscribe, unsubscribe } = useWebSocket(['permissions', 'usage']);
 * ```
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = window.location.protocol === 'https:'
  ? `wss://${window.location.host}/ws`
  : `ws://${window.location.host}/ws`;

const RECONNECT_INTERVAL = 5000; // 5 seconds
const MAX_RECONNECT_ATTEMPTS = 10;
const PONG_TIMEOUT = 45000; // 45 seconds (ping interval is 30s)

export function useWebSocket(initialChannels = []) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const ws = useRef(null);
  const reconnectTimer = useRef(null);
  const pongTimer = useRef(null);
  const channelsRef = useRef(initialChannels);
  const messageHandlersRef = useRef([]);

  // Get auth token from localStorage
  const getAuthToken = useCallback(() => {
    return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
  }, []);

  // Get org ID from localStorage
  const getOrgId = useCallback(() => {
    return localStorage.getItem('currentOrgId');
  }, []);

  // Send message
  const send = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  // Subscribe to channels
  const subscribe = useCallback((channels) => {
    if (!Array.isArray(channels)) {
      channels = [channels];
    }

    // Add to channels ref
    channelsRef.current = [...new Set([...channelsRef.current, ...channels])];

    // Send subscribe message if connected
    send({
      type: 'subscribe',
      channels: channels
    });
  }, [send]);

  // Unsubscribe from channels
  const unsubscribe = useCallback((channels) => {
    if (!Array.isArray(channels)) {
      channels = [channels];
    }

    // Remove from channels ref
    channelsRef.current = channelsRef.current.filter(ch => !channels.includes(ch));

    // Send unsubscribe message if connected
    send({
      type: 'unsubscribe',
      channels: channels
    });
  }, [send]);

  // Add message handler
  const addMessageHandler = useCallback((handler) => {
    messageHandlersRef.current.push(handler);

    // Return function to remove handler
    return () => {
      messageHandlersRef.current = messageHandlersRef.current.filter(h => h !== handler);
    };
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((event) => {
    try {
      const message = JSON.parse(event.data);

      // Handle ping/pong
      if (message.type === 'ping') {
        send({ type: 'pong' });

        // Reset pong timeout
        if (pongTimer.current) {
          clearTimeout(pongTimer.current);
        }
        pongTimer.current = setTimeout(() => {
          console.warn('No ping received, reconnecting...');
          ws.current?.close();
        }, PONG_TIMEOUT);

        return;
      }

      // Handle connection confirmation
      if (message.type === 'connected') {
        console.log('WebSocket connected:', message);
        setConnected(true);
        setReconnectAttempts(0);
        return;
      }

      // Handle subscription confirmation
      if (message.type === 'subscribed' || message.type === 'unsubscribed') {
        console.log('Channel subscription updated:', message);
        return;
      }

      // Add to messages
      setMessages(prev => {
        const newMessages = [...prev, message];
        // Keep last 100 messages
        if (newMessages.length > 100) {
          newMessages.shift();
        }
        return newMessages;
      });

      // Call message handlers
      messageHandlersRef.current.forEach(handler => {
        try {
          handler(message);
        } catch (err) {
          console.error('Message handler error:', err);
        }
      });

    } catch (err) {
      console.error('WebSocket message parse error:', err);
    }
  }, [send]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    const token = getAuthToken();
    const orgId = getOrgId();

    if (!token) {
      console.warn('No auth token, cannot connect to WebSocket');
      return;
    }

    // Build WebSocket URL with params
    const params = new URLSearchParams({
      token: token
    });

    if (orgId) {
      params.append('org_id', orgId);
    }

    if (channelsRef.current.length > 0) {
      params.append('channels', channelsRef.current.join(','));
    }

    const wsUrl = `${WS_URL}?${params.toString()}`;

    console.log('Connecting to WebSocket...');

    // Create WebSocket connection
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connection established');
      setConnected(true);
      setReconnectAttempts(0);
    };

    ws.current.onmessage = handleMessage;

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.current.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason);
      setConnected(false);

      // Clear pong timer
      if (pongTimer.current) {
        clearTimeout(pongTimer.current);
      }

      // Attempt reconnection
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        console.log(`Reconnecting in ${RECONNECT_INTERVAL / 1000}s (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})...`);

        reconnectTimer.current = setTimeout(() => {
          setReconnectAttempts(prev => prev + 1);
          connect();
        }, RECONNECT_INTERVAL);
      } else {
        console.error('Max reconnection attempts reached');
      }
    };
  }, [getAuthToken, getOrgId, handleMessage, reconnectAttempts]);

  // Initial connection
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      if (pongTimer.current) {
        clearTimeout(pongTimer.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []); // Only connect once on mount

  // Handle channel changes
  useEffect(() => {
    if (connected && initialChannels.length > 0) {
      subscribe(initialChannels);
    }
  }, [connected, initialChannels, subscribe]);

  return {
    connected,
    messages,
    send,
    subscribe,
    unsubscribe,
    addMessageHandler,
    reconnectAttempts
  };
}

/**
 * useWebSocketMessage Hook
 *
 * Subscribe to specific message types and execute callback.
 *
 * Usage:
 * ```
 * useWebSocketMessage('permission_change', (message) => {
 *   console.log('Permission changed:', message);
 * });
 * ```
 */
export function useWebSocketMessage(messageType, callback, deps = []) {
  const { addMessageHandler } = useWebSocket([]);

  useEffect(() => {
    const removeHandler = addMessageHandler((message) => {
      if (message.type === messageType) {
        callback(message);
      }
    });

    return removeHandler;
  }, [messageType, callback, addMessageHandler, ...deps]);
}

/**
 * useWebSocketChannel Hook
 *
 * Subscribe to specific channel and get messages from that channel only.
 *
 * Usage:
 * ```
 * const { messages: permissionMessages } = useWebSocketChannel('permissions');
 * ```
 */
export function useWebSocketChannel(channel) {
  const { messages, subscribe, unsubscribe } = useWebSocket([]);
  const [channelMessages, setChannelMessages] = useState([]);

  useEffect(() => {
    subscribe(channel);

    return () => {
      unsubscribe(channel);
    };
  }, [channel, subscribe, unsubscribe]);

  useEffect(() => {
    const filtered = messages.filter(msg => msg.channel === channel);
    setChannelMessages(filtered);
  }, [messages, channel]);

  return { messages: channelMessages };
}
