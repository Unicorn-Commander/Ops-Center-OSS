# Epic 1.4 Frontend - Manual Testing Checklist

**Date**: October 23, 2025
**Tester**: ___________________
**Build Version**: ___________________
**Environment**: Production / Staging / Development (circle one)

---

## Pre-Testing Setup

- [ ] Frontend built: `npm run build`
- [ ] Files deployed to public: `cp -r dist/* public/`
- [ ] Ops-Center restarted: `docker restart ops-center-direct`
- [ ] Access URL: https://your-domain.com/admin/storage
- [ ] Browser: Chrome / Firefox / Safari (circle one)
- [ ] Browser console open (F12)
- [ ] No console errors on page load

---

## Tab 1: Storage Overview

### Initial Load
- [ ] Page loads without errors
- [ ] Loading spinner appears briefly
- [ ] Data loads successfully

### Metric Cards
- [ ] **Total Storage** card displays
  - Shows number (e.g., "1.00 TB")
  - Blue server icon visible
- [ ] **Used Storage** card displays
  - Shows number (e.g., "350 GB")
  - Shows percentage (e.g., "35.0% used")
  - Yellow pie chart icon visible
- [ ] **Available Storage** card displays
  - Shows number (e.g., "650 GB")
  - Shows percentage (e.g., "65.0% free")
  - Green cloud icon visible

### Progress Bar
- [ ] Progress bar shows correct fill (matches used percentage)
- [ ] "Used:" and "Free:" labels show correct values

### Storage Breakdown
- [ ] Storage types display (AI Models, Database, Cache, etc.)
- [ ] Each type shows size in appropriate unit (GB, MB, etc.)
- [ ] Grid layout displays correctly

### Refresh Button
- [ ] Click "Refresh" button
- [ ] Button changes to "Refreshing..." with spinner
- [ ] Data reloads
- [ ] Button returns to "Refresh"

**Notes**: ___________________________________________________________________

---

## Tab 2: Volume Management

### Volume List
- [ ] All volumes display in list
- [ ] Each volume card shows:
  - [ ] Volume name
  - [ ] Volume path
  - [ ] Size (formatted correctly)
  - [ ] Type (AI Models, Database, etc.)
  - [ ] Health status (healthy/warning/error)
  - [ ] Last accessed timestamp
- [ ] Health icons show correct color:
  - [ ] Green for "healthy"
  - [ ] Yellow for "warning"
  - [ ] Red for "error"

### Empty State
- [ ] If no volumes, shows folder icon and "No volumes found" message

**Test Volume Count**: _____ volumes found

**Notes**: ___________________________________________________________________

---

## Tab 3: Backup & Recovery

### Status Cards
- [ ] **Backup Status** card shows "Enabled" or "Disabled"
  - Icon color matches status (green/red)
- [ ] **Last Backup** card shows timestamp
- [ ] **Next Backup** card shows timestamp
- [ ] **Retention** card shows number of days

### Action Buttons
- [ ] "Start Backup Now" button visible and enabled
- [ ] "Configure Schedule" button visible and enabled

### Create Backup Test
- [ ] Click "Start Backup Now"
- [ ] Alert appears: "Backup created successfully!" OR error message
- [ ] If success, backup list refreshes
- [ ] New backup appears at top of list

### Backup List
- [ ] Backups display in chronological order (newest first)
- [ ] Each backup shows:
  - [ ] Backup ID
  - [ ] Timestamp
  - [ ] Size
  - [ ] Type (Full/Incremental)
  - [ ] Duration
  - [ ] File count
  - [ ] Status (Completed)
- [ ] "Restore" button per backup
- [ ] "Delete" button per backup

### Restore Backup Test
- [ ] Click "Restore" button on any backup
- [ ] Restore modal opens
- [ ] Backup details display correctly
- [ ] Restore location input has default value
- [ ] Two restore options visible:
  - [ ] "Overwrite existing files"
  - [ ] "Create new location"
- [ ] Select "Create new location"
- [ ] Warning does NOT show
- [ ] Select "Overwrite existing files"
- [ ] Yellow warning shows: "This action cannot be undone"
- [ ] Click "Start Restore"
- [ ] Progress bar appears (0-100%)
- [ ] Success message appears
- [ ] Modal closes after 2 seconds OR click "Close"

### Delete Backup Test
- [ ] Click "Delete" button on any backup
- [ ] Confirmation dialog: "Are you sure you want to delete backup..."
- [ ] Click "Cancel" - nothing happens
- [ ] Click "Delete" again
- [ ] Click "OK"
- [ ] Alert: "Backup deleted successfully" OR error message
- [ ] Backup list refreshes
- [ ] Deleted backup no longer visible

### Empty State
- [ ] If no backups, shows archive icon and "No backups found" message

**Test Backup Count**: _____ backups found

**Notes**: ___________________________________________________________________

---

## Tab 4: Backup Scheduling

### CronBuilder Component
- [ ] Preset dropdown displays
- [ ] Default preset selected (e.g., "Daily at 2:00 AM")
- [ ] Cron expression displays below: `0 2 * * *`
- [ ] Human-readable description: "Runs every day at 02:00"

### Preset Selection Test
- [ ] Change preset to "Hourly"
- [ ] Cron expression updates to `0 * * * *`
- [ ] Description updates to "Runs every day every hour at :00"
- [ ] Change preset to "Weekly on Sunday at 2:00 AM"
- [ ] Cron expression updates to `0 2 * * 0`
- [ ] Description updates appropriately
- [ ] Change preset to "Monthly on the 1st at 2:00 AM"
- [ ] Cron expression updates to `0 2 1 * *`

### Custom Cron Test
- [ ] Select "Custom schedule" preset
- [ ] Custom field section appears
- [ ] 5 input fields visible: Minute, Hour, Day, Month, Weekday
- [ ] Info tooltip visible: "Use * for 'every' or specific numbers"
- [ ] Change Minute to "30"
- [ ] Cron expression updates to `30 2 * * *`
- [ ] Change Hour to "9"
- [ ] Cron expression updates to `30 9 * * *`
- [ ] Description updates appropriately

### Quick Reference
- [ ] Click "Cron Format Reference" (if visible)
- [ ] Reference documentation expands
- [ ] Examples shown (e.g., `0 2 * * *` = Daily at 2:00 AM)

### Other Configuration
- [ ] **Retention Days** field shows number (default: 7)
- [ ] Change to different number (e.g., 14)
- [ ] Value updates
- [ ] **Backup Location** field shows path
- [ ] Change path (e.g., /home/backups)
- [ ] **Enable automatic backups** checkbox visible
- [ ] Check/uncheck toggles value

### Save Configuration Test
- [ ] Click "Save Configuration"
- [ ] Alert: "Backup configuration saved successfully!" OR error
- [ ] If success, values persist

**Notes**: ___________________________________________________________________

---

## Tab 5: Cloud Backup

### Provider Selection
- [ ] Three provider cards visible:
  - [ ] Amazon S3 (bucket icon)
  - [ ] Backblaze B2 (cloud icon)
  - [ ] Wasabi (filing cabinet icon)
- [ ] Click "Amazon S3" - card highlights (blue border)
- [ ] Click "Backblaze B2" - card highlights
- [ ] Click "Wasabi" - card highlights

### Configuration Form (Test with Amazon S3)
- [ ] **Access Key ID** field visible
- [ ] **Secret Access Key** field visible (type=password)
- [ ] Show/hide credentials checkbox visible
- [ ] Check "Show credentials" - fields change to type=text
- [ ] Uncheck - fields return to type=password
- [ ] **Bucket Name** field visible
- [ ] **Region** dropdown visible
- [ ] Region options: us-east-1, us-west-1, us-west-2, etc.
- [ ] **Enable automatic cloud backup sync** checkbox visible

### Backblaze B2 Configuration
- [ ] Select "Backblaze B2"
- [ ] **Endpoint URL** field appears
- [ ] Default value: "s3.us-west-004.backblazeb2.com"
- [ ] **Region** dropdown NOT visible

### Wasabi Configuration
- [ ] Select "Wasabi"
- [ ] **Endpoint URL** field appears
- [ ] Default value: "s3.wasabisys.com"
- [ ] **Region** dropdown visible

### Connection Test
- [ ] Fill in all required fields with VALID credentials
- [ ] Click "Test Connection"
- [ ] Button changes to "Testing Connection..." with spinner
- [ ] After test:
  - **Success**: Green checkmark box, "Connection Successful"
  - **Failure**: Red X box, error message
- [ ] "Save Configuration" button enabled only after success

### Save Configuration Test
- [ ] After successful test, click "Save Configuration"
- [ ] Alert: "Cloud backup configuration saved successfully!" OR error

### Info Box
- [ ] Blue info box visible at bottom
- [ ] "Getting Started" section shows:
  - Create bucket
  - Generate API credentials
  - Grant permissions
  - Test connection

**Provider Tested**: _____________________

**Notes**: ___________________________________________________________________

---

## Tab 6: Verification

### Initial Display
- [ ] Header shows: "Backup Verification"
- [ ] "Verify All Backups" button visible
- [ ] Blue info box shows verification process:
  - Validates file checksums
  - Checks archive integrity
  - Verifies files accessible
  - Tests partial restore

### Backup List
- [ ] All backups listed
- [ ] Each backup shows:
  - [ ] Backup ID
  - [ ] Timestamp
  - [ ] Size
  - [ ] Type
  - [ ] Files count
  - [ ] Status: "Not verified" (gray icon)
- [ ] "Verify" button per backup

### Single Verification Test
- [ ] Click "Verify" button on one backup
- [ ] Button changes to "Verifying..." with spinner
- [ ] Status icon changes to spinner (blue)
- [ ] "Verifying backup integrity..." message appears
- [ ] After verification (simulated 2-3 seconds):
  - **Success**: Green checkmark, "Backup verified successfully"
  - **Details** list shows:
    - Checksum validated: OK
    - All files accessible: OK
    - Archive integrity: OK
  - **Corrupted**: Red X, error message
  - **Warning**: Yellow triangle, warning message

### Verify All Test
- [ ] Click "Verify All Backups"
- [ ] Verifications run sequentially
- [ ] Each backup shows spinner, then result
- [ ] 1-second delay between verifications

### Summary Panel
- [ ] After verifications, summary panel appears at bottom
- [ ] Shows counts:
  - [ ] Total backups verified
  - [ ] Verified count (green)
  - [ ] Warnings count (yellow)
  - [ ] Corrupted count (red)

**Test Verification Count**: _____ backups verified

**Notes**: ___________________________________________________________________

---

## Tab 7: Storage Optimizer

### Initial Display
- [ ] Header shows: "Storage Optimizer"
- [ ] "Scan for Cleanup" button visible
- [ ] Empty state message: "Click 'Scan for Cleanup' to find optimization opportunities"

### Scan Test
- [ ] Click "Scan for Cleanup"
- [ ] Button changes to "Scanning..." with spinner
- [ ] Scan runs (simulated 2 seconds)
- [ ] After scan, 3 summary cards appear:
  - [ ] **Potential Savings** (green)
  - [ ] **Items Found** (blue)
  - [ ] **Selected Items** (purple)

### Cleanup Categories
- [ ] **Unused Docker Images** category displays (🐳)
  - [ ] Shows count and total size
  - [ ] "Select All" / "Deselect All" button visible
  - [ ] Up to 5 items listed with checkboxes
  - [ ] Each item shows name, age, size
- [ ] **Unused Docker Volumes** category displays (📦)
  - Same structure as above
- [ ] **Temporary Files** category displays (📄)
  - Shows paths instead of individual files
- [ ] **Old Log Files** category displays (📋)
  - Shows paths
- [ ] **Cache Directories** category displays (🗃️)
  - Shows paths

### Item Selection Test
- [ ] Click checkbox on one item - Selected Items count increases
- [ ] Unclick - count decreases
- [ ] Click "Select All" in one category - all items in category selected
- [ ] Click "Deselect All" - all items deselected
- [ ] Select items across multiple categories - count accurate

### Cleanup Test
- [ ] Select at least 3 items
- [ ] "Ready to clean up X item(s)" panel appears at bottom
- [ ] Warning text: "This action cannot be undone"
- [ ] Click "Clean Up Now"
- [ ] Confirmation dialog: "Are you sure you want to clean X items? This action cannot be undone."
- [ ] Click "Cancel" - nothing happens
- [ ] Click "Clean Up Now" again
- [ ] Click "OK"
- [ ] Button changes to "Cleaning..." with spinner
- [ ] After cleanup (simulated):
  - Alert: Success or error
  - Automatic rescan runs
  - Numbers update (Potential Savings decreases)

### Warning Box
- [ ] Yellow warning box visible at bottom
- [ ] Text: "Always create a backup before performing cleanup operations..."

**Test Items Cleaned**: _____ items

**Notes**: ___________________________________________________________________

---

## General UI/UX Tests

### Tab Navigation
- [ ] All 7 tabs visible in tab bar
- [ ] Tab icons display correctly
- [ ] Click each tab - content switches correctly
- [ ] Active tab highlighted (blue underline)
- [ ] Tab bar scrolls horizontally on mobile/narrow screens

### Refresh Button (Global)
- [ ] Refresh button in header
- [ ] Works from any tab
- [ ] Updates all data (storage, backups, cloud config)
- [ ] Shows "Refreshing..." state

### Loading States
- [ ] Initial page load shows full-screen spinner
- [ ] Spinner disappears when data loads
- [ ] No flickering or layout shift

### Error Handling
- [ ] **Test**: Disconnect from internet, click Refresh
- [ ] Error logged to console
- [ ] Alert shows: "Failed to load..." OR falls back to mock data
- [ ] **Test**: Restore internet, click Refresh
- [ ] Data loads successfully

### Dark Mode
- [ ] Switch to dark mode (system or toggle)
- [ ] All tabs render correctly
- [ ] Cards have dark background
- [ ] Text is readable (light on dark)
- [ ] Icons adapt colors
- [ ] Switch back to light mode
- [ ] Everything renders correctly

### Responsive Design
- [ ] Test on desktop (1920x1080)
  - [ ] Layout uses full width
  - [ ] Grid layouts display multiple columns
- [ ] Test on tablet (768px width)
  - [ ] Tab bar scrolls horizontally
  - [ ] Grid layouts adapt (fewer columns)
- [ ] Test on mobile (375px width)
  - [ ] Single column layouts
  - [ ] Cards stack vertically
  - [ ] Text remains readable

### Browser Compatibility
- [ ] Chrome/Chromium - all features work
- [ ] Firefox - all features work
- [ ] Safari - all features work
- [ ] Edge - all features work

**Browsers Tested**: _____________________________________________________

**Notes**: ___________________________________________________________________

---

## Performance Tests

### Page Load Time
- [ ] Initial page load < 3 seconds
- [ ] Tab switches instant (< 100ms)
- [ ] Data refresh < 2 seconds

### Large Data Sets
- [ ] **Test**: 50+ backups in list
  - [ ] List renders without lag
  - [ ] Scrolling smooth
- [ ] **Test**: 20+ volumes
  - [ ] List renders without lag
- [ ] **Test**: 100+ cleanup items
  - [ ] Selection responsive

### Memory Leaks
- [ ] Switch between tabs 20+ times
- [ ] No memory increase in DevTools
- [ ] No console warnings

**Notes**: ___________________________________________________________________

---

## Accessibility Tests

### Keyboard Navigation
- [ ] Tab key navigates through buttons
- [ ] Enter key activates buttons
- [ ] Arrow keys work in dropdowns
- [ ] Focus indicators visible

### Screen Reader
- [ ] Button labels descriptive
- [ ] Form fields have labels
- [ ] Status messages announced

**Notes**: ___________________________________________________________________

---

## Edge Cases & Error Scenarios

### Empty States
- [ ] No storage data - displays fallback
- [ ] No volumes - shows empty state
- [ ] No backups - shows empty state
- [ ] No cleanup opportunities - shows empty state

### Invalid Inputs
- [ ] **Test**: Enter invalid cron expression (e.g., "99 99 99 99 99")
  - Description shows "Invalid cron expression"
- [ ] **Test**: Enter negative retention days
  - Input validation prevents it
- [ ] **Test**: Leave cloud credentials blank
  - "Test Connection" disabled OR shows error

### Network Errors
- [ ] API returns 404 - error handled gracefully
- [ ] API returns 500 - error handled gracefully
- [ ] Slow network - loading states persist

**Notes**: ___________________________________________________________________

---

## Security Tests

### Credential Handling
- [ ] Cloud credentials hidden by default (type=password)
- [ ] Show credentials requires explicit action
- [ ] Credentials not visible in console logs
- [ ] Credentials not exposed in network tab

### Confirmation Dialogs
- [ ] Delete backup requires confirmation
- [ ] Cleanup requires confirmation
- [ ] Restore with overwrite shows warning

**Notes**: ___________________________________________________________________

---

## Final Checklist

- [ ] All 7 tabs tested
- [ ] All components functional
- [ ] No console errors
- [ ] No visual bugs
- [ ] Dark mode works
- [ ] Responsive design works
- [ ] Error handling works
- [ ] Performance acceptable
- [ ] Documentation matches implementation

---

## Issues Found

**Issue 1**:
- **Severity**: Critical / High / Medium / Low
- **Description**: _____________________________________________________________
- **Steps to Reproduce**: _______________________________________________________
- **Expected**: _________________________________________________________________
- **Actual**: ___________________________________________________________________

**Issue 2**:
- **Severity**: Critical / High / Medium / Low
- **Description**: _____________________________________________________________
- **Steps to Reproduce**: _______________________________________________________
- **Expected**: _________________________________________________________________
- **Actual**: ___________________________________________________________________

**Issue 3**:
- **Severity**: Critical / High / Medium / Low
- **Description**: _____________________________________________________________
- **Steps to Reproduce**: _______________________________________________________
- **Expected**: _________________________________________________________________
- **Actual**: ___________________________________________________________________

---

## Sign-Off

**Tester**: ___________________
**Date**: ___________________
**Result**: PASS / FAIL / PASS WITH ISSUES (circle one)
**Ready for Production**: YES / NO (circle one)

**Additional Notes**: __________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
