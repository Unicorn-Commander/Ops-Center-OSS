import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  AlertTitle,
  CircularProgress,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  Collapse,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

const ImportCSVModal = ({ open, onClose, onImportComplete }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState(null);
  const [parsedData, setParsedData] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [importResults, setImportResults] = useState(null);
  const [importing, setImporting] = useState(false);
  const [showErrors, setShowErrors] = useState(false);

  const steps = ['Upload CSV', 'Review Data', 'Import Results'];

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      parseCSV(selectedFile);
    } else {
      alert('Please select a valid CSV file');
    }
  };

  const parseCSV = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        setValidationErrors(['CSV file is empty']);
        return;
      }

      // Parse header
      const header = lines[0].split(',').map(h => h.trim());

      // Expected columns
      const requiredColumns = ['email', 'username'];
      const optionalColumns = ['firstName', 'lastName', 'password', 'tier', 'roles', 'organization'];

      // Validate header
      const missingColumns = requiredColumns.filter(col => !header.includes(col));
      if (missingColumns.length > 0) {
        setValidationErrors([`Missing required columns: ${missingColumns.join(', ')}`]);
        return;
      }

      // Parse data rows
      const data = [];
      const errors = [];

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const row = {};

        header.forEach((col, index) => {
          row[col] = values[index] || '';
        });

        // Validate row
        const rowErrors = [];
        if (!row.email || !row.email.includes('@')) {
          rowErrors.push('Invalid email');
        }
        if (!row.username || row.username.length < 3) {
          rowErrors.push('Invalid username (min 3 characters)');
        }
        if (row.password && row.password.length < 8) {
          rowErrors.push('Password too short (min 8 characters)');
        }

        if (rowErrors.length > 0) {
          errors.push({
            row: i,
            email: row.email || 'unknown',
            errors: rowErrors
          });
        }

        data.push({...row, _rowNumber: i + 1, _valid: rowErrors.length === 0 });
      }

      setParsedData(data);
      setValidationErrors(errors);
      setActiveStep(1);
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    setImporting(true);

    try {
      // Filter out invalid rows
      const validUsers = parsedData.filter(row => row._valid).map(row => {
        const user = {...row};
        delete user._rowNumber;
        delete user._valid;
        return user;
      });

      const response = await fetch('/api/v1/admin/users/bulk/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ users: validUsers }),
      });

      if (!response.ok) {
        throw new Error('Import failed');
      }

      const results = await response.json();
      setImportResults(results);
      setActiveStep(2);

      if (results.created > 0) {
        onImportComplete(results);
      }
    } catch (error) {
      console.error('Import error:', error);
      alert('Import failed: ' + error.message);
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setFile(null);
    setParsedData([]);
    setValidationErrors([]);
    setImportResults(null);
    setImporting(false);
    onClose();
  };

  const downloadTemplate = () => {
    const template = 'email,username,firstName,lastName,password,tier,roles,organization\n' +
                    'user@example.com,johndoe,John,Doe,TempPass123,trial,,\n' +
                    'admin@example.com,janeadmin,Jane,Admin,AdminPass456,professional,brigade-platform-admin,';

    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'user_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const validRowCount = parsedData.filter(row => row._valid).length;
  const invalidRowCount = parsedData.length - validRowCount;

  return (
    <Dialog
      open={open}
      onClose={importing ? undefined : handleClose}
      maxWidth="lg"
      fullWidth
      disableEscapeKeyDown={importing}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Import Users from CSV</Typography>
          <Button
            size="small"
            startIcon={<DownloadIcon />}
            onClick={downloadTemplate}
          >
            Download Template
          </Button>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Step 1: Upload CSV */}
        {activeStep === 0 && (
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              <AlertTitle>CSV Format</AlertTitle>
              Required columns: <strong>email, username</strong><br/>
              Optional columns: firstName, lastName, password, tier, roles, organization<br/>
              Maximum 1000 users per import.
            </Alert>

            <Paper
              sx={{
                p: 4,
                textAlign: 'center',
                border: '2px dashed',
                borderColor: 'primary.main',
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
              component="label"
            >
              <input
                type="file"
                accept=".csv"
                hidden
                onChange={handleFileChange}
              />
              <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Click to upload CSV file
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or drag and drop your file here
              </Typography>
            </Paper>
          </Box>
        )}

        {/* Step 2: Review Data */}
        {activeStep === 1 && (
          <Box>
            <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
              <Chip
                icon={<CheckIcon />}
                label={`${validRowCount} valid users`}
                color="success"
              />
              {invalidRowCount > 0 && (
                <Chip
                  icon={<ErrorIcon />}
                  label={`${invalidRowCount} invalid rows`}
                  color="error"
                />
              )}
            </Box>

            {validationErrors.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <AlertTitle>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>Validation Errors ({validationErrors.length})</span>
                    <IconButton
                      size="small"
                      onClick={() => setShowErrors(!showErrors)}
                    >
                      {showErrors ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Box>
                </AlertTitle>
                <Collapse in={showErrors}>
                  <List dense>
                    {validationErrors.map((error, idx) => (
                      <ListItem key={idx}>
                        <ListItemText
                          primary={`Row ${error.row}: ${error.email}`}
                          secondary={error.errors.join(', ')}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Collapse>
              </Alert>
            )}

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Status</TableCell>
                    <TableCell>Row</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>First Name</TableCell>
                    <TableCell>Last Name</TableCell>
                    <TableCell>Tier</TableCell>
                    <TableCell>Roles</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parsedData.slice(0, 50).map((row, idx) => (
                    <TableRow
                      key={idx}
                      sx={{ bgcolor: row._valid ? 'inherit' : 'error.light' }}
                    >
                      <TableCell>
                        {row._valid ? (
                          <CheckIcon color="success" fontSize="small" />
                        ) : (
                          <ErrorIcon color="error" fontSize="small" />
                        )}
                      </TableCell>
                      <TableCell>{row._rowNumber}</TableCell>
                      <TableCell>{row.email}</TableCell>
                      <TableCell>{row.username}</TableCell>
                      <TableCell>{row.firstName}</TableCell>
                      <TableCell>{row.lastName}</TableCell>
                      <TableCell>{row.tier || 'trial'}</TableCell>
                      <TableCell>{row.roles}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {parsedData.length > 50 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Showing first 50 of {parsedData.length} rows
              </Typography>
            )}
          </Box>
        )}

        {/* Step 3: Import Results */}
        {activeStep === 2 && importResults && (
          <Box>
            {importing ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CircularProgress size={64} sx={{ mb: 2 }} />
                <Typography variant="h6">Importing users...</Typography>
                <LinearProgress sx={{ mt: 2 }} />
              </Box>
            ) : (
              <>
                <Alert severity={importResults.failed === 0 ? 'success' : 'warning'} sx={{ mb: 2 }}>
                  <AlertTitle>Import Complete</AlertTitle>
                  {importResults.created} users created successfully
                  {importResults.failed > 0 && `, ${importResults.failed} failed`}
                </Alert>

                {importResults.errors && importResults.errors.length > 0 && (
                  <>
                    <Typography variant="subtitle1" gutterBottom>
                      Errors:
                    </Typography>
                    <List>
                      {importResults.errors.map((error, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`Row ${error.row}: ${error.email}`}
                            secondary={error.error}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}

                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Summary:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                    <Chip label={`Total: ${importResults.total}`} />
                    <Chip label={`Created: ${importResults.created}`} color="success" />
                    <Chip label={`Failed: ${importResults.failed}`} color="error" />
                  </Box>
                </Box>
              </>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button
          onClick={handleClose}
          disabled={importing}
        >
          {activeStep === 2 ? 'Close' : 'Cancel'}
        </Button>
        {activeStep === 1 && (
          <Button
            variant="contained"
            onClick={handleImport}
            disabled={validRowCount === 0 || importing}
            startIcon={importing ? <CircularProgress size={20} /> : <UploadIcon />}
          >
            {importing ? 'Importing...' : `Import ${validRowCount} Users`}
          </Button>
        )}
        {activeStep === 0 && file && (
          <Button
            variant="contained"
            onClick={() => setActiveStep(1)}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ImportCSVModal;
