import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for Colonel WebSocket communication.
 * Handles connection, reconnection, streaming chunks, and ping/pong.
 */
export default function useColonelWebSocket(sessionId = null) {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [colonelName, setColonelName] = useState('The Colonel');
  const [serverName, setServerName] = useState('');
  const [writeEnabled, setWriteEnabled] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);

  // Track pending confirmation requests
  const [pendingConfirm, setPendingConfirm] = useState(null);

  // Track active skill executions
  const [activeSkill, setActiveSkill] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const pingTimer = useRef(null);
  const streamBuffer = useRef('');
  const reconnectAttempts = useRef(0);
  const maxReconnects = 5;

  const buildWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    let url = `${protocol}//${host}/ws/colonel`;
    if (currentSessionId) {
      url += `?session_id=${currentSessionId}`;
    }
    return url;
  }, [currentSessionId]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (connecting) return;

    setConnecting(true);
    setError(null);

    const ws = new WebSocket(buildWsUrl());

    ws.onopen = () => {
      setConnecting(false);
      setConnected(true);
      reconnectAttempts.current = 0;

      // Start ping interval (every 30s)
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      try {
        const frame = JSON.parse(event.data);
        handleFrame(frame);
      } catch (e) {
        console.error('Failed to parse WS frame:', e);
      }
    };

    ws.onclose = (event) => {
      setConnected(false);
      setConnecting(false);
      setIsStreaming(false);
      clearInterval(pingTimer.current);

      if (event.code === 4001 || event.code === 4003) {
        // Auth error — don't reconnect
        setError(event.reason || 'Authentication required');
        return;
      }

      // Auto-reconnect with exponential backoff
      if (reconnectAttempts.current < maxReconnects) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        reconnectTimer.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      setConnecting(false);
      setError('Connection error');
    };

    wsRef.current = ws;
  }, [buildWsUrl, connecting]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    clearInterval(pingTimer.current);
    reconnectAttempts.current = maxReconnects; // Prevent reconnect
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect');
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const handleFrame = useCallback((frame) => {
    switch (frame.type) {
      case 'connected':
        setCurrentSessionId(frame.session_id);
        setColonelName(frame.colonel_name || 'The Colonel');
        setServerName(frame.server_name || '');
        setWriteEnabled(frame.write_enabled || false);
        break;

      case 'chunk':
        streamBuffer.current += frame.content;
        setIsStreaming(true);
        // Update the last assistant message in-place
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant' && last._streaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: streamBuffer.current },
            ];
          }
          // Start a new streaming message
          return [
            ...prev,
            { role: 'assistant', content: streamBuffer.current, _streaming: true, id: frame.id },
          ];
        });
        break;

      case 'message_done':
        streamBuffer.current = '';
        setIsStreaming(false);
        // Finalize the streaming message
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last && last.role === 'assistant' && last._streaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: frame.content, _streaming: false },
            ];
          }
          return prev;
        });
        break;

      case 'error':
        setIsStreaming(false);
        streamBuffer.current = '';
        setError(frame.detail);
        break;

      case 'skill_start':
        setActiveSkill({ name: frame.skill_name, action: frame.action, output: '' });
        break;

      case 'skill_progress':
        setActiveSkill(prev => prev ? { ...prev, output: prev.output + frame.output } : null);
        break;

      case 'skill_result':
        setActiveSkill(null);
        // Add skill result as a system-like message
        setMessages(prev => [
          ...prev,
          {
            role: 'skill_result',
            skill_name: frame.skill_name,
            action: frame.action,
            success: frame.success,
            content: frame.output,
            duration_ms: frame.duration_ms,
          },
        ]);
        break;

      case 'confirm_required':
        setPendingConfirm({
          skill_name: frame.skill_name,
          action: frame.action,
          description: frame.description,
          params: frame.params,
          confirm_id: frame.id,
        });
        break;

      case 'pong':
        // Keepalive acknowledged
        break;

      default:
        console.warn('Unknown Colonel WS frame type:', frame.type);
    }
  }, []);

  const sendMessage = useCallback((content) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected');
      return;
    }

    // Add user message to local state immediately
    setMessages(prev => [
      ...prev,
      { role: 'user', content, id: Date.now().toString() },
    ]);

    // Reset stream buffer
    streamBuffer.current = '';

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content,
    }));
  }, []);

  const confirmAction = useCallback((confirmId, confirmed) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(JSON.stringify({
      type: 'confirm',
      confirm_id: confirmId,
      confirmed,
    }));

    setPendingConfirm(null);
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  // Reconnect when session ID changes
  useEffect(() => {
    if (sessionId && sessionId !== currentSessionId) {
      setCurrentSessionId(sessionId);
      setMessages([]); // Clear messages for new session
      disconnect();
      // Small delay then reconnect
      setTimeout(connect, 100);
    }
  }, [sessionId]);

  return {
    connected,
    connecting,
    colonelName,
    serverName,
    writeEnabled,
    currentSessionId,
    messages,
    isStreaming,
    error,
    activeSkill,
    pendingConfirm,
    sendMessage,
    confirmAction,
    connect,
    disconnect,
    setMessages,
    clearError: () => setError(null),
    startNewSession: () => {
      setCurrentSessionId(null);
      setMessages([]);
      disconnect();
      setTimeout(connect, 100);
    },
  };
}
