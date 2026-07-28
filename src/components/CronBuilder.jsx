import React, { useState, useEffect } from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

/**
 * CronBuilder Component
 *
 * Visual cron expression builder with presets and custom editing.
 * Provides human-readable description of the schedule.
 */
export default function CronBuilder({ value, onChange, className = '' }) {
  const [cronExpression, setCronExpression] = useState(value || '0 2 * * *');
  const [preset, setPreset] = useState('custom');
  const [customFields, setCustomFields] = useState({
    minute: '0',
    hour: '2',
    day: '*',
    month: '*',
    weekday: '*'
  });

  // Presets for common schedules
  const presets = {
    hourly: { cron: '0 * * * *', label: 'Every hour' },
    daily_2am: { cron: '0 2 * * *', label: 'Daily at 2:00 AM' },
    daily_midnight: { cron: '0 0 * * *', label: 'Daily at midnight' },
    weekly_sunday: { cron: '0 2 * * 0', label: 'Weekly on Sunday at 2:00 AM' },
    weekly_monday: { cron: '0 2 * * 1', label: 'Weekly on Monday at 2:00 AM' },
    monthly: { cron: '0 2 1 * *', label: 'Monthly on the 1st at 2:00 AM' },
    custom: { cron: cronExpression, label: 'Custom schedule' }
  };

  useEffect(() => {
    // Parse existing cron expression into fields
    const parts = cronExpression.split(' ');
    if (parts.length === 5) {
      setCustomFields({
        minute: parts[0],
        hour: parts[1],
        day: parts[2],
        month: parts[3],
        weekday: parts[4]
      });
    }

    // Check if matches a preset
    const matchingPreset = Object.entries(presets).find(
      ([key, val]) => val.cron === cronExpression && key !== 'custom'
    );
    if (matchingPreset) {
      setPreset(matchingPreset[0]);
    } else {
      setPreset('custom');
    }
  }, [cronExpression]);

  const handlePresetChange = (presetKey) => {
    setPreset(presetKey);
    if (presetKey !== 'custom') {
      const newCron = presets[presetKey].cron;
      setCronExpression(newCron);
      onChange(newCron);
    }
  };

  const handleCustomFieldChange = (field, value) => {
    const newFields = { ...customFields, [field]: value };
    setCustomFields(newFields);

    const newCron = `${newFields.minute} ${newFields.hour} ${newFields.day} ${newFields.month} ${newFields.weekday}`;
    setCronExpression(newCron);
    onChange(newCron);
  };

  const getCronDescription = () => {
    try {
      const parts = cronExpression.split(' ');
      if (parts.length !== 5) return 'Invalid cron expression';

      const [minute, hour, day, month, weekday] = parts;
      let description = 'Runs ';

      // Weekday
      if (weekday !== '*') {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayNames = weekday.split(',').map(d => days[parseInt(d)] || d).join(', ');
        description += `every ${dayNames} `;
      } else if (day !== '*') {
        description += `on day ${day} of the month `;
      } else {
        description += 'every day ';
      }

      // Month
      if (month !== '*') {
        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
        const monthNames = month.split(',').map(m => months[parseInt(m) - 1] || m).join(', ');
        description += `in ${monthNames} `;
      }

      // Time
      const hourStr = hour === '*' ? 'every hour' : `at ${hour.padStart(2, '0')}`;
      const minuteStr = minute === '*' ? 'every minute' : `:${minute.padStart(2, '0')}`;

      if (hour === '*' && minute === '*') {
        description += 'every minute';
      } else if (hour === '*') {
        description += `${minuteStr} of every hour`;
      } else {
        description += `${hourStr}${minute !== '0' ? minuteStr : ':00'}`;
      }

      return description;
    } catch (error) {
      return 'Invalid cron expression';
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Preset Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Schedule Preset
        </label>
        <select
          value={preset}
          onChange={(e) => handlePresetChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="hourly">{presets.hourly.label}</option>
          <option value="daily_2am">{presets.daily_2am.label}</option>
          <option value="daily_midnight">{presets.daily_midnight.label}</option>
          <option value="weekly_sunday">{presets.weekly_sunday.label}</option>
          <option value="weekly_monday">{presets.weekly_monday.label}</option>
          <option value="monthly">{presets.monthly.label}</option>
          <option value="custom">Custom schedule</option>
        </select>
      </div>

      {/* Custom Fields (only show if custom is selected) */}
      {preset === 'custom' && (
        <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <InformationCircleIcon className="h-5 w-5 text-blue-500" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Use * for "every" or specific numbers
            </span>
          </div>

          <div className="grid grid-cols-5 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Minute (0-59)
              </label>
              <input
                type="text"
                value={customFields.minute}
                onChange={(e) => handleCustomFieldChange('minute', e.target.value)}
                placeholder="0-59 or *"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Hour (0-23)
              </label>
              <input
                type="text"
                value={customFields.hour}
                onChange={(e) => handleCustomFieldChange('hour', e.target.value)}
                placeholder="0-23 or *"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Day (1-31)
              </label>
              <input
                type="text"
                value={customFields.day}
                onChange={(e) => handleCustomFieldChange('day', e.target.value)}
                placeholder="1-31 or *"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Month (1-12)
              </label>
              <input
                type="text"
                value={customFields.month}
                onChange={(e) => handleCustomFieldChange('month', e.target.value)}
                placeholder="1-12 or *"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Weekday (0-6)
              </label>
              <input
                type="text"
                value={customFields.weekday}
                onChange={(e) => handleCustomFieldChange('weekday', e.target.value)}
                placeholder="0-6 or *"
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
              <span className="text-xs text-gray-500">0=Sun</span>
            </div>
          </div>
        </div>
      )}

      {/* Cron Expression Display */}
      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Cron Expression:</div>
        <code className="text-sm font-mono text-blue-700 dark:text-blue-300">{cronExpression}</code>
        <div className="text-xs text-gray-600 dark:text-gray-400 mt-2">
          {getCronDescription()}
        </div>
      </div>

      {/* Quick Reference */}
      <details className="text-xs text-gray-600 dark:text-gray-400">
        <summary className="cursor-pointer hover:text-gray-900 dark:hover:text-gray-200">
          Cron Format Reference
        </summary>
        <div className="mt-2 space-y-1 pl-4">
          <div><code>*</code> - Every value (any)</div>
          <div><code>5</code> - Specific value (e.g., 5th minute)</div>
          <div><code>1,3,5</code> - Multiple values (1st, 3rd, and 5th)</div>
          <div><code>1-5</code> - Range of values (1 through 5)</div>
          <div><code>*/2</code> - Every 2 units (e.g., every 2 hours)</div>
          <div className="mt-2">
            <strong>Examples:</strong>
            <ul className="list-disc list-inside">
              <li><code>0 2 * * *</code> - Daily at 2:00 AM</li>
              <li><code>0 */4 * * *</code> - Every 4 hours</li>
              <li><code>30 9 * * 1-5</code> - Weekdays at 9:30 AM</li>
              <li><code>0 0 1,15 * *</code> - 1st and 15th of month at midnight</li>
            </ul>
          </div>
        </div>
      </details>
    </div>
  );
}
