import { createContext, useContext } from 'react'
import type { MyShop, User } from './types'

export interface Session {
  user: User
  current: MyShop
  shops: MyShop[]
  switchShop(id: number | null): void
}

export const SessionContext = createContext<Session | null>(null)

export function useSession(): Session {
  const value = useContext(SessionContext)
  if (!value) throw new Error('SessionContext is missing')
  return value
}

export function useCanSeeProfit() {
  return useSession().current.role !== 'seller'
}
