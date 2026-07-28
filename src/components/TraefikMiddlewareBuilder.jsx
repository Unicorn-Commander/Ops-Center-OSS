import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider
} from '@mui/material';
import {
  PlusIcon,
  TrashIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const MIDDLEWARE_TYPES = [
  {
    type: 'BasicAuth',
    label: 'Basic Authentication',
    description: 'Username and password authentication',
    fields: [
      { name: 'users', label: 'Users', type: 'text', placeholder: 'user:password (comma-separated)' }
    ]
  },
  {
    type: 'Compress',
    label: 'Compression',
    description: 'Gzip compression for responses',
    fields: []
  },
  {
    type: 'RateLimit',
    label: 'Rate Limiting',
    description: 'Limit requests per second',
    fields: [
      { name: 'average', label: 'Average RPS', type: 'number', placeholder: '100' },
      { name: 'burst', label: 'Burst Limit', type: 'number', placeholder: '200' }
    ]
  },
  {
    type: 'Headers',
    label: 'Custom Headers',
    description: 'Add or remove HTTP headers',
    fields: [
      { name: 'customRequestHeaders', label: 'Request Headers', type: 'json', placeholder: '{"X-Custom": "value"}' },
      { name: 'customResponseHeaders', label: 'Response Headers', type: 'json', placeholder: '{"X-Custom": "value"}' }
    ]
  },
  {
    type: 'RedirectScheme',
    label: 'HTTPS Redirect',
    description: 'Redirect HTTP to HTTPS',
    fields: [
      { name: 'scheme', label: 'Scheme', type: 'select', options: ['https'], default: 'https' },
      { name: 'permanent', label: 'Permanent', type: 'checkbox', default: true }
    ]
  },
  {
    type: 'StripPrefix',
    label: 'Strip Prefix',
    description: 'Remove path prefix before forwarding',
    fields: [
      { name: 'prefixes', label: 'Prefixes', type: 'text', placeholder: '/api,/v1 (comma-separated)' }
    ]
  }
];

const TraefikMiddlewareBuilder = ({ middleware, onChange }) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedType, setSelectedType] = useState('');
  const [formData, setFormData] = useState({});
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedInfo, setSelectedInfo] = useState(null);

  const handleAdd = () => {
    const middlewareType = MIDDLEWARE_TYPES.find((m) => m.type === selectedType);
    if (!middlewareType) return;

    const newMiddleware = {
      type: selectedType,
      config: formData
    };

    onChange([...middleware, newMiddleware]);
    setDialogOpen(false);
    setSelectedType('');
    setFormData({});
  };

  const handleRemove = (index) => {
    const updated = middleware.filter((_, i) => i !== index);
    onChange(updated);
  };

  const handleMoveUp = (index) => {
    if (index === 0) return;
    const updated = [...middleware];
    [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
    onChange(updated);
  };

  const handleMoveDown = (index) => {
    if (index === middleware.length - 1) return;
    const updated = [...middleware];
    [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
    onChange(updated);
  };

  const handleTypeChange = (type) => {
    setSelectedType(type);
    const middlewareType = MIDDLEWARE_TYPES.find((m) => m.type === type);

    // Set default values
    const defaults = {};
    middlewareType?.fields?.forEach((field) => {
      if (field.default !== undefined) {
        defaults[field.name] = field.default;
      }
    });
    setFormData(defaults);
  };

  const renderFormField = (field) => {
    switch (field.type) {
      case 'text':
        return (
          <TextField
            key={field.name}
            label={field.label}
            value={formData[field.name] || ''}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            fullWidth
            placeholder={field.placeholder}
          />
        );

      case 'number':
        return (
          <TextField
            key={field.name}
            label={field.label}
            type="number"
            value={formData[field.name] || ''}
            onChange={(e) => setFormData({ ...formData, [field.name]: parseInt(e.target.value) })}
            fullWidth
            placeholder={field.placeholder}
          />
        );

      case 'json':
        return (
          <TextField
            key={field.name}
            label={field.label}
            value={formData[field.name] || ''}
            onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
            fullWidth
            multiline
            rows={3}
            placeholder={field.placeholder}
          />
        );

      case 'select':
        return (
          <FormControl key={field.name} fullWidth>
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={formData[field.name] || field.default || ''}
              onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
              label={field.label}
            >
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      {/* Middleware List */}
      {middleware.length > 0 ? (
        <Paper variant="outlined" sx={{ mb: 2 }}>
          <List>
            {middleware.map((item, index) => {
              const middlewareType = MIDDLEWARE_TYPES.find((m) => m.type === item.type);
              return (
                <React.Fragment key={index}>
                  <ListItem
                    secondaryAction={
                      <Box display="flex" gap={0.5}>
                        <IconButton
                          size="small"
                          onClick={() => handleMoveUp(index)}
                          disabled={index === 0}
                        >
                          <ArrowUpIcon style={{ width: 16, height: 16 }} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleMoveDown(index)}
                          disabled={index === middleware.length - 1}
                        >
                          <ArrowDownIcon style={{ width: 16, height: 16 }} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedInfo(middlewareType);
                            setInfoDialogOpen(true);
                          }}
                        >
                          <InformationCircleIcon style={{ width: 16, height: 16 }} />
                        </IconButton>
                        <IconButton size="small" onClick={() => handleRemove(index)} color="error">
                          <TrashIcon style={{ width: 16, height: 16 }} />
                        </IconButton>
                      </Box>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip label={index + 1} size="small" />
                          <Typography variant="body2">{middlewareType?.label || item.type}</Typography>
                        </Box>
                      }
                      secondary={middlewareType?.description}
                    />
                  </ListItem>
                  {index < middleware.length - 1 && <Divider />}
                </React.Fragment>
              );
            })}
          </List>
        </Paper>
      ) : (
        <Paper variant="outlined" sx={{ p: 4, mb: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No middleware configured
          </Typography>
        </Paper>
      )}

      {/* Add Button */}
      <Button
        variant="outlined"
        startIcon={<PlusIcon style={{ width: 20, height: 20 }} />}
        onClick={() => setDialogOpen(true)}
        fullWidth
      >
        Add Middleware
      </Button>

      {/* Add Middleware Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Middleware</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <FormControl fullWidth>
              <InputLabel>Middleware Type</InputLabel>
              <Select
                value={selectedType}
                onChange={(e) => handleTypeChange(e.target.value)}
                label="Middleware Type"
              >
                {MIDDLEWARE_TYPES.map((type) => (
                  <MenuItem key={type.type} value={type.type}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedType && (
              <>
                <Typography variant="body2" color="text.secondary">
                  {MIDDLEWARE_TYPES.find((m) => m.type === selectedType)?.description}
                </Typography>

                {MIDDLEWARE_TYPES.find((m) => m.type === selectedType)?.fields?.map((field) =>
                  renderFormField(field)
                )}
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!selectedType}>
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Info Dialog */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedInfo?.label}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" paragraph>
            {selectedInfo?.description}
          </Typography>
          {selectedInfo?.fields && selectedInfo.fields.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Configuration Options:
              </Typography>
              <List dense>
                {selectedInfo.fields.map((field) => (
                  <ListItem key={field.name}>
                    <ListItemText
                      primary={field.label}
                      secondary={field.placeholder || `Type: ${field.type}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TraefikMiddlewareBuilder;
