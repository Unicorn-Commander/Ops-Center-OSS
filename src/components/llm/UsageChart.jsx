import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function UsageChart({ data, title = "Usage by Model" }) {
  const chartData = Object.entries(data || {}).map(([key, value]) => ({
    name: key.split(':')[1] || key,
    requests: value.request_count || 0,
    tokens: (value.total_input_tokens || 0) + (value.total_output_tokens || 0)
  }));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>{title}</Typography>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="requests" fill="#8884d8" name="Requests" />
            <Bar dataKey="tokens" fill="#82ca9d" name="Tokens" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
