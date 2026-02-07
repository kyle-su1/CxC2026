import React, { useState } from 'react';

const BoundingBoxOverlay = ({ boundingBox, label, onHover }) => {
    if (!boundingBox || boundingBox.length !== 4) return null;

    // Gemini returns [ymin, xmin, ymax, xmax] normalized to 0-1000
    const [ymin, xmin, ymax, xmax] = boundingBox;

    const top = (ymin / 1000) * 100;
    const left = (xmin / 1000) * 100;
    const height = ((ymax - ymin) / 1000) * 100;
    const width = ((xmax - xmin) / 1000) * 100;

    const style = {
        position: 'absolute',
        top: `${top}%`,
        left: `${left}%`,
        width: `${width}%`,
        height: `${height}%`,
        border: '3px solid #00ff00',
        backgroundColor: 'rgba(0, 255, 0, 0.1)',
        cursor: 'pointer',
        zIndex: 10,
        transition: 'all 0.2s ease-in-out',
    };

    return (
        <div
            className="bounding-box"
            style={style}
            onMouseEnter={() => onHover(true)}
            onMouseLeave={() => onHover(false)}
        >
            <div style={{
                position: 'absolute',
                top: '-30px',
                left: '0',
                backgroundColor: '#00ff00',
                color: 'black',
                padding: '2px 8px',
                fontSize: '14px',
                fontWeight: 'bold',
                borderRadius: '4px',
                whiteSpace: 'nowrap'
            }}>
                {label || 'Detected Item'}
            </div>
        </div>
    );
};

export default BoundingBoxOverlay;
