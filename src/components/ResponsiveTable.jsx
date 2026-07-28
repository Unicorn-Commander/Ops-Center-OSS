/**
 * ResponsiveTable Component
 *
 * A flexible table component that automatically converts to card layout
 * on mobile devices for better touch interaction and readability
 *
 * Features:
 * - Desktop: Traditional table layout
 * - Tablet: Horizontal scroll with visible scrollbar
 * - Mobile: Card-based layout
 * - Sticky headers
 * - Sortable columns
 * - Row selection
 * - Touch-friendly interactions
 *
 * Usage:
 * <ResponsiveTable
 *   data={users}
 *   columns={[
 *     { key: 'name', label: 'Name', sortable: true },
 *     { key: 'email', label: 'Email', mobile: true },
 *     { key: 'tier', label: 'Tier', mobile: true }
 *   ]}
 *   onRowClick={(row) => handleClick(row)}
 *   cardLayout={true}
 * />
 *
 * Last Updated: October 24, 2025
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Checkbox,
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

/**
 * ResponsiveTable Component
 */
export default function ResponsiveTable({
  data = [],
  columns = [],
  onRowClick = null,
  cardLayout = true,
  selectable = false,
  onSelectionChange = null,
  stickyHeader = true,
  sortable = true,
  emptyMessage = 'No data available',
  loading = false,
  className = ''
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // < 600px
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md')); // 600-900px

  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [selectedRows, setSelectedRows] = useState([]);
  const [sortedData, setSortedData] = useState(data);

  // Update sorted data when data or sort config changes
  useEffect(() => {
    if (sortConfig.key && sortable) {
      const sorted = [...data].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue === bValue) return 0;

        const comparison = aValue > bValue ? 1 : -1;
        return sortConfig.direction === 'asc' ? comparison : -comparison;
      });

      setSortedData(sorted);
    } else {
      setSortedData(data);
    }
  }, [data, sortConfig, sortable]);

  // Handle sort
  const handleSort = (key) => {
    if (!sortable) return;

    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Handle row selection
  const handleRowSelect = (row, checked) => {
    if (!selectable) return;

    const newSelection = checked
      ? [...selectedRows, row]
      : selectedRows.filter((r) => r !== row);

    setSelectedRows(newSelection);

    if (onSelectionChange) {
      onSelectionChange(newSelection);
    }
  };

  // Handle select all
  const handleSelectAll = (checked) => {
    if (!selectable) return;

    const newSelection = checked ? sortedData : [];
    setSelectedRows(newSelection);

    if (onSelectionChange) {
      onSelectionChange(newSelection);
    }
  };

  // Get mobile-visible columns
  const mobileColumns = columns.filter((col) => col.mobile !== false);

  // Render loading state
  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Loading...
        </Typography>
      </Box>
    );
  }

  // Render empty state
  if (!sortedData || sortedData.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {emptyMessage}
        </Typography>
      </Box>
    );
  }

  // Render mobile card layout
  if (isMobile && cardLayout) {
    return (
      <Box className={`table-mobile-cards ${className}`}>
        {sortedData.map((row, index) => (
          <Card
            key={index}
            className="table-card"
            sx={{
              mb: 1.5,
              cursor: onRowClick ? 'pointer' : 'default',
              '&:hover': onRowClick ? { boxShadow: 3 } : {},
              transition: 'box-shadow 0.2s'
            }}
            onClick={() => onRowClick && onRowClick(row)}
          >
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              {/* Header with primary info and selection */}
              <Box className="table-card-header" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5, pb: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                  {selectable && (
                    <Checkbox
                      checked={selectedRows.includes(row)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleRowSelect(row, e.target.checked);
                      }}
                      sx={{ p: 0.5 }}
                    />
                  )}
                  <Typography variant="subtitle1" fontWeight={600}>
                    {row[mobileColumns[0]?.key] || 'N/A'}
                  </Typography>
                </Box>
                {onRowClick && (
                  <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                )}
              </Box>

              {/* Body with remaining fields */}
              <Box className="table-card-body" sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {mobileColumns.slice(1).map((column) => (
                  <Box
                    key={column.key}
                    className="table-card-row"
                    sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <Typography
                      variant="body2"
                      className="label"
                      color="text.secondary"
                      sx={{ fontWeight: 500, flex: '0 0 40%' }}
                    >
                      {column.label}:
                    </Typography>
                    <Box className="value" sx={{ flex: 1, textAlign: 'right' }}>
                      {column.render
                        ? column.render(row[column.key], row)
                        : renderCellValue(row[column.key], column)}
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  }

  // Render tablet/desktop table layout
  return (
    <TableContainer
      component={Paper}
      className={`table-responsive ${className}`}
      sx={{
        maxWidth: '100%',
        overflowX: isTablet ? 'auto' : 'visible',
        '&::-webkit-scrollbar': {
          height: 8,
          backgroundColor: 'rgba(0, 0, 0, 0.05)'
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          borderRadius: 4
        }
      }}
    >
      <Table stickyHeader={stickyHeader}>
        <TableHead>
          <TableRow>
            {selectable && (
              <TableCell padding="checkbox" sx={{ minWidth: 60 }}>
                <Checkbox
                  checked={selectedRows.length === sortedData.length}
                  indeterminate={
                    selectedRows.length > 0 &&
                    selectedRows.length < sortedData.length
                  }
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </TableCell>
            )}
            {columns.map((column) => (
              <TableCell
                key={column.key}
                align={column.align || 'left'}
                sx={{
                  minWidth: column.minWidth || 100,
                  fontWeight: 600,
                  backgroundColor: theme.palette.mode === 'dark' ? '#1f2937' : '#f9fafb'
                }}
              >
                {column.sortable !== false && sortable ? (
                  <TableSortLabel
                    active={sortConfig.key === column.key}
                    direction={sortConfig.key === column.key ? sortConfig.direction : 'asc'}
                    onClick={() => handleSort(column.key)}
                    sx={{
                      '&.MuiTableSortLabel-root': {
                        minHeight: 44,
                        minWidth: 44
                      }
                    }}
                  >
                    {column.label}
                  </TableSortLabel>
                ) : (
                  column.label
                )}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedData.map((row, index) => (
            <TableRow
              key={index}
              hover={!!onRowClick}
              onClick={() => onRowClick && onRowClick(row)}
              sx={{
                cursor: onRowClick ? 'pointer' : 'default',
                '& > td': { minHeight: 44 }
              }}
            >
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedRows.includes(row)}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleRowSelect(row, e.target.checked);
                    }}
                  />
                </TableCell>
              )}
              {columns.map((column) => (
                <TableCell key={column.key} align={column.align || 'left'}>
                  {column.render
                    ? column.render(row[column.key], row)
                    : renderCellValue(row[column.key], column)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

/**
 * Render cell value with type-specific formatting
 */
function renderCellValue(value, column) {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return <Typography variant="body2" color="text.secondary">N/A</Typography>;
  }

  // Handle boolean
  if (typeof value === 'boolean') {
    return (
      <Chip
        label={value ? 'Yes' : 'No'}
        color={value ? 'success' : 'default'}
        size="small"
      />
    );
  }

  // Handle date
  if (value instanceof Date) {
    return <Typography variant="body2">{value.toLocaleDateString()}</Typography>;
  }

  // Handle status/tier badges
  if (column.type === 'badge') {
    const colorMap = {
      trial: 'default',
      starter: 'primary',
      professional: 'secondary',
      enterprise: 'success',
      active: 'success',
      inactive: 'default',
      suspended: 'error',
      enabled: 'success',
      disabled: 'default'
    };

    const color = colorMap[value?.toLowerCase()] || 'default';

    return (
      <Chip
        label={value}
        color={color}
        size="small"
        sx={{ fontWeight: 500 }}
      />
    );
  }

  // Handle arrays
  if (Array.isArray(value)) {
    return (
      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
        {value.map((item, i) => (
          <Chip key={i} label={item} size="small" />
        ))}
      </Box>
    );
  }

  // Handle numbers
  if (typeof value === 'number') {
    // Format large numbers with commas
    if (column.type === 'number') {
      return <Typography variant="body2">{value.toLocaleString()}</Typography>;
    }
    // Format currency
    if (column.type === 'currency') {
      return (
        <Typography variant="body2" fontWeight={500}>
          ${value.toFixed(2)}
        </Typography>
      );
    }
  }

  // Default: plain text
  return <Typography variant="body2">{String(value)}</Typography>;
}

/**
 * Example usage:
 *
 * const columns = [
 *   {
 *     key: 'name',
 *     label: 'Name',
 *     sortable: true,
 *     mobile: true
 *   },
 *   {
 *     key: 'email',
 *     label: 'Email',
 *     mobile: true
 *   },
 *   {
 *     key: 'tier',
 *     label: 'Subscription',
 *     type: 'badge',
 *     mobile: true
 *   },
 *   {
 *     key: 'status',
 *     label: 'Status',
 *     type: 'badge',
 *     mobile: false
 *   },
 *   {
 *     key: 'created',
 *     label: 'Created',
 *     sortable: true,
 *     mobile: false,
 *     render: (value) => new Date(value).toLocaleDateString()
 *   }
 * ];
 *
 * <ResponsiveTable
 *   data={users}
 *   columns={columns}
 *   onRowClick={(user) => navigate(`/users/${user.id}`)}
 *   selectable
 *   onSelectionChange={(selected) => setSelectedUsers(selected)}
 * />
 */
