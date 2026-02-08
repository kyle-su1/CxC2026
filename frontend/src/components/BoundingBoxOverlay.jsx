import React, { useState } from 'react';

const BoundingBoxOverlay = ({ boundingBox, label, onHover, onClick, isSelected }) => {
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
        border: isSelected ? '3px solid #34d399' : '3px solid #10b981',
        backgroundColor: isSelected ? 'rgba(52, 211, 153, 0.2)' : 'rgba(16, 185, 129, 0.1)',
        cursor: 'pointer',
        zIndex: isSelected ? 20 : 10,
        transition: 'all 0.2s ease-in-out',
        boxShadow: isSelected ? '0 0 15px rgba(16,185,129,0.5)' : 'none',
    };

    return (
        <div
            className="bounding-box"
            style={style}
            onMouseEnter={() => onHover && onHover(true)}
            onMouseLeave={() => onHover && onHover(false)}
            onClick={onClick}
        >
            <div style={{
                position: 'absolute',
                top: '-30px',
                left: '0',
                backgroundColor: isSelected ? '#34d399' : '#10b981',
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
