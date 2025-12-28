/**
 * Geeses.jsx - Navigator Geeses AI Assistant Chat Interface
 *
 * Provides conversational interface to Geeses AI agent for Ops-Center management.
 * Features:
 * - Real-time chat with message history
 * - Tool execution visualization
 * - System status sidebar with live metrics
 * - Military-themed purple/gold UI matching Ops-Center
 *
 * @author Chat Interface Developer (AI Agent Team)
 * @version 1.0.0
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  LinearProgress,
  Grid,
  Tooltip,
  Drawer,
  AppBar,
  Toolbar,
  Badge,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as UserIcon,
  Build as ToolIcon,
  Speed as MetricsIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

/**
 * Styled Components
 */
const ChatContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  height: 'calc(100vh - 64px)',
  background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%)',
}));

const ChatMain = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(3),
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: 'rgba(255, 255, 255, 0.05)',
  },
  '&::-webkit-scrollbar-thumb': {
    background: 'rgba(138, 43, 226, 0.3)',
    borderRadius: '4px',
  },
}));

const MessageBubble = styled(Paper)(({ theme, role }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  maxWidth: '70%',
  background: role === 'user'
    ? 'linear-gradient(135deg, #8a2be2 0%, #9d4edd 100%)'
    : 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)',
  color: '#ffffff',
  borderRadius: '12px',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
  alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  background: 'rgba(255, 255, 255, 0.05)',
  backdropFilter: 'blur(10px)',
  borderTop: '1px solid rgba(255, 255, 255, 0.1)',
}));

const SidebarContainer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: 320,
    background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)',
    borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
    color: '#ffffff',
  },
}));

const StatusCard = styled(Card)(({ theme }) => ({
  background: 'rgba(255, 255, 255, 0.05)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  marginBottom: theme.spacing(2),
  color: '#ffffff',
}));

/**
 * Geeses Chat Component
 */
const Geeses = () => {
  // State management
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [geesesAgent, setGeesesAgent] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Refs
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  // Configuration
  const BRIGADE_API_URL = process.env.REACT_APP_BRIGADE_API_URL || 'https://api.brigade.your-domain.com';
  const ATLAS_AGENT_ID = process.env.REACT_APP_ATLAS_AGENT_ID || 'geeses';

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /**
   * Initialize session on mount
   */
  useEffect(() => {
    initializeSession();
    fetchSystemStatus();

    // Set up interval for system status updates
    const statusInterval = setInterval(fetchSystemStatus, 30000); // Every 30 seconds

    return () => {
      clearInterval(statusInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  /**
   * Initialize chat session
   */
  const initializeSession = async () => {
    try {
      // Generate or retrieve session ID
      let sid = sessionStorage.getItem('geeses_session_id');
      if (!sid) {
        sid = `geeses-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('geeses_session_id', sid);
      }
      setSessionId(sid);

      // Fetch Geeses agent info
      const response = await fetch(`${BRIGADE_API_URL}/api/agents/${ATLAS_AGENT_ID}/card`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (response.ok) {
        const agentData = await response.json();
        setGeesesAgent(agentData);
      }

      // Add welcome message
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: 'Roger that, Navigator Geeses reporting for duty. How can I assist with Ops-Center operations today?',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Failed to initialize Geeses session:', error);
    }
  };

  /**
   * Fetch system status for sidebar
   */
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  /**
   * Send message to Geeses
   */
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Get current page context
      const context = {
        page: window.location.pathname,
        user_id: localStorage.getItem('userId'),
        timestamp: new Date().toISOString(),
      };

      const response = await fetch(`${BRIGADE_API_URL}/api/agents/${ATLAS_AGENT_ID}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          context,
          sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Add Geeses response
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || data.message || 'Received',
        toolsUsed: data.toolsUsed || data.tools_used || [],
        data: data.data,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Communication error: ${error.message}. Service may be temporarily unavailable.`,
        error: true,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /**
   * Render message with tool usage
   */
  const renderMessage = (message) => {
    return (
      <Box key={message.id} sx={{ display: 'flex', flexDirection: 'column', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Avatar
            sx={{
              bgcolor: message.role === 'user' ? '#8a2be2' : '#3b82f6',
              width: 32,
              height: 32,
            }}
          >
            {message.role === 'user' ? <UserIcon fontSize="small" /> : <BotIcon fontSize="small" />}
          </Avatar>

          <MessageBubble role={message.role} elevation={3}>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {message.content}
            </Typography>

            {/* Tool usage indicators */}
            {message.toolsUsed && message.toolsUsed.length > 0 && (
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {message.toolsUsed.map((tool, idx) => (
                  <Chip
                    key={idx}
                    icon={<ToolIcon fontSize="small" />}
                    label={tool.replace(/_/g, ' ')}
                    size="small"
                    sx={{
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      color: '#ffffff',
                      fontWeight: 500,
                    }}
                  />
                ))}
              </Box>
            )}

            {/* Timestamp */}
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 1,
                opacity: 0.7,
                textAlign: message.role === 'user' ? 'right' : 'left',
              }}
            >
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </MessageBubble>
        </Box>
      </Box>
    );
  };

  /**
   * Render system status sidebar
   */
  const renderSidebar = () => {
    if (!systemStatus) {
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <CircularProgress size={40} />
          <Typography variant="body2" sx={{ mt: 2 }}>
            Loading system status...
          </Typography>
        </Box>
      );
    }

    const { services, gpu, metrics } = systemStatus;

    return (
      <Box sx={{ p: 2, overflowY: 'auto', height: '100%' }}>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            System Status
          </Typography>
          <IconButton onClick={fetchSystemStatus} size="small" sx={{ color: '#ffffff' }}>
            <RefreshIcon />
          </IconButton>
        </Box>

        {/* System Metrics */}
        {metrics && (
          <StatusCard>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <MetricsIcon fontSize="small" />
                System Metrics
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Typography variant="caption">CPU Usage</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.cpuUsage || 0}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">{(metrics.cpuUsage || 0).toFixed(1)}%</Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="caption">Memory Usage</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.memoryUsage || 0}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">{(metrics.memoryUsage || 0).toFixed(1)}%</Typography>
                </Box>
              </Box>

              <Box>
                <Typography variant="caption">Disk Usage</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.diskUsage || 0}
                    sx={{ flex: 1, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">{(metrics.diskUsage || 0).toFixed(1)}%</Typography>
                </Box>
              </Box>
            </CardContent>
          </StatusCard>
        )}

        {/* GPU Status */}
        {gpu && gpu.available && gpu.devices && (
          <StatusCard>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <StorageIcon fontSize="small" />
                GPU Status
              </Typography>

              {gpu.devices.map((device, idx) => (
                <Box key={idx} sx={{ mb: 2 }}>
                  <Typography variant="caption">{device.name}</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={device.utilization || 0}
                      sx={{ flex: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption">{device.utilization}%</Typography>
                  </Box>
                  <Typography variant="caption" sx={{ opacity: 0.7, fontSize: '0.7rem' }}>
                    {device.memoryUsed} / {device.memoryTotal}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </StatusCard>
        )}

        {/* Service Status */}
        {services && services.length > 0 && (
          <StatusCard>
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <MemoryIcon fontSize="small" />
                Services ({services.length})
              </Typography>

              <List dense>
                {services.slice(0, 8).map((service, idx) => (
                  <ListItem key={idx} disablePadding sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1 }}>
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          bgcolor: service.status === 'running' ? '#4ade80' : '#ef4444',
                          flexShrink: 0,
                        }}
                      />
                      <Typography variant="caption" sx={{ flex: 1, fontSize: '0.75rem' }}>
                        {service.name}
                      </Typography>
                      <Chip
                        label={service.health || 'N/A'}
                        size="small"
                        sx={{
                          fontSize: '0.65rem',
                          height: 20,
                          bgcolor: service.health === 'healthy' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        }}
                      />
                    </Box>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </StatusCard>
        )}
      </Box>
    );
  };

  return (
    <ChatContainer>
      {/* Main Chat Area */}
      <ChatMain>
        {/* Header */}
        <AppBar
          position="static"
          elevation={0}
          sx={{
            background: 'linear-gradient(90deg, #8a2be2 0%, #9d4edd 100%)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <Toolbar>
            <Avatar sx={{ bgcolor: '#ffffff', color: '#8a2be2', mr: 2 }}>
              <BotIcon />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Navigator Geeses
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                Ops-Center AI Assistant
              </Typography>
            </Box>
            <IconButton
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              sx={{ color: '#ffffff' }}
            >
              <Badge badgeContent={systemStatus ? systemStatus.services?.length : 0} color="error">
                <MetricsIcon />
              </Badge>
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Messages */}
        <MessagesContainer>
          {messages.map(renderMessage)}
          {isLoading && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Avatar sx={{ bgcolor: '#3b82f6', width: 32, height: 32 }}>
                <BotIcon fontSize="small" />
              </Avatar>
              <Paper
                sx={{
                  p: 2,
                  background: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                }}
              >
                <CircularProgress size={20} />
                <Typography variant="body2" sx={{ ml: 2, display: 'inline', color: '#ffffff' }}>
                  Geeses is processing...
                </Typography>
              </Paper>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </MessagesContainer>

        {/* Input */}
        <InputContainer>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              variant="outlined"
              placeholder="Ask Geeses about services, users, billing, or logs..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  color: '#ffffff',
                  background: 'rgba(255, 255, 255, 0.05)',
                  '& fieldset': {
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'rgba(138, 43, 226, 0.5)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#8a2be2',
                  },
                },
              }}
            />
            <IconButton
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              sx={{
                bgcolor: '#8a2be2',
                color: '#ffffff',
                '&:hover': {
                  bgcolor: '#9d4edd',
                },
                '&.Mui-disabled': {
                  bgcolor: 'rgba(138, 43, 226, 0.3)',
                },
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </InputContainer>
      </ChatMain>

      {/* Sidebar */}
      <SidebarContainer
        anchor="right"
        open={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        variant="persistent"
      >
        {renderSidebar()}
      </SidebarContainer>
    </ChatContainer>
  );
};

export default Geeses;
