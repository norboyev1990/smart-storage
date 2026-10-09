type BackButton = { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void }

type WebApp = {
  initData: string
  colorScheme: 'light' | 'dark'
  ready(): void
  expand(): void
  BackButton: BackButton
  HapticFeedback?: { notificationOccurred(type: 'error' | 'success' | 'warning'): void }
  showScanQrPopup?(params: { text?: string }, cb: (text: string) => boolean | void): void
}

declare global {
  interface Window {
    Telegram?: { WebApp: WebApp }
  }
}

export const tg: WebApp | undefined = window.Telegram?.WebApp

export function getInitData(): string {
  return tg?.initData || import.meta.env.VITE_DEV_INIT_DATA || ''
}

export function haptic(type: 'error' | 'success' | 'warning') {
  tg?.HapticFeedback?.notificationOccurred(type)
}

export function scanCode(text: string): Promise<string | null> {
  return new Promise((resolve) => {
    if (!tg?.showScanQrPopup) return resolve(null)
    tg.showScanQrPopup({ text }, (value) => {
      resolve(value)
      return true
    })
  })
}
