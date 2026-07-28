import React, { useState, useRef, useEffect } from 'react';
import { Box, Card, CardContent, Typography, IconButton, Menu, MenuItem } from '@mui/material';
import { motion } from 'framer-motion';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  EllipsisVerticalIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function ResourceChartModern({ type, data, title }) {
  const { theme, currentTheme } = useTheme();
  const chartRef = useRef(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExport = () => {
    const chart = chartRef.current;
    if (chart) {
      const url = chart.toBase64Image();
      const link = document.createElement('a');
      link.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.png`;
      link.href = url;
      link.click();
    }
    handleMenuClose();
  };

  // Chart type configurations
  const getChartConfig = () => {
    switch (type) {
      case 'cpu':
        return getCPUChartConfig();
      case 'memory':
        return getMemoryChartConfig();
      case 'disk':
        return getDiskChartConfig();
      case 'network':
        return getNetworkChartConfig();
      default:
        return getCPUChartConfig();
    }
  };

  // CPU Chart Configuration (Line Chart)
  const getCPUChartConfig = () => {
    const isDark = currentTheme !== 'light';
    const labels = data?.labels || Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const values = data?.values || Array.from({ length: 24 }, () => Math.random() * 100);

    return {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'CPU Usage (%)',
            data: values,
            borderColor: currentTheme === 'unicorn'
              ? 'rgba(168, 85, 247, 1)'
              : 'rgba(59, 130, 246, 1)',
            backgroundColor: currentTheme === 'unicorn'
              ? 'rgba(168, 85, 247, 0.1)'
              : 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: isDark ? '#fff' : '#000',
            bodyColor: isDark ? '#fff' : '#000',
            borderColor: currentTheme === 'unicorn' ? 'rgba(168, 85, 247, 0.5)' : 'rgba(59, 130, 246, 0.5)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              maxTicksLimit: 12
            }
          },
          y: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              callback: (value) => `${value}%`
            },
            min: 0,
            max: 100
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    };
  };

  // Memory Chart Configuration (Line Chart)
  const getMemoryChartConfig = () => {
    const isDark = currentTheme !== 'light';
    const labels = data?.labels || Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const values = data?.values || Array.from({ length: 24 }, () => Math.random() * 100);

    return {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Memory Usage (%)',
            data: values,
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: isDark ? '#fff' : '#000',
            bodyColor: isDark ? '#fff' : '#000',
            borderColor: 'rgba(16, 185, 129, 0.5)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              maxTicksLimit: 12
            }
          },
          y: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              callback: (value) => `${value}%`
            },
            min: 0,
            max: 100
          }
        }
      }
    };
  };

  // Disk Chart Configuration (Doughnut Chart)
  const getDiskChartConfig = () => {
    const isDark = currentTheme !== 'light';
    const volumes = data?.volumes || [
      { name: 'System', used: 45, total: 100 },
      { name: 'Data', used: 60, total: 200 },
      { name: 'Backups', used: 120, total: 300 }
    ];

    return {
      type: 'doughnut',
      data: {
        labels: volumes.map(v => v.name),
        datasets: [
          {
            label: 'Disk Usage (GB)',
            data: volumes.map(v => v.used),
            backgroundColor: [
              'rgba(59, 130, 246, 0.8)',
              'rgba(16, 185, 129, 0.8)',
              'rgba(245, 158, 11, 0.8)',
              'rgba(239, 68, 68, 0.8)'
            ],
            borderColor: [
              'rgba(59, 130, 246, 1)',
              'rgba(16, 185, 129, 1)',
              'rgba(245, 158, 11, 1)',
              'rgba(239, 68, 68, 1)'
            ],
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: isDark ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)',
              padding: 16,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: isDark ? '#fff' : '#000',
            bodyColor: isDark ? '#fff' : '#000',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const volume = volumes[context.dataIndex];
                return ` ${volume.name}: ${volume.used}GB / ${volume.total}GB`;
              }
            }
          }
        },
        cutout: '70%'
      }
    };
  };

  // Network Chart Configuration (Area Chart)
  const getNetworkChartConfig = () => {
    const isDark = currentTheme !== 'light';
    const labels = data?.labels || Array.from({ length: 24 }, (_, i) => `${i}:00`);
    const inbound = data?.inbound || Array.from({ length: 24 }, () => Math.random() * 1000);
    const outbound = data?.outbound || Array.from({ length: 24 }, () => Math.random() * 800);

    return {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Inbound (MB/s)',
            data: inbound,
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            borderWidth: 2
          },
          {
            label: 'Outbound (MB/s)',
            data: outbound,
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: isDark ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              usePointStyle: true,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: isDark ? '#fff' : '#000',
            bodyColor: isDark ? '#fff' : '#000',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              maxTicksLimit: 12
            }
          },
          y: {
            grid: {
              color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              drawBorder: false
            },
            ticks: {
              color: isDark ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)',
              callback: (value) => `${value} MB/s`
            }
          }
        }
      }
    };
  };

  const chartConfig = getChartConfig();
  const ChartComponent = chartConfig.type === 'doughnut' ? Doughnut : Line;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className={`${theme.card} h-full`}>
        <CardContent className="p-6">
          {/* Header */}
          <Box className="flex items-center justify-between mb-6">
            <Typography variant="h6" className={`font-bold ${theme.text.primary}`}>
              {title}
            </Typography>

            <IconButton onClick={handleMenuOpen} size="small">
              <EllipsisVerticalIcon className={`h-5 w-5 ${theme.text.secondary}`} />
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleExport}>
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Export PNG
              </MenuItem>
            </Menu>
          </Box>

          {/* Chart */}
          <Box sx={{ height: 300, position: 'relative' }}>
            <ChartComponent
              ref={chartRef}
              data={chartConfig.data}
              options={chartConfig.options}
            />
          </Box>

          {/* Footer stats */}
          {type !== 'disk' && (
            <Box className="mt-4 pt-4 border-t border-gray-700">
              <Box className="flex items-center justify-between text-sm">
                <Typography variant="caption" className={theme.text.secondary}>
                  Last 24 hours • Auto-refreshing
                </Typography>
                <Typography variant="caption" className={theme.text.accent}>
                  {timeRange}
                </Typography>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
