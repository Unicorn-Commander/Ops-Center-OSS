import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Tooltip,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

/**
 * Permission Matrix Component
 * Visual grid showing permissions granted by roles
 *
 * Props:
 * - roles: Array of role names assigned to user
 * - rolePermissions: Map of role -> permissions
 * - expanded: Boolean to show/hide matrix
 */
const PermissionMatrix = ({ roles = [], rolePermissions = {}, expanded = false }) => {
  const [isExpanded, setIsExpanded] = React.useState(expanded);

  // Define services and their possible actions
  const services = [
    { id: 'open-webui', name: 'Open-WebUI', description: 'Chat interface' },
    { id: 'center-deep', name: 'Center-Deep', description: 'Search engine' },
    { id: 'brigade', name: 'Unicorn Brigade', description: 'Agent platform' },
    { id: 'orator', name: 'Unicorn Orator', description: 'Text-to-Speech' },
    { id: 'amanuensis', name: 'Unicorn Amanuensis', description: 'Speech-to-Text' },
    { id: 'ops-center', name: 'Ops Center', description: 'Admin dashboard' },
  ];

  const actions = [
    { id: 'read', name: 'Read', description: 'View and access' },
    { id: 'write', name: 'Write', description: 'Create and modify' },
    { id: 'admin', name: 'Admin', description: 'Full control' },
    { id: 'execute', name: 'Execute', description: 'Run operations' },
  ];

  // Calculate effective permissions from all roles
  const calculateEffectivePermissions = () => {
    const permissions = {};

    services.forEach(service => {
      permissions[service.id] = {};
      actions.forEach(action => {
        permissions[service.id][action.id] = {
          granted: false,
          sources: [], // Which roles grant this permission
        };
      });
    });

    // Check each role's permissions
    roles.forEach(role => {
      const rolePerms = rolePermissions[role] || {};

      // Parse role permissions (format: "service:action")
      Object.keys(rolePerms).forEach(perm => {
        const [service, action] = perm.split(':');
        if (permissions[service] && permissions[service][action]) {
          permissions[service][action].granted = true;
          permissions[service][action].sources.push(role);
        }
      });
    });

    return permissions;
  };

  const effectivePermissions = calculateEffectivePermissions();

  // Get permission cell color based on sources
  const getPermissionColor = (permission) => {
    if (!permission.granted) return 'default';

    // If directly granted by a role
    if (permission.sources.length === 1) {
      return 'success'; // Green for directly granted
    }

    // If granted by multiple roles (inherited)
    return 'info'; // Blue for inherited from multiple
  };

  // Get permission cell icon
  const renderPermissionIcon = (permission) => {
    if (permission.granted) {
      return (
        <Tooltip
          title={`Granted by: ${permission.sources.join(', ')}`}
          arrow
        >
          <CheckIcon
            sx={{
              color: getPermissionColor(permission) === 'success' ? 'success.main' : 'info.main',
              fontSize: 20
            }}
          />
        </Tooltip>
      );
    }

    return (
      <CancelIcon sx={{ color: 'action.disabled', fontSize: 20 }} />
    );
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 1,
          cursor: 'pointer',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Typography variant="subtitle1" fontWeight="bold">
          Permission Matrix
        </Typography>
        <IconButton size="small">
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      <Collapse in={isExpanded}>
        <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
          <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckIcon sx={{ color: 'success.main', fontSize: 18 }} />
              <Typography variant="caption">Directly Granted</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckIcon sx={{ color: 'info.main', fontSize: 18 }} />
              <Typography variant="caption">Inherited (Multiple Roles)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CancelIcon sx={{ color: 'action.disabled', fontSize: 18 }} />
              <Typography variant="caption">Not Granted</Typography>
            </Box>
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 180 }}>
                    Service
                  </TableCell>
                  {actions.map(action => (
                    <TableCell
                      key={action.id}
                      align="center"
                      sx={{ fontWeight: 'bold' }}
                    >
                      <Tooltip title={action.description} arrow>
                        <span>{action.name}</span>
                      </Tooltip>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {services.map(service => (
                  <TableRow key={service.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {service.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {service.description}
                        </Typography>
                      </Box>
                    </TableCell>
                    {actions.map(action => (
                      <TableCell key={action.id} align="center">
                        {renderPermissionIcon(effectivePermissions[service.id][action.id])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {roles.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="body2" color="text.secondary">
                No roles assigned. Assign roles to see permissions.
              </Typography>
            </Box>
          )}
        </Paper>
      </Collapse>
    </Box>
  );
};

export default PermissionMatrix;
