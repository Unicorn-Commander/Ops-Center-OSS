import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Box,
  IconButton,
  InputAdornment,
  OutlinedInput,
  Chip,
} from '@mui/material';
import { Eye, EyeOff, RefreshCw, Shield, AlertTriangle } from 'lucide-react';
import PasswordStrengthIndicator from './PasswordStrengthIndicator';

const CreateUserModal = ({
  open,
  onClose,
  newUser,
  setNewUser,
  validationErrors,
  availableGroups,
  showPassword,
  setShowPassword,
  showConfirmPassword,
  setShowConfirmPassword,
  passwordStrength,
  onGeneratePassword,
  onCreate,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>Create New User</DialogTitle>
      <DialogContent>
        {validationErrors.general && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {validationErrors.general}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Username"
          value={newUser.username}
          onChange={(e) => setNewUser({ ...newUser, username: e.target.value.toLowerCase() })}
          error={!!validationErrors.username}
          helperText={validationErrors.username || 'Lowercase alphanumeric with hyphens/underscores'}
          sx={{ mb: 2, mt: 1 }}
        />

        <TextField
          fullWidth
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={newUser.password}
          onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
          error={!!validationErrors.password}
          helperText={validationErrors.password}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 1 }}
        />

        <PasswordStrengthIndicator strength={passwordStrength} />

        <Button
          variant="outlined"
          size="small"
          startIcon={<RefreshCw size={16} />}
          onClick={onGeneratePassword}
          sx={{ mb: 2 }}
        >
          Generate Random Password
        </Button>

        <TextField
          fullWidth
          label="Confirm Password"
          type={showConfirmPassword ? 'text' : 'password'}
          value={newUser.confirmPassword}
          onChange={(e) => setNewUser({ ...newUser, confirmPassword: e.target.value })}
          error={!!validationErrors.confirmPassword}
          helperText={validationErrors.confirmPassword}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end">
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Shell</InputLabel>
          <Select
            value={newUser.shell}
            onChange={(e) => setNewUser({ ...newUser, shell: e.target.value })}
            label="Shell"
          >
            <MenuItem value="/bin/bash">/bin/bash</MenuItem>
            <MenuItem value="/bin/zsh">/bin/zsh</MenuItem>
            <MenuItem value="/bin/sh">/bin/sh</MenuItem>
            <MenuItem value="/bin/dash">/bin/dash</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Groups</InputLabel>
          <Select
            multiple
            value={newUser.groups}
            onChange={(e) => setNewUser({ ...newUser, groups: e.target.value })}
            input={<OutlinedInput label="Groups" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {availableGroups.map((group) => (
              <MenuItem key={group} value={group}>
                {group}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Checkbox
              checked={newUser.grantSudo}
              onChange={(e) => setNewUser({ ...newUser, grantSudo: e.target.checked })}
            />
          }
          label={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Shield size={16} style={{ marginRight: 8 }} />
              Grant sudo access
            </Box>
          }
        />

        {newUser.grantSudo && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AlertTriangle size={16} style={{ marginRight: 8 }} />
              Granting sudo access gives this user administrative privileges
            </Box>
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={onCreate}>
          Create User
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateUserModal;
