import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  IconButton,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  InputAdornment,
  Badge,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Security as SecurityIcon,
  Payment as PaymentIcon,
  Psychology as PsychologyIcon,
  Email as EmailIcon,
  Storage as StorageIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';
import SystemSettingCard from '../components/SystemSettingCard';
import EditSettingModal from '../components/EditSettingModal';
import PageHeader from '../components/admin/PageHeader';

const SystemSettings = () => {
  const navigate = useNavigate();
  const { currentTheme } = useTheme();

  // State for settings list
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedSetting, setSelectedSetting] = useState(null);

  // Filter state
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Notification state
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Category definitions
  const categories = [
    { id: 'all', label: 'All Settings', icon: null, count: 0 },
    { id: 'security', label: 'Security', icon: SecurityIcon, count: 0 },
    { id: 'billing', label: 'Billing', icon: PaymentIcon, count: 0 },
    { id: 'llm', label: 'LLM', icon: PsychologyIcon, count: 0 },
    { id: 'email', label: 'Email', icon: EmailIcon, count: 0 },
    { id: 'storage', label: 'Storage', icon: StorageIcon, count: 0 },
  ];

  // Fetch settings from backend
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/system-settings', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch system settings');
      }

      const data = await response.json();
      setSettings(data.settings || []);
    } catch (err) {
      console.error('Error fetching settings:', err);
      setError(err.message);
      showSnackbar('Failed to load settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSetting = () => {
    setSelectedSetting(null);
    setEditModalOpen(true);
  };

  const handleEditSetting = (setting) => {
    setSelectedSetting(setting);
    setEditModalOpen(true);
  };

  const handleDeleteSetting = async (settingKey) => {
    if (!window.confirm(`Are you sure you want to delete "${settingKey}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/system-settings/${settingKey}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to delete setting');
      }

      showSnackbar('Setting deleted successfully', 'success');
      fetchSettings();
    } catch (err) {
      console.error('Error deleting setting:', err);
      showSnackbar('Failed to delete setting', 'error');
    }
  };

  const handleTestConnection = async (settingKey, category) => {
    try {
      const response = await fetch(`/api/v1/admin/system-settings/${settingKey}/test`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Connection test failed');
      }

      const data = await response.json();
      showSnackbar(data.message || 'Connection test successful', 'success');
    } catch (err) {
      console.error('Error testing connection:', err);
      showSnackbar('Connection test failed', 'error');
    }
  };

  const handleSaveSetting = async (settingData) => {
    try {
      const isEdit = selectedSetting !== null;
      const method = isEdit ? 'PUT' : 'POST';
      const url = isEdit
        ? `/api/v1/admin/system-settings/${selectedSetting.key}`
        : '/api/v1/admin/system-settings';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(settingData),
      });

      if (!response.ok) {
        throw new Error('Failed to save setting');
      }

      showSnackbar(`Setting ${isEdit ? 'updated' : 'created'} successfully`, 'success');
      setEditModalOpen(false);
      fetchSettings();
    } catch (err) {
      console.error('Error saving setting:', err);
      throw err; // Re-throw to let modal handle it
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Filter settings by category and search
  const filteredSettings = settings.filter((setting) => {
    const matchesCategory = activeCategory === 'all' || setting.category === activeCategory;
    const matchesSearch =
      searchQuery === '' ||
      setting.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      setting.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // Calculate category counts
  const categoryCounts = categories.map((cat) => {
    if (cat.id === 'all') {
      return { ...cat, count: settings.length };
    }
    return { ...cat, count: settings.filter((s) => s.category === cat.id).length };
  });

  // Theme-based styling
  const isDark = currentTheme === 'dark' || currentTheme === 'unicorn';
  const bgColor = currentTheme === 'unicorn'
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : currentTheme === 'light'
    ? '#ffffff'
    : '#1e293b';

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <PageHeader
        title="System Settings"
        subtitle="Manage environment variables and system configuration through the GUI"
      />

      {/* Alert for errors */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <TextField
          placeholder="Search settings..."
          variant="outlined"
          size="small"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ width: 300 }}
        />
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchSettings}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddSetting}
          >
            Add Setting
          </Button>
        </Box>
      </Box>

      {/* Category Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeCategory}
          onChange={(e, newValue) => setActiveCategory(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {categoryCounts.map((cat) => (
            <Tab
              key={cat.id}
              value={cat.id}
              label={
                <Badge badgeContent={cat.count} color="primary">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {cat.icon && <cat.icon sx={{ fontSize: 20 }} />}
                    <span>{cat.label}</span>
                  </Box>
                </Badge>
              }
            />
          ))}
        </Tabs>
      </Paper>

      {/* Settings Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : filteredSettings.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            No settings found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchQuery
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by adding your first system setting'}
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddSetting}>
            Add First Setting
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>Key</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Value</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Category</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Last Updated</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSettings.map((setting) => (
                <SystemSettingCard
                  key={setting.key}
                  setting={setting}
                  onEdit={handleEditSetting}
                  onDelete={handleDeleteSetting}
                  onTest={handleTestConnection}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit/Create Modal */}
      <EditSettingModal
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        setting={selectedSetting}
        onSave={handleSaveSetting}
      />

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SystemSettings;
