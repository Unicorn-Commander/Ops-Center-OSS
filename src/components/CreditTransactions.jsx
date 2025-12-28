import React, { useState, useEffect } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, IconButton, TextField, MenuItem, Select, FormControl,
  InputLabel, Box, Typography, TablePagination, Button, InputAdornment,
  CircularProgress, Alert
} from '@mui/material';
import { Download, FilterList, Search, CalendarToday } from '@mui/icons-material';

export default function CreditTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, allocation, usage, bonus, refund
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadTransactions();
  }, [filter, searchTerm, dateFrom, dateTo, page, rowsPerPage]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        limit: rowsPerPage,
        offset: page * rowsPerPage,
        ...(filter !== 'all' && { type: filter }),
        ...(searchTerm && { search: searchTerm }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });

      const response = await fetch(`/api/v1/credits/transactions?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) throw new Error('Failed to load transactions');

      const data = await response.json();
      setTransactions(data.transactions || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error('Transaction load error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const exportToCSV = () => {
    const csvContent = [
      ['Date', 'Type', 'Service', 'Model', 'Amount', 'Balance After', 'Description'],
      ...transactions.map(tx => [
        formatDate(tx.created_at),
        tx.transaction_type,
        tx.service || '-',
        tx.model || '-',
        tx.amount,
        tx.balance_after,
        tx.description || ''
      ])
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `credit_transactions_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTypeColor = (type) => {
    const colors = {
      allocation: 'success',
      usage: 'error',
      bonus: 'info',
      refund: 'warning',
      adjustment: 'default'
    };
    return colors[type] || 'default';
  };

  const getTypeIcon = (type) => {
    const icons = {
      allocation: '+',
      usage: '-',
      bonus: '+',
      refund: '+',
      adjustment: '±'
    };
    return icons[type] || '';
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={loadTransactions} sx={{ ml: 2 }}>Retry</Button>
      </Alert>
    );
  }

  return (
    <Paper>
      {/* Filters */}
      <Box sx={{ p: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Transaction Type</InputLabel>
          <Select
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setPage(0);
            }}
            label="Transaction Type"
          >
            <MenuItem value="all">All Transactions</MenuItem>
            <MenuItem value="allocation">Allocations</MenuItem>
            <MenuItem value="usage">Usage</MenuItem>
            <MenuItem value="bonus">Bonuses</MenuItem>
            <MenuItem value="refund">Refunds</MenuItem>
            <MenuItem value="adjustment">Adjustments</MenuItem>
          </Select>
        </FormControl>

        <TextField
          size="small"
          placeholder="Search service/model..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setPage(0);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            )
          }}
          sx={{ minWidth: 250 }}
        />

        <TextField
          size="small"
          type="date"
          label="From Date"
          value={dateFrom}
          onChange={(e) => {
            setDateFrom(e.target.value);
            setPage(0);
          }}
          InputLabelProps={{ shrink: true }}
        />

        <TextField
          size="small"
          type="date"
          label="To Date"
          value={dateTo}
          onChange={(e) => {
            setDateTo(e.target.value);
            setPage(0);
          }}
          InputLabelProps={{ shrink: true }}
        />

        <Box sx={{ flexGrow: 1 }} />

        <Button
          variant="outlined"
          startIcon={<Download />}
          onClick={exportToCSV}
          disabled={transactions.length === 0}
        >
          Export CSV
        </Button>
      </Box>

      {/* Table */}
      <TableContainer>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : transactions.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="textSecondary">
              No transactions found
            </Typography>
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date & Time</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Model</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell align="right">Balance After</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transactions.map((tx) => (
                <TableRow
                  key={tx.id}
                  hover
                  sx={{
                    '&:hover': {
                      backgroundColor: 'action.hover'
                    }
                  }}
                >
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(tx.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={tx.transaction_type}
                      color={getTypeColor(tx.transaction_type)}
                      size="small"
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {tx.service || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {tx.model || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      sx={{
                        color: tx.amount < 0 ? 'error.main' : 'success.main',
                        fontWeight: 600,
                        fontFamily: 'monospace'
                      }}
                    >
                      {tx.amount > 0 ? '+' : ''}${Math.abs(tx.amount).toFixed(4)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      ${tx.balance_after?.toFixed(2) || '0.00'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary" noWrap>
                      {tx.description || '-'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
}
