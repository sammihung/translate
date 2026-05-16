import { useState } from 'react'

interface Bubble {
  id: string
  speaker: string
  original: string
  translated: string
  speakerId: number
  time: string
}

const MAX_BUBBLES = 100

export function useChat() {
  const [bubbles, setBubbles] = useState<Bubble[]>([])

  const addBubble = (data: {
    bubble_id: string
    original: string
    translated: string
    speaker_id: number
  }) => {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`

    setBubbles((prev: Bubble[]) => {
      const newBubbles = [
        ...prev,
        {
          id: data.bubble_id,
          speaker: data.speaker_id === 1 ? 'Speaker #1' : 'Speaker #2',
          original: data.original,
          translated: data.translated,
          speakerId: data.speaker_id,
          time,
        },
      ]
      return newBubbles.length > MAX_BUBBLES
        ? newBubbles.slice(newBubbles.length - MAX_BUBBLES)
        : newBubbles
    })
  }

  const updateBubble = (data: { bubble_id: string; translated: string }) => {
    setBubbles((prev: Bubble[]) =>
      prev.map((b: Bubble) =>
        b.id === data.bubble_id ? { ...b, translated: data.translated } : b
      )
    )
  }

  const clearBubbles = () => setBubbles([])

  return { bubbles, addBubble, updateBubble, clearBubbles }
}