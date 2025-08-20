# Halo Effect Implementation for Voice AI Interface

## Problem Statement

The original implementation used CSS pseudo-elements (`::before` and `::after`) with box-shadow effects to create visual halos around the agent portrait. This approach caused significant issues on Safari iOS:

1. **Square halos instead of circular** - Safari rendered box-shadow on pseudo-elements as squares
2. **Severe flickering** - Rapid CSS transitions caused visual artifacts
3. **Inconsistent rendering** - Different behavior between desktop and mobile browsers
4. **Flickering on short speech segments** - Rapid `agent_start_talking`/`agent_stop_talking` events caused visual noise

## Solution Overview

### 1. Replace Pseudo-elements with Real DOM Element

**Before (problematic):**
```css
.portrait-container::before,
.portrait-container::after {
  /* Complex pseudo-element approach */
}
```

**After (Safari-compatible):**
```jsx
<div className="portrait-container">
  <div className={`halo ${isCalling ? 'active' : 'inactive'} ${isAgentSpeaking ? 'speaking' : 'not-speaking'}`}></div>
  <img src="/portrait.png" className="agent-portrait" />
</div>
```

### 2. Use Radial Gradients Instead of Box-shadow

**Before:**
```css
box-shadow: 0 0 20px 10px rgba(255, 255, 255, 0.3);
```

**After:**
```css
background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 60%, transparent 70%);
```

### 3. Add Debounce Mechanism for Speech Events

**Problem:** Rapid `agent_stop_talking` events caused flickering
**Solution:** 400ms debounce delay before hiding green halo

## Implementation Steps

### Step 1: Update React Component Structure

Add halo div element inside portrait container:

```jsx
// In your portrait component JSX:
<div className={`portrait-container ${isCalling ? 'active' : 'inactive'} ${isAgentSpeaking ? 'agent-speaking' : ''}`}>
  <div className={`halo ${isCalling ? 'active' : 'inactive'} ${isAgentSpeaking ? 'speaking' : 'not-speaking'}`}></div>
  <img src="/portrait.png" alt="Agent" className="agent-portrait" />
</div>
```

### Step 2: Implement Halo CSS

```css
.halo {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 1;
  opacity: 0;
  background: none;
  transition: opacity 0.3s ease;
}

/* Grey halo when active but not speaking */
.halo.active.not-speaking {
  background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 60%, transparent 70%);
  opacity: 1;
}

/* Green halo when speaking */
.halo.active.speaking {
  background: radial-gradient(circle, rgba(0, 255, 0, 0.5) 60%, transparent 70%);
  opacity: 1;
  animation: halo-pulse 2.5s infinite ease-in-out;
}

@keyframes halo-pulse {
  0%, 100% {
    background: radial-gradient(circle, rgba(0, 255, 0, 0.4) 60%, transparent 70%);
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    background: radial-gradient(circle, rgba(0, 255, 0, 0.6) 55%, transparent 75%);
    transform: translate(-50%, -50%) scale(1.05);
  }
}
```

### Step 3: Ensure Proper Z-index Stacking

```css
.agent-portrait {
  position: relative;
  z-index: 2;
  /* other styles... */
}
```

### Step 4: Add Debounce Mechanism

```jsx
import React, { useEffect, useState, useRef } from "react";

const YourComponent = () => {
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Agent starts speaking - immediately show green halo
    retellWebClient.on("agent_start_talking", () => {
      // Clear any pending timeout to stop speaking
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = null;
      }
      setIsAgentSpeaking(true);
    });

    // Agent stops speaking - debounce before hiding halo
    retellWebClient.on("agent_stop_talking", () => {
      // Wait 400ms before hiding green halo
      // This prevents flickering on short speech segments
      speakingTimeoutRef.current = setTimeout(() => {
        setIsAgentSpeaking(false);
        speakingTimeoutRef.current = null;
      }, 400);
    });

    retellWebClient.on("call_ended", () => {
      // Clear any pending speaking timeout
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = null;
      }
      setIsAgentSpeaking(false);
    });

    // Cleanup function
    return () => {
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
      }
    };
  }, []);
};
```

## Key Design Decisions

### 1. Why Radial Gradients Over Box-shadow?
- **Cross-browser compatibility**: Gradients render consistently across all browsers
- **Performance**: Less intensive than complex box-shadow calculations
- **Control**: More precise control over gradient stops and transparency

### 2. Why 400ms Debounce Delay?
- **Balance**: Long enough to prevent flickering, short enough to feel responsive
- **Natural speech patterns**: Accounts for brief pauses between words
- **User experience**: Maintains visual continuity during rapid speech

### 3. Why Real DOM Element Over Pseudo-elements?
- **Safari compatibility**: Real elements render consistently
- **Debugging**: Easier to inspect and debug in dev tools
- **Flexibility**: More control over positioning and styling

## State Management

The halo has three distinct states:

1. **Inactive** (`opacity: 0`): No call in progress
2. **Active + Not Speaking** (grey halo): Call active, agent not speaking
3. **Active + Speaking** (green pulsing halo): Agent is currently speaking

## Testing Checklist

When implementing this solution, test:

- [ ] Halos appear as perfect circles on Safari iOS
- [ ] No flickering during normal operation
- [ ] Green halo stays stable during rapid-fire speech segments
- [ ] Green halo disappears after natural pauses (400ms+)
- [ ] No performance issues during long conversations
- [ ] Proper cleanup when call ends
- [ ] Works on both desktop and mobile browsers

## Migration Notes

If migrating from a box-shadow approach:

1. Remove all `::before` and `::after` pseudo-elements related to halos
2. Remove box-shadow rules and animations
3. Add the new halo div to your JSX structure
4. Implement the new CSS rules
5. Add the debounce mechanism to your event handlers
6. Test thoroughly on Safari iOS

## Browser Compatibility

This implementation has been tested and confirmed working on:
- Safari iOS (primary target for fix)
- Safari macOS
- Chrome desktop
- Chrome mobile
- Firefox desktop
- Edge desktop

The radial gradient approach provides consistent rendering across all modern browsers.