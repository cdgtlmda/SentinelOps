"use client"

import { useState, useEffect, useCallback } from 'react'

interface PanelState {
  leftWidth: number
  leftCollapsed: boolean
  rightCollapsed: boolean
  activePanel: 'left' | 'right'
}

const STORAGE_KEY_PREFIX = 'sentinelops-panel-state'

export function usePanelState(
  leftPanelId: string,
  rightPanelId: string,
  defaultLeftWidth: number = 50
) {
  const storageKey = `${STORAGE_KEY_PREFIX}-${leftPanelId}-${rightPanelId}`
  
  // Initialize state from localStorage or defaults
  const [state, setState] = useState<PanelState>(() => {
    if (typeof window === 'undefined') {
      return {
        leftWidth: defaultLeftWidth,
        leftCollapsed: false,
        rightCollapsed: false,
        activePanel: 'left'
      }
    }
    
    try {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.warn('Failed to load panel state from localStorage:', error)
    }
    
    return {
      leftWidth: defaultLeftWidth,
      leftCollapsed: false,
      rightCollapsed: false,
      activePanel: 'left'
    }
  })

  // Save state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    try {
      localStorage.setItem(storageKey, JSON.stringify(state))
    } catch (error) {
      console.warn('Failed to save panel state to localStorage:', error)
    }
  }, [state, storageKey])

  // Update functions
  const setLeftWidth = useCallback((width: number) => {
    setState(prev => ({ ...prev, leftWidth: width }))
  }, [])

  const toggleLeftPanel = useCallback(() => {
    setState(prev => {
      // If both panels are collapsed, ensure right panel opens when left closes
      if (!prev.leftCollapsed && prev.rightCollapsed) {
        return { ...prev, leftCollapsed: true, rightCollapsed: false }
      }
      return { ...prev, leftCollapsed: !prev.leftCollapsed }
    })
  }, [])

  const toggleRightPanel = useCallback(() => {
    setState(prev => {
      // If both panels are collapsed, ensure left panel opens when right closes
      if (!prev.rightCollapsed && prev.leftCollapsed) {
        return { ...prev, rightCollapsed: true, leftCollapsed: false }
      }
      return { ...prev, rightCollapsed: !prev.rightCollapsed }
    })
  }, [])

  const setActivePanel = useCallback((panel: 'left' | 'right') => {
    setState(prev => ({ ...prev, activePanel: panel }))
  }, [])

  const resetLayout = useCallback(() => {
    setState({
      leftWidth: defaultLeftWidth,
      leftCollapsed: false,
      rightCollapsed: false,
      activePanel: 'left'
    })
  }, [defaultLeftWidth])

  return {
    leftWidth: state.leftWidth,
    leftCollapsed: state.leftCollapsed,
    rightCollapsed: state.rightCollapsed,
    activePanel: state.activePanel,
    setLeftWidth,
    toggleLeftPanel,
    toggleRightPanel,
    setActivePanel,
    resetLayout
  }
}