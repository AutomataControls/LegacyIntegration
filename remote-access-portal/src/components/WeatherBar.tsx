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

import React from 'react';
import { SystemInfo, WeatherData } from '../types';

interface WeatherBarProps {
  systemInfo: SystemInfo | null;
  weatherData: WeatherData | null;
}

const WeatherBar: React.FC<WeatherBarProps> = ({ systemInfo, weatherData }) => {
  const getWeatherIcon = (icon: string): string => {
    const iconMap: { [key: string]: string } = {
      '01d': 'ri-sun-line',
      '01n': 'ri-moon-line',
      '02d': 'ri-sun-cloudy-line',
      '02n': 'ri-moon-cloudy-line',
      '03d': 'ri-cloud-line',
      '03n': 'ri-cloud-line',
      '04d': 'ri-cloudy-2-line',
      '04n': 'ri-cloudy-2-line',
      '09d': 'ri-drizzle-line',
      '09n': 'ri-drizzle-line',
      '10d': 'ri-rainy-line',
      '10n': 'ri-rainy-line',
      '11d': 'ri-thunderstorms-line',
      '11n': 'ri-thunderstorms-line',
      '13d': 'ri-snowy-line',
      '13n': 'ri-snowy-line',
      '50d': 'ri-mist-line',
      '50n': 'ri-mist-line'
    };
    return iconMap[icon] || 'ri-cloud-line';
  };

  return (
    <div className="weather-bar">
      <div className="weather-left">
        <div className="logo-section">
          <img 
            src="/static/automata-nexus-logo.png" 
            alt="AutomataNexus" 
            className="logo-image"
          />
          <div className="logo-text">
            <span className="logo-primary">AutomataControls</span>
            <span className="logo-secondary">Neural Nexus™</span>
          </div>
        </div>
        
        {weatherData && (
          <div className="weather-info">
            <i className={`weather-icon ${getWeatherIcon(weatherData.icon)}`}></i>
            <div className="weather-details">
              <div className="weather-temp">{weatherData.temperature}°F</div>
              <div className="weather-condition">{weatherData.condition}</div>
            </div>
            {weatherData.humidity && (
              <div className="weather-extra">
                <span className="humidity">
                  <i className="ri-drop-line"></i> {weatherData.humidity}%
                </span>
                {weatherData.windSpeed && (
                  <span className="wind">
                    <i className="ri-windy-line"></i> {weatherData.windSpeed} mph
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="weather-right">
        <div className="system-status">
          <div className="status-indicator online"></div>
          <span className="status-text">System Online</span>
        </div>
        
        <div className="controller-info">
          <div className="controller-label">Controller</div>
          <div className="controller-serial">
            {systemInfo?.serial || 'AutomataNexusBms-XXXXXX'}
          </div>
          {systemInfo?.location && (
            <div className="controller-location">
              <i className="ri-map-pin-line"></i> {systemInfo.location}
            </div>
          )}
        </div>
        
        <div className="datetime">
          <div className="time">{new Date().toLocaleTimeString()}</div>
          <div className="date">{new Date().toLocaleDateString()}</div>
        </div>
      </div>
    </div>
  );
};

export default WeatherBar;