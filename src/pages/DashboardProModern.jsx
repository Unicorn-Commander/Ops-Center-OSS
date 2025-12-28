import React, { useState, useEffect } from 'react';
import { Box, Grid, Container, Fade } from '@mui/material';
import { motion } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';

// Import new modern components
import SystemHealthScore from '../components/SystemHealthScore';
import WelcomeBanner from '../components/WelcomeBanner';
import QuickActionsGrid from '../components/QuickActionsGrid';
import ResourceChartModern from '../components/ResourceChartModern';
import RecentActivityWidget from '../components/RecentActivityWidget';
import SystemAlertsWidget from '../components/SystemAlertsWidget';

// Container animations
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 12
    }
  }
};

export default function DashboardProModern() {
  const { systemData, services, fetchSystemStatus, fetchServices } = useSystem();
  const { theme, currentTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const [healthScore, setHealthScore] = useState(0);
  const [systemAlerts, setSystemAlerts] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);

  // Fetch initial data
  useEffect(() => {
    const initializeDashboard = async () => {
      setIsLoading(true);
      try {
        // Fetch system status and services
        await Promise.all([
          fetchSystemStatus(),
          fetchServices()
        ]);

        // Fetch user session
        const userResponse = await fetch('/api/v1/auth/session', {
          credentials: 'include'
        });
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setCurrentUser({
            username: userData?.user?.username || userData?.username || 'Admin',
            name: userData?.user?.name || userData?.name,
            email: userData?.user?.email || userData?.email,
            subscription_tier: userData?.user?.subscription_tier || userData?.subscription_tier || 'trial'
          });
        }
      } catch (error) {
        console.error('Failed to initialize dashboard:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeDashboard();
  }, []);

  // Auto-refresh system data every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchServices();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchSystemStatus, fetchServices]);

  // Calculate system health score
  useEffect(() => {
    if (systemData && services) {
      let score = 100;

      // CPU penalty
      if (systemData?.cpu?.percent > 90) score -= 15;
      else if (systemData?.cpu?.percent > 80) score -= 10;
      else if (systemData?.cpu?.percent > 70) score -= 5;

      // Memory penalty
      if (systemData?.memory?.percent > 90) score -= 20;
      else if (systemData?.memory?.percent > 85) score -= 15;
      else if (systemData?.memory?.percent > 75) score -= 8;

      // Disk penalty
      if (systemData?.disk?.percent > 95) score -= 25;
      else if (systemData?.disk?.percent > 90) score -= 20;
      else if (systemData?.disk?.percent > 80) score -= 10;

      // Service status penalty
      const stoppedServices = services?.filter(s => s.status !== 'running').length || 0;
      score -= stoppedServices * 5;

      setHealthScore(Math.max(0, Math.min(100, score)));
    }
  }, [systemData, services]);

  // Generate health subsystem details
  const getHealthDetails = () => {
    if (!systemData) return null;

    return [
      {
        name: 'CPU',
        value: systemData?.cpu?.percent || 0,
        icon: 'CpuChipIcon',
        status: systemData?.cpu?.percent < 70 ? 'healthy' : systemData?.cpu?.percent < 85 ? 'degraded' : 'critical'
      },
      {
        name: 'Memory',
        value: systemData?.memory?.percent || 0,
        icon: 'ServerIcon',
        status: systemData?.memory?.percent < 75 ? 'healthy' : systemData?.memory?.percent < 85 ? 'degraded' : 'critical'
      },
      {
        name: 'Disk',
        value: systemData?.disk?.percent || 0,
        icon: 'CircleStackIcon',
        status: systemData?.disk?.percent < 80 ? 'healthy' : systemData?.disk?.percent < 90 ? 'degraded' : 'critical'
      },
      {
        name: 'Network',
        value: Math.min(100, (systemData?.network?.bytes_sent || 0) / 1000000),
        icon: 'SignalIcon',
        status: 'healthy'
      }
    ];
  };

  // Quick stats for welcome banner
  const getQuickStats = () => {
    return {
      activeServices: services?.filter(s => s.status === 'running').length || 0,
      totalServices: services?.length || 0
    };
  };

  // Generate chart data for resource monitoring
  const getCPUChartData = () => {
    // In production, this would fetch historical data from API
    // For now, generating mock data
    const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const values = Array.from({ length: 24 }, () => Math.random() * 100);
    return { labels, values };
  };

  const getMemoryChartData = () => {
    const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const values = Array.from({ length: 24 }, () => Math.random() * 100);
    return { labels, values };
  };

  const getDiskChartData = () => {
    return {
      volumes: [
        { name: 'System', used: systemData?.disk?.used / (1024 ** 3) || 45, total: 100 },
        { name: 'Data', used: 120, total: 200 },
        { name: 'Backups', used: 180, total: 300 }
      ]
    };
  };

  const getNetworkChartData = () => {
    const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const inbound = Array.from({ length: 24 }, () => Math.random() * 1000);
    const outbound = Array.from({ length: 24 }, () => Math.random() * 800);
    return { labels, inbound, outbound };
  };

  return (
    <Fade in={!isLoading} timeout={800}>
      <Box
        className="min-h-screen p-6"
        sx={{
          background: currentTheme === 'light'
            ? 'linear-gradient(to bottom right, #f9fafb, #f3f4f6)'
            : currentTheme === 'unicorn'
            ? 'linear-gradient(to bottom right, #1e1b4b, #312e81, #1e1b4b)'
            : 'linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a)'
        }}
      >
        <Container maxWidth="xl">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Row 1: Welcome Banner + System Health Score */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={8}>
                <motion.div variants={itemVariants}>
                  <WelcomeBanner
                    user={currentUser}
                    stats={getQuickStats()}
                  />
                </motion.div>
              </Grid>
              <Grid item xs={12} md={4}>
                <motion.div variants={itemVariants}>
                  <SystemHealthScore
                    score={healthScore}
                    details={getHealthDetails()}
                    isLoading={isLoading}
                  />
                </motion.div>
              </Grid>
            </Grid>

            {/* Row 2: Quick Action Cards */}
            <Box sx={{ mb: 3 }}>
              <motion.div variants={itemVariants}>
                <QuickActionsGrid />
              </motion.div>
            </Box>

            {/* Row 3: Resource Charts (2x2 Grid) */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <ResourceChartModern
                    type="cpu"
                    data={getCPUChartData()}
                    title="CPU Usage"
                  />
                </motion.div>
              </Grid>
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <ResourceChartModern
                    type="memory"
                    data={getMemoryChartData()}
                    title="Memory Usage"
                  />
                </motion.div>
              </Grid>
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <ResourceChartModern
                    type="disk"
                    data={getDiskChartData()}
                    title="Disk Usage"
                  />
                </motion.div>
              </Grid>
              <Grid item xs={12} md={6}>
                <motion.div variants={itemVariants}>
                  <ResourceChartModern
                    type="network"
                    data={getNetworkChartData()}
                    title="Network I/O"
                  />
                </motion.div>
              </Grid>
            </Grid>

            {/* Row 4: Recent Activity + System Alerts */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <motion.div variants={itemVariants}>
                  <RecentActivityWidget
                    activities={recentActivities}
                    limit={10}
                    autoRefresh={true}
                  />
                </motion.div>
              </Grid>
              <Grid item xs={12} md={4}>
                <motion.div variants={itemVariants}>
                  <SystemAlertsWidget
                    alerts={systemAlerts}
                    onDismiss={(id) => {
                      setSystemAlerts(prev => prev.filter(a => a.id !== id));
                    }}
                  />
                </motion.div>
              </Grid>
            </Grid>
          </motion.div>
        </Container>
      </Box>
    </Fade>
  );
}
