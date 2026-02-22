'use client';

import React, { createContext, useContext, useEffect, useCallback } from 'react';

interface ShortcutHandler {
  (): void;
}

interface RTSShortcutsContextType {
  registerShortcut: (key: string, handler: ShortcutHandler) => void;
  unregisterShortcut: (key: string) => void;
}

const RTSShortcutsContext = createContext<RTSShortcutsContextType | null>(null);

export function RTSShortcutProvider({ children }: { children: React.ReactNode }) {
  const shortcuts = React.useRef<Map<string, ShortcutHandler>>(new Map());

  const registerShortcut = useCallback((key: string, handler: ShortcutHandler) => {
    shortcuts.current.set(key, handler);
  }, []);

  const unregisterShortcut = useCallback((key: string) => {
    shortcuts.current.delete(key);
  }, []);

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // Build command key
      let commandKey = '';
      
      if (event.ctrlKey) commandKey += 'Ctrl+';
      if (event.shiftKey) commandKey += 'Shift+';
      if (event.altKey) commandKey += 'Alt+';
      
      commandKey += event.key;

      // Check if shortcut exists
      const handler = shortcuts.current.get(commandKey);
      if (handler) {
        event.preventDefault();
        handler();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <RTSShortcutsContext.Provider value={{ registerShortcut, unregisterShortcut }}>
      {children}
    </RTSShortcutsContext.Provider>
  );
}

export function useRTSShortcuts() {
  const context = useContext(RTSShortcutsContext);
  if (!context) {
    throw new Error('useRTSShortcuts must be used within RTSShortcutProvider');
  }
  return context;
}
