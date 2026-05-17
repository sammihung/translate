import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = `ws://127.0.0.1:8000/ws`

interface WsMessage {
  type: string
  [key: string]: unknown
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)
  const listenersRef = useRef<Map<string, (data: WsMessage) => void>>(new Map())

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      setConnected(true)
      console.log('[WS] Connected')
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('[WS] Disconnected, reconnecting in 3s...')
      setTimeout(connect, 3000)
    }

    ws.onerror = (err) => {
      console.error('[WS] Error:', err)
      ws.close()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsMessage
        if (data.type === 'audio_level') {
          console.log('[WS] audio_level:', data.level)
        }
        setLastMessage(data)

        const listener = listenersRef.current.get(data.type)
        if (listener) {
          listener(data)
        } else {
          console.warn('[WS] No listener for type:', data.type)
        }
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    wsRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('[WS] Cannot send - WebSocket not connected, message dropped:', data)
    }
  }, [])

  const on = useCallback((type: string, handler: (data: WsMessage) => void) => {
    listenersRef.current.set(type, handler)
  }, [])

  const off = useCallback((type: string) => {
    listenersRef.current.delete(type)
  }, [])

  return { connected, lastMessage, send, on, off }
}