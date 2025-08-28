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

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: string;
  description?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const navItems: NavItem[] = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: 'ri-dashboard-line',
      description: 'System overview and metrics'
    },
    { 
      id: 'nodered', 
      label: 'Node-RED', 
      icon: 'ri-node-tree',
      description: 'Flow-based programming'
    },
    { 
      id: 'terminal', 
      label: 'Terminal', 
      icon: 'ri-terminal-box-line',
      description: 'Command line access'
    },
    { 
      id: 'neuralbms', 
      label: 'Neural BMS', 
      icon: 'ri-database-2-line',
      description: 'Building management system'
    }
  ];

  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Navigation</div>
      </div>
      
      <div className="nav-menu">
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
            title={item.description}
          >
            <i className={`nav-icon ${item.icon}`}></i>
            <span className="nav-label">{item.label}</span>
            {currentView === item.id && (
              <span className="nav-indicator"></span>
            )}
          </button>
        ))}
      </div>
      
      <div className="sidebar-footer">
        <div className="sidebar-version">
          <span>v2.0.0</span>
        </div>
        <div className="sidebar-copyright">
          © 2024 AutomataNexus
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;