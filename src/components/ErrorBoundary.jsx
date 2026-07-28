import React from 'react';
import { Box, Typography, Button, Collapse } from '@mui/material';
import { ErrorOutline as ErrorIcon, Refresh as RefreshIcon, ExpandMore as ExpandIcon } from '@mui/icons-material';

/**
 * App-wide error boundary. On-brand, composed fallback (never a raw white crash),
 * with the real error available in a collapsible "technical details" panel so an
 * admin (or we) can see what actually broke. Also stashes the error on
 * window.__uc_lastError for diagnostics.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null, showDetails: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    try {
      window.__uc_lastError = {
        message: String(error && error.message),
        stack: String(error && error.stack || '').slice(0, 1200),
        componentStack: String(errorInfo && errorInfo.componentStack || '').slice(0, 1200),
      };
    } catch (e) {}
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => this.setState({ hasError: false, error: null, errorInfo: null, showDetails: false });

  render() {
    if (this.state.hasError) {
      const msg = (this.state.error && this.state.error.message) || '';
      const stack = (this.state.error && this.state.error.stack) || '';
      const compStack = (this.state.errorInfo && this.state.errorInfo.componentStack) || '';
      return (
        <Box sx={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
          <Box
            sx={{
              maxWidth: 560, width: '100%', textAlign: 'center',
              p: { xs: 3, sm: 5 }, borderRadius: '16px',
              border: '1px solid rgba(160,170,210,0.12)',
              background: 'rgba(18,21,33,0.72)',
              backdropFilter: 'blur(14px)',
              boxShadow: '0 24px 64px -28px rgba(0,0,0,0.8)',
            }}
          >
            <Box sx={{ width: 64, height: 64, borderRadius: '50%', mx: 'auto', mb: 2.5,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(248,113,113,0.10)', border: '1px solid rgba(248,113,113,0.28)' }}>
              <ErrorIcon sx={{ fontSize: 32, color: '#f87171' }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, fontFamily: '"Space Grotesk","Inter",sans-serif' }}>
              This screen hit a snag
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
              {this.props.fallbackMessage || 'Something on this page failed to render. The rest of the console is fine — try again, or reload.'}
            </Typography>
            {msg ? (
              <Typography variant="caption" sx={{ display: 'block', color: '#fca5a5', mb: 2.5, fontFamily: 'monospace', wordBreak: 'break-word' }}>
                {msg}
              </Typography>
            ) : <Box sx={{ mb: 2.5 }} />}

            <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button variant="contained" startIcon={<RefreshIcon />} onClick={this.handleReset}>Try Again</Button>
              <Button variant="outlined" onClick={() => window.location.reload()}>Reload Page</Button>
            </Box>

            {(stack || compStack) && (
              <Box sx={{ mt: 3 }}>
                <Button size="small" endIcon={<ExpandIcon sx={{ transform: this.state.showDetails ? 'rotate(180deg)' : 'none', transition: '0.2s' }} />}
                  onClick={() => this.setState(s => ({ showDetails: !s.showDetails }))}
                  sx={{ color: 'text.disabled', textTransform: 'none' }}>
                  Technical details
                </Button>
                <Collapse in={this.state.showDetails}>
                  <Box component="pre" sx={{ mt: 1, p: 2, textAlign: 'left', borderRadius: '10px',
                    background: 'rgba(2,6,23,0.5)', border: '1px solid rgba(160,170,210,0.1)',
                    fontSize: 11, color: 'text.secondary', overflow: 'auto', maxHeight: 260, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {compStack || stack}
                  </Box>
                </Collapse>
              </Box>
            )}
          </Box>
        </Box>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
