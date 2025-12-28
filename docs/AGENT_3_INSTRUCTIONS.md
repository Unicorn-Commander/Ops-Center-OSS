# Agent 3: System Monitoring Specialist - H15 Task

**Mission**: Fix network stats always showing 0 in Monitoring page

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/pages/System.jsx`

**Duration**: 2-3 hours

---

## Current Issue

**Line 180**: Network stats state is initialized but never updated:
```javascript
const [networkStats, setNetworkStats] = useState({ in: 0, out: 0 });
```

**Problem**: No `fetchNetworkStats()` function exists to populate this data from the API.

---

## Backend API Endpoint

**Endpoint**: `GET /api/v1/system/network`
**Status**: EXISTS (verified in compiled frontend)

**Expected Response**:
```json
{
  "hostname": "unicorn-server",
  "interface": "eth0",
  "ip_address": "192.168.1.100",
  "bytes_recv_per_sec": 1024567,
  "bytes_sent_per_sec": 512345,
  "total_recv": 1073741824,
  "total_sent": 536870912
}
```

---

## Required Changes

### 1. Create `fetchNetworkStats()` Function

Add this function after `fetchDiskIo()` (around line 223):

```javascript
const fetchDiskIo = async () => {
  try {
    const response = await fetch('/api/v1/system/disk-io');
    if (response.ok) {
      const data = await response.json();
      setDiskIoStats(data);
    }
  } catch (error) {
    console.error('Failed to fetch disk I/O:', error);
  }
};

// ADD THIS NEW FUNCTION:
const fetchNetworkStats = async () => {
  try {
    const response = await fetch('/api/v1/system/network');
    if (response.ok) {
      const data = await response.json();
      setNetworkStats({
        in: data.bytes_recv_per_sec || 0,
        out: data.bytes_sent_per_sec || 0,
        total_in: data.total_recv || 0,
        total_out: data.total_sent || 0
      });
    }
  } catch (error) {
    console.error('Failed to fetch network stats:', error);
    // Set to 0 on error, but don't break the UI
    setNetworkStats({ in: 0, out: 0, total_in: 0, total_out: 0 });
  }
};
```

### 2. Call Function in useEffect

Update the useEffect hook (lines 186-199):

```javascript
// Fetch data on mount and interval
useEffect(() => {
  fetchHardwareInfo();
  fetchDiskIo();
  fetchNetworkStats(); // ✅ ADD THIS LINE

  if (!autoRefresh) return;

  const interval = setInterval(() => {
    fetchSystemStatus();
    fetchDiskIo();
    fetchNetworkStats(); // ✅ ADD THIS LINE
    updateHistoricalData();
  }, refreshInterval);

  return () => clearInterval(interval);
}, [autoRefresh, refreshInterval]);
```

### 3. Update `updateHistoricalData()` Function

Find the `updateHistoricalData()` function (around line 225) and add network data collection.

**Current code** (lines 230-250) has sections for CPU, memory, GPU. Add network section:

```javascript
const updateHistoricalData = () => {
  if (!systemStatus) return;

  const timestamp = new Date().toLocaleTimeString();

  const newData = {
    cpu: [...dataRef.current.cpu, {
      time: timestamp,
      usage: systemStatus.cpu?.percent || 0,
      temp: systemStatus.cpu?.temp || 0
    }].slice(-maxDataPoints),

    memory: [...dataRef.current.memory, {
      time: timestamp,
      used: ((systemStatus.memory?.used || 0) / (1024 * 1024 * 1024)).toFixed(2),
      percent: systemStatus.memory?.percent || 0
    }].slice(-maxDataPoints),

    gpu: systemStatus.gpu?.[0] ? [...dataRef.current.gpu, {
      time: timestamp,
      utilization: systemStatus.gpu[0]?.utilization || 0,
      memory: ((systemStatus.gpu[0]?.memory_used || 0) / (1024 * 1024 * 1024)).toFixed(2),
      temp: systemStatus.gpu[0]?.temperature || 0,
      power: systemStatus.gpu[0]?.power_draw || 0
    }].slice(-maxDataPoints) : dataRef.current.gpu,

    // ✅ ADD THIS NETWORK SECTION:
    network: [...dataRef.current.network, {
      time: timestamp,
      in: networkStats.in || 0,
      out: networkStats.out || 0
    }].slice(-maxDataPoints),

    diskIo: diskIoStats ? [...dataRef.current.diskIo, {
      time: timestamp,
      read: diskIoStats.read_bytes_per_sec || 0,
      write: diskIoStats.write_bytes_per_sec || 0
    }].slice(-maxDataPoints) : dataRef.current.diskIo
  };

  setHistoricalData(newData);
  dataRef.current = newData;
};
```

### 4. Verify Network Tab UI

The Network tab should already exist (lines 898-913). Verify it displays the data correctly.

**Find this section** and ensure it uses `networkStats` state:

```javascript
{selectedView === 'network' && (
  <motion.div variants={cardVariants} className={cardClass}>
    <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
      Network I/O
    </h3>
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={historicalData.network}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
          <XAxis dataKey="time" stroke={chartColors.text} />
          <YAxis stroke={chartColors.text} />
          <Tooltip
            contentStyle={{
              backgroundColor: chartColors.tooltipBg,
              border: `1px solid ${chartColors.border}`,
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="in"
            name="Download"
            stroke={chartColors.primary}
            fill={chartColors.primary}
            fillOpacity={0.3}
          />
          <Area
            type="monotone"
            dataKey="out"
            name="Upload"
            stroke={chartColors.success}
            fill={chartColors.success}
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>

    {/* ✅ ADD CURRENT STATS DISPLAY */}
    <div className="grid grid-cols-2 gap-4 mt-4">
      <div className={`p-4 rounded-lg ${theme.bg.secondary}`}>
        <p className={`text-sm ${theme.text.secondary}`}>Download Speed</p>
        <p className={`text-2xl font-bold ${theme.text.primary}`}>
          {formatNetworkSpeed(networkStats.in)}
        </p>
      </div>
      <div className={`p-4 rounded-lg ${theme.bg.secondary}`}>
        <p className={`text-sm ${theme.text.secondary}`}>Upload Speed</p>
        <p className={`text-2xl font-bold ${theme.text.primary}`}>
          {formatNetworkSpeed(networkStats.out)}
        </p>
      </div>
    </div>
  </motion.div>
)}
```

---

## formatNetworkSpeed() Function

This function already exists in the file (lines 41-45). Verify it's working:

```javascript
const formatNetworkSpeed = (bytesPerSec) => {
  if (bytesPerSec < 1024) return `${bytesPerSec.toFixed(0)} B/s`;
  if (bytesPerSec < 1024 * 1024) return `${(bytesPerSec / 1024).toFixed(2)} KB/s`;
  return `${(bytesPerSec / (1024 * 1024)).toFixed(2)} MB/s`;
};
```

---

## Backend Verification

Check if the network endpoint exists and returns proper data:

```bash
# Test the endpoint
curl http://localhost:8084/api/v1/system/network

# Expected output:
{
  "hostname": "...",
  "interface": "eth0",
  "ip_address": "...",
  "bytes_recv_per_sec": 1234,
  "bytes_sent_per_sec": 5678
}
```

**If endpoint doesn't exist**, report it and create a stub backend endpoint:

```python
# backend/server.py or backend/system_api.py
@router.get("/api/v1/system/network")
async def get_network_stats():
    """Get current network I/O statistics"""
    try:
        import psutil

        # Get network I/O stats
        net_io = psutil.net_io_counters()

        # Calculate per-second rates (simplified)
        # In production, should track deltas over time
        bytes_recv_per_sec = net_io.bytes_recv / (time.time() - process_start_time)
        bytes_sent_per_sec = net_io.bytes_sent / (time.time() - process_start_time)

        return {
            "hostname": socket.gethostname(),
            "interface": "eth0",  # Could detect primary interface
            "bytes_recv_per_sec": bytes_recv_per_sec,
            "bytes_sent_per_sec": bytes_sent_per_sec,
            "total_recv": net_io.bytes_recv,
            "total_sent": net_io.bytes_sent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Acceptance Criteria

- [ ] `fetchNetworkStats()` function created
- [ ] Function called in useEffect on mount
- [ ] Function called in useEffect interval (every 2 seconds)
- [ ] `networkStats` state updates with real data
- [ ] Network tab shows live download/upload speeds
- [ ] Historical network chart populates over time
- [ ] Data formatted correctly (KB/s, MB/s)
- [ ] No errors in browser console
- [ ] Graceful handling if API unavailable

---

## Testing Checklist

```bash
# 1. Build and deploy
cd /home/muut/Production/UC-Cloud/services/ops-center
npm run build
cp -r dist/* public/
docker restart ops-center-direct

# 2. Test backend endpoint
curl http://localhost:8084/api/v1/system/network

# 3. Test in browser
# Visit: https://your-domain.com/admin/system/monitoring
# - Check Overview cards show network stats (not 0)
# - Click "Network" tab
# - Verify chart updates every 2 seconds
# - Verify download/upload speeds display with units
# - Monitor for 30+ seconds to see historical data build up

# 4. Test error handling
# - Stop ops-center backend temporarily
# - Verify frontend doesn't crash
# - Shows 0 values instead of breaking
```

---

## Edge Cases

1. **API Returns Empty Data**: Set to 0, don't crash
2. **API Returns Null**: Set to 0, don't crash
3. **Network Disconnected**: Show 0 KB/s
4. **Very High Speeds**: Format should handle GB/s if needed

---

## Deliverables

1. Modified `src/pages/System.jsx` with:
   - `fetchNetworkStats()` function implemented
   - Function called in useEffect
   - `updateHistoricalData()` includes network data
   - Network stats display with proper formatting
2. Working live network monitoring
3. Historical chart populating correctly
4. Report if backend endpoint needs to be created
