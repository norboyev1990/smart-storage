import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { api, getShopId, setShopId, setToken } from './api'
import { getInitData, tg } from './telegram'
import { SessionContext } from './session'
import type { MyShop, User } from './types'
import Home from './pages/Home'
import Stock from './pages/Stock'
import PhonePage from './pages/PhonePage'
import BuyPhone from './pages/BuyPhone'
import SellPhone from './pages/SellPhone'
import Reports from './pages/Reports'
import Clients from './pages/Clients'
import Settings from './pages/Settings'
import ShopPicker from './pages/ShopPicker'

function useLogin() {
  return useQuery({
    queryKey: ['login'],
    queryFn: async () => {
      const initData = getInitData()
      if (!initData) throw new Error('Откройте приложение через Telegram')
      const res = await api<{ access_token: string; user: User }>('/auth/telegram', { body: { init_data: initData } })
      setToken(res.access_token)
      return res.user
    },
    staleTime: Infinity,
    retry: false,
  })
}

function useTelegramBackButton() {
  const location = useLocation()
  const navigate = useNavigate()
  useEffect(() => {
    if (!tg) return
    const back = () => navigate(-1)
    if (location.pathname === '/') tg.BackButton.hide()
    else tg.BackButton.show()
    tg.BackButton.onClick(back)
    return () => tg?.BackButton.offClick(back)
  }, [location.pathname, navigate])
}

export default function App() {
  const login = useLogin()
  const queryClient = useQueryClient()
  const [shopId, setShop] = useState(getShopId())
  const shops = useQuery({ queryKey: ['shops'], queryFn: () => api<MyShop[]>('/shops'), enabled: login.isSuccess })
  useTelegramBackButton()

  if (login.isPending || (login.isSuccess && shops.isPending)) return <div className="center muted">Загрузка…</div>
  if (login.isError) return <div className="center error">{login.error.message}</div>
  if (shops.isError) return <div className="center error">{shops.error.message}</div>

  const switchShop = (id: number | null) => {
    setShopId(id)
    setShop(id)
    queryClient.removeQueries({ predicate: (q) => !['login', 'shops'].includes(q.queryKey[0] as string) })
  }
  const current = shops.data!.find((s) => s.shop.id === shopId)
  if (!current) return <ShopPicker shops={shops.data!} onPick={switchShop} />

  return (
    <SessionContext.Provider value={{ user: login.data!, current, shops: shops.data!, switchShop }}>
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/stock" element={<Stock />} />
          <Route path="/phones/new" element={<BuyPhone />} />
          <Route path="/phones/:id" element={<PhonePage />} />
          <Route path="/phones/:id/sell" element={<SellPhone />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
      <nav className="tabbar">
        <NavLink to="/" end>Главная</NavLink>
        <NavLink to="/stock">Склад</NavLink>
        <NavLink to="/reports">Отчёты</NavLink>
        <NavLink to="/clients">Клиенты</NavLink>
        <NavLink to="/settings">Ещё</NavLink>
      </nav>
    </SessionContext.Provider>
  )
}
