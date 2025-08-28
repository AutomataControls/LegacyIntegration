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

import React, { useState } from 'react';

const NodeRED: React.FC = () => {
  const [loading, setLoading] = useState(true);

  return (
    <div className="iframe-container">
      {loading && (
        <div className="iframe-loading">
          <div className="spinner-container">
            <div className="spinner"></div>
            <p className="loading-text">Loading Node-RED...</p>
            <p className="loading-subtext">Flow-based programming interface</p>
          </div>
        </div>
      )}
      <iframe
        src="/node-red"
        className="full-iframe"
        onLoad={() => setLoading(false)}
        style={{ display: loading ? 'none' : 'block' }}
        title="Node-RED"
      />
    </div>
  );
};

export default NodeRED;