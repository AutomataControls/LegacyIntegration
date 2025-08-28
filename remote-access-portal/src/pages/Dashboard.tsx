/*
 * AutomataControls™ Remote Portal
 * Copyright © 2024 AutomataNexus, LLC. All rights reserved.
 * 
 * PROPRIETARY AND CONFIDENTIAL
 * This software is proprietary to AutomataNexus and constitutes valuable 
 * trade secrets. This software may not be copied, distributed, modified, 
 * or disclosed to third parties without prior written authorization from 
 * AutomataNexus. Use of this software is governed by a commercial license
 * agreement. Unauthorized use is strictly prohibited.
 * 
 * AutomataNexusBms Controller Software
 */

import React, { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { SystemInfo } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardProps {
  systemInfo: SystemInfo | null;
}

const Dashboard: React.FC<DashboardProps> = ({ systemInfo }) => {
  const [cpuHistory, setCpuHistory] = useState<number[]>(Array(20).fill(0));
  const [memHistory, setMemHistory] = useState<number[]>(Array(20).fill(0));
  const [timeLabels, setTimeLabels] = useState<string[]>(Array(20).fill(''));

  useEffect(() => {
    if (!systemInfo) return;

    const now = new Date().toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });

    setCpuHistory(prev => [...prev.slice(1), parseFloat(systemInfo.cpu_usage || '0')]);
    setMemHistory(prev => [...prev.slice(1), systemInfo.mem_percent || 0]);
    setTimeLabels(prev => [...prev.slice(1), now]);
  }, [systemInfo]);

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(20, 27, 40, 0.95)',
        titleColor: '#06b6d4',
        bodyColor: '#f0f9ff',
        borderColor: '#06b6d4',
        borderWidth: 1
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: { 
          color: '#64748b',
          callback: function(value: any) {
            return value + '%';
          }
        },
        grid: { 
          color: 'rgba(148, 163, 184, 0.1)',
          drawBorder: false
        }
      },
      x: {
        ticks: { 
          color: '#64748b',
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 6
        },
        grid: { 
          display: false 
        }
      }
    }
  };

  const cpuChartData = {
    labels: timeLabels,
    datasets: [{
      label: 'CPU Usage',
      data: cpuHistory,
      borderColor: '#06b6d4',
      backgroundColor: 'rgba(6, 182, 212, 0.1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointBackgroundColor: '#06b6d4'
    }]
  };

  const memChartData = {
    labels: timeLabels,
    datasets: [{
      label: 'Memory Usage',
      data: memHistory,
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointBackgroundColor: '#10b981'
    }]
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">System Dashboard</h1>
        <p className="dashboard-subtitle">
          {systemInfo ? (
            <>
              <span className="hostname">{systemInfo.hostname}</span>
              {systemInfo.location && (
                <span className="location">
                  <i className="ri-map-pin-line"></i> {systemInfo.location}
                </span>
              )}
            </>
          ) : (
            'Loading system information...'
          )}
        </p>
      </div>

      {systemInfo && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">CPU Temperature</span>
                <div className="metric-icon">
                  <i className="ri-temp-hot-line"></i>
                </div>
              </div>
              <div className="metric-value">{systemInfo.cpu_temp || 'N/A'}</div>
              <div className="metric-change positive">
                <i className="ri-arrow-down-line"></i>
                <span>Normal Range</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">CPU Usage</span>
                <div className="metric-icon">
                  <i className="ri-cpu-line"></i>
                </div>
              </div>
              <div className="metric-value">{systemInfo.cpu_usage || '0'}%</div>
              <div className="metric-status">
                <div className="status-bar">
                  <div 
                    className="status-bar-fill cpu"
                    style={{ width: `${systemInfo.cpu_usage || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">Memory Usage</span>
                <div className="metric-icon">
                  <i className="ri-database-2-line"></i>
                </div>
              </div>
              <div className="metric-value">{systemInfo.mem_percent || 0}%</div>
              <div className="metric-detail">
                {systemInfo.mem_used || 0}MB / {systemInfo.mem_total || 0}MB
              </div>
              <div className="metric-status">
                <div className="status-bar">
                  <div 
                    className="status-bar-fill memory"
                    style={{ width: `${systemInfo.mem_percent || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">Disk Usage</span>
                <div className="metric-icon">
                  <i className="ri-hard-drive-2-line"></i>
                </div>
              </div>
              <div className="metric-value">{systemInfo.disk_percent || 0}%</div>
              <div className="metric-detail">
                {systemInfo.disk_used || 'N/A'} / {systemInfo.disk_total || 'N/A'}
              </div>
              <div className="metric-status">
                <div className="status-bar">
                  <div 
                    className="status-bar-fill disk"
                    style={{ width: `${systemInfo.disk_percent || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">System Uptime</span>
                <div className="metric-icon">
                  <i className="ri-time-line"></i>
                </div>
              </div>
              <div className="metric-value">{formatUptime(systemInfo.uptime || 0)}</div>
              <div className="metric-change positive">
                <i className="ri-checkbox-circle-line"></i>
                <span>Stable</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span className="metric-title">Network Status</span>
                <div className="metric-icon">
                  <i className="ri-wifi-line"></i>
                </div>
              </div>
              <div className="metric-value">Connected</div>
              <div className="metric-change positive">
                <i className="ri-signal-wifi-3-line"></i>
                <span>Strong Signal</span>
              </div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">CPU Usage History</h3>
                <div className="chart-legend">
                  <span className="legend-item cpu">
                    <span className="legend-dot"></span>
                    Current: {systemInfo.cpu_usage || 0}%
                  </span>
                </div>
              </div>
              <div className="chart-wrapper">
                <Line data={cpuChartData} options={chartOptions} />
              </div>
            </div>

            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">Memory Usage History</h3>
                <div className="chart-legend">
                  <span className="legend-item memory">
                    <span className="legend-dot"></span>
                    Current: {systemInfo.mem_percent || 0}%
                  </span>
                </div>
              </div>
              <div className="chart-wrapper">
                <Line data={memChartData} options={chartOptions} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;