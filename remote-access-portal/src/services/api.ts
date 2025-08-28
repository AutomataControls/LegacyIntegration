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

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Get auth token from session storage
const getAuthToken = (): string | null => {
  return sessionStorage.getItem('authToken');
};

// Set auth token
export const setAuthToken = (token: string): void => {
  sessionStorage.setItem('authToken', token);
};

// Clear auth token
export const clearAuthToken = (): void => {
  sessionStorage.removeItem('authToken');
};

// Authenticated fetch wrapper
export const authenticatedFetch = async (
  url: string, 
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    ...(token && { 'X-API-Key': token })
  };

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers
  });

  // Handle unauthorized responses
  if (response.status === 401) {
    clearAuthToken();
    // Optionally redirect to login
    window.location.href = '/login';
  }

  return response;
};

// API methods
export const api = {
  // System info
  async getSystemInfo() {
    const response = await authenticatedFetch('/api/system-info');
    return response.json();
  },

  // Weather
  async getWeather() {
    const response = await authenticatedFetch('/api/weather');
    return response.json();
  },

  // Send email notification
  async sendNotification(data: {
    subject: string;
    message: string;
    type: 'alert' | 'info' | 'warning' | 'error';
  }) {
    const response = await authenticatedFetch('/api/notifications', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  },

  // Get controller logs
  async getLogs(limit: number = 100) {
    const response = await authenticatedFetch(`/api/logs?limit=${limit}`);
    return response.json();
  },

  // System commands
  async executeCommand(command: string) {
    const response = await authenticatedFetch('/api/command', {
      method: 'POST',
      body: JSON.stringify({ command })
    });
    return response.json();
  },

  // Configuration
  async getConfig() {
    const response = await authenticatedFetch('/api/config');
    return response.json();
  },

  async updateConfig(config: any) {
    const response = await authenticatedFetch('/api/config', {
      method: 'PUT',
      body: JSON.stringify(config)
    });
    return response.json();
  }
};