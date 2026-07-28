import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import {
  InboxIcon,
  FolderOpenIcon,
  DocumentIcon,
  UsersIcon,
  CubeIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';

const iconMap = {
  inbox: InboxIcon,
  folder: FolderOpenIcon,
  document: DocumentIcon,
  users: UsersIcon,
  models: CubeIcon,
  services: ServerIcon,
};

/**
 * EmptyState - Consistent empty data state for admin pages
 *
 * Usage:
 *   {data.length === 0 && (
 *     <EmptyState
 *       icon="inbox"
 *       title="No items found"
 *       description="Get started by creating your first item."
 *       actionLabel="Create Item"
 *       onAction={() => setOpenDialog(true)}
 *     />
 *   )}
 */
export default function EmptyState({
  icon = 'inbox',
  title = 'No data found',
  description = 'There are no items to display.',
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
}) {
  const IconComponent = iconMap[icon] || InboxIcon;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        py: 8,
        px: 4,
        minHeight: 300,
      }}
    >
      <Box
        sx={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          backgroundColor: 'action.hover',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3,
        }}
      >
        <IconComponent
          style={{
            width: 40,
            height: 40,
            color: 'var(--mui-palette-text-secondary, #666)'
          }}
        />
      </Box>

      <Typography
        variant="h6"
        color="text.primary"
        gutterBottom
        sx={{ fontWeight: 600 }}
      >
        {title}
      </Typography>

      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 3, maxWidth: 400 }}
      >
        {description}
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        {actionLabel && onAction && (
          <Button
            variant="contained"
            color="primary"
            onClick={onAction}
            sx={{
              px: 3,
              py: 1,
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            {actionLabel}
          </Button>
        )}

        {secondaryActionLabel && onSecondaryAction && (
          <Button
            variant="outlined"
            color="primary"
            onClick={onSecondaryAction}
            sx={{
              px: 3,
              py: 1,
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
            }}
          >
            {secondaryActionLabel}
          </Button>
        )}
      </Box>
    </Box>
  );
}
