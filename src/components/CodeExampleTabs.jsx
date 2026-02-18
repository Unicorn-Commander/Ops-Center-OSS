import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  useTheme,
} from '@mui/material';
import { ContentCopy as CopyIcon, Check as CheckIcon } from '@mui/icons-material';

/**
 * CodeExampleTabs
 *
 * Multi-language code examples for API endpoints
 * Supports cURL, JavaScript (Axios), Python (requests)
 */
const CodeExampleTabs = ({ endpoint, baseUrl = 'https://unicorncommander.ai' }) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  if (!endpoint) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          Select an endpoint to view code examples
        </Typography>
      </Box>
    );
  }

  const handleCopy = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setSnackbarOpen(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const generateCurlExample = () => {
    const { method, path } = endpoint;
    let curlCommand = `curl -X ${method} "${baseUrl}${path}"`;

    // Add headers
    curlCommand += ` \\\n  -H "Authorization: Bearer YOUR_TOKEN"`;
    curlCommand += ` \\\n  -H "Content-Type: application/json"`;

    // Add request body for POST/PUT/PATCH
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      curlCommand += ` \\\n  -d '{\n    "key": "value"\n  }'`;
    }

    return curlCommand;
  };

  const generateJavaScriptExample = () => {
    const { method, path } = endpoint;
    const methodLower = method.toLowerCase();

    let code = `// Using Axios\nimport axios from 'axios';\n\n`;
    code += `const response = await axios.${methodLower}(\n`;
    code += `  '${baseUrl}${path}',\n`;

    if (['post', 'put', 'patch'].includes(methodLower)) {
      code += `  {\n    // Request body\n    key: 'value'\n  },\n`;
    }

    code += `  {\n    headers: {\n`;
    code += `      'Authorization': 'Bearer YOUR_TOKEN',\n`;
    code += `      'Content-Type': 'application/json'\n`;
    code += `    }\n  }\n`;
    code += `);\n\n`;
    code += `console.log(response.data);`;

    return code;
  };

  const generatePythonExample = () => {
    const { method, path } = endpoint;
    const methodLower = method.toLowerCase();

    let code = `# Using requests library\nimport requests\n\n`;
    code += `url = '${baseUrl}${path}'\n`;
    code += `headers = {\n`;
    code += `    'Authorization': 'Bearer YOUR_TOKEN',\n`;
    code += `    'Content-Type': 'application/json'\n`;
    code += `}\n\n`;

    if (['post', 'put', 'patch'].includes(methodLower)) {
      code += `data = {\n`;
      code += `    'key': 'value'\n`;
      code += `}\n\n`;
      code += `response = requests.${methodLower}(url, json=data, headers=headers)\n`;
    } else {
      code += `response = requests.${methodLower}(url, headers=headers)\n`;
    }

    code += `\n# Check response\n`;
    code += `if response.status_code == 200:\n`;
    code += `    print(response.json())\n`;
    code += `else:\n`;
    code += `    print(f'Error: {response.status_code}')`;

    return code;
  };

  const codeExamples = [
    {
      label: 'cURL',
      language: 'bash',
      code: generateCurlExample(),
    },
    {
      label: 'JavaScript',
      language: 'javascript',
      code: generateJavaScriptExample(),
    },
    {
      label: 'Python',
      language: 'python',
      code: generatePythonExample(),
    },
  ];

  const currentExample = codeExamples[activeTab];

  return (
    <Box>
      {/* Language Tabs */}
      <Box
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: 'rgba(0, 0, 0, 0.02)',
        }}
      >
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{
            minHeight: 48,
            '& .MuiTab-root': {
              minHeight: 48,
              textTransform: 'none',
              fontWeight: 500,
              fontSize: '14px',
            },
          }}
        >
          {codeExamples.map((example, index) => (
            <Tab key={index} label={example.label} />
          ))}
        </Tabs>
      </Box>

      {/* Code Block */}
      <Box
        sx={{
          position: 'relative',
          backgroundColor: '#1f2937',
          color: '#f9fafb',
          borderRadius: '0 0 8px 8px',
          overflow: 'hidden',
        }}
      >
        {/* Copy Button */}
        <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
          <IconButton
            onClick={() => handleCopy(currentExample.code)}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              color: 'white',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              },
              zIndex: 1,
            }}
            size="small"
          >
            {copied ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
          </IconButton>
        </Tooltip>

        {/* Code Content */}
        <Box
          component="pre"
          sx={{
            m: 0,
            p: 3,
            pt: 5,
            fontSize: '13px',
            lineHeight: 1.6,
            overflow: 'auto',
            fontFamily: '"Fira Code", "Courier New", monospace',
            maxHeight: '400px',

            // Syntax highlighting (basic)
            '& .comment': { color: '#6b7280' },
            '& .keyword': { color: '#a78bfa' },
            '& .string': { color: '#34d399' },
            '& .number': { color: '#fbbf24' },

            // Mobile responsive
            '@media (max-width: 768px)': {
              fontSize: '12px',
              p: 2,
              pt: 4,
            },
          }}
        >
          {currentExample.code}
        </Box>
      </Box>

      {/* Endpoint Info */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: 'rgba(0, 0, 0, 0.02)', borderRadius: 1 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Endpoint Information
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Method
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {endpoint.method}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Path
            </Typography>
            <Typography
              variant="body2"
              fontWeight={500}
              sx={{ fontFamily: 'monospace', fontSize: '13px' }}
            >
              {endpoint.path}
            </Typography>
          </Box>
        </Box>
        {endpoint.summary && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {endpoint.summary}
          </Typography>
        )}
      </Box>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled" sx={{ width: '100%' }}>
          Code copied to clipboard!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeExampleTabs;
