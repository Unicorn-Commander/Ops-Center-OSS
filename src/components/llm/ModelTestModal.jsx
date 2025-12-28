import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  Typography,
  CircularProgress,
  Chip
} from '@mui/material';
import { CheckCircle, Error } from '@mui/icons-material';

/**
 * ModelTestModal Component
 *
 * Modal for testing a model with a sample prompt
 */
export default function ModelTestModal({ open, model, onClose, onTest }) {
  const [prompt, setPrompt] = useState('Hello, world! Please respond with a brief greeting.');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleTest = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const testResult = await onTest(model.model_id, prompt);
      setResult(testResult);
    } catch (err) {
      setError(err.message || 'Test failed');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPrompt('Hello, world! Please respond with a brief greeting.');
    setResult(null);
    setError('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Test Model: {model?.name}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="Test Prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            multiline
            rows={3}
            fullWidth
            placeholder="Enter a test prompt..."
          />

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          )}

          {error && <Alert severity="error">{error}</Alert>}

          {result && (
            <Box>
              {result.success ? (
                <Box>
                  <Alert icon={<CheckCircle />} severity="success" sx={{ mb: 2 }}>
                    Model test successful!
                  </Alert>

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={`Latency: ${result.latency_ms.toFixed(0)}ms`}
                      color="primary"
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    {result.usage && (
                      <>
                        <Chip
                          label={`Input: ${result.usage.prompt_tokens} tokens`}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={`Output: ${result.usage.completion_tokens} tokens`}
                          size="small"
                        />
                      </>
                    )}
                  </Box>

                  <Typography variant="subtitle2" gutterBottom>
                    Response:
                  </Typography>
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: 'background.paper',
                      borderRadius: 1,
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.response}
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Alert icon={<Error />} severity="error">
                  {result.error}
                </Alert>
              )}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        <Button onClick={handleTest} variant="contained" disabled={loading || !prompt}>
          {loading ? 'Testing...' : 'Run Test'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
