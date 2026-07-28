import React from 'react';
import { Grid, Card, CardContent, Box, Typography } from '@mui/material';
import { User, Shield, Terminal, Key } from 'lucide-react';
import { alpha } from '@mui/material/styles';

const StatisticsCards = ({ stats }) => {
  const cards = [
    {
      title: 'Total Users',
      value: stats.totalUsers,
      icon: User,
      color: '#667eea',
    },
    {
      title: 'Sudo Users',
      value: stats.sudoUsers,
      icon: Shield,
      color: '#f093fb',
    },
    {
      title: 'Active Sessions',
      value: stats.activeSessions,
      icon: Terminal,
      color: '#4facfe',
    },
    {
      title: 'SSH Keys Configured',
      value: stats.sshKeysConfigured,
      icon: Key,
      color: '#43e97b',
    },
  ];

  return (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      {cards.map((card) => {
        const IconComponent = card.icon;
        return (
          <Grid item xs={12} sm={6} md={3} key={card.title}>
            <Card
              sx={{
                background: alpha(card.color, 0.1),
                backdropFilter: 'blur(10px)',
                border: '1px solid',
                borderColor: alpha(card.color, 0.2),
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <IconComponent size={24} color={card.color} />
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {card.value}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {card.title}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
};

export default StatisticsCards;
