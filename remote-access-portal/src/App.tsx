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

import React, { useState, useEffect } from 'react';
import WeatherBar from './components/WeatherBar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import NodeRED from './pages/NodeRED';
import Terminal from './pages/Terminal';
import NeuralBMS from './pages/NeuralBMS';
import { authenticatedFetch } from './services/api';
import { SystemInfo, WeatherData } from './types';
import './styles/app.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  // Fetch system info
  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const response = await authenticatedFetch('/api/system-info');
        if (response.ok) {
          const data = await response.json();
          setSystemInfo(data);
        }
      } catch (error) {
        console.error('Failed to fetch system info:', error);
      }
    };

    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch weather data
  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const response = await authenticatedFetch('/api/weather');
        if (response.ok) {
          const data = await response.json();
          setWeatherData(data);
        }
      } catch (error) {
        console.error('Failed to fetch weather:', error);
      }
    };

    fetchWeather();
    const interval = setInterval(fetchWeather, 600000); // 10 minutes
    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard systemInfo={systemInfo} />;
      case 'nodered':
        return <NodeRED />;
      case 'terminal':
        return <Terminal />;
      case 'neuralbms':
        return <NeuralBMS />;
      default:
        return <Dashboard systemInfo={systemInfo} />;
    }
  };

  return (
    <div id="app-root">
      <WeatherBar systemInfo={systemInfo} weatherData={weatherData} />
      <div className="main-container">
        <Sidebar currentView={currentView} onViewChange={setCurrentView} />
        <main className="content">
          <div className="content-inner">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;