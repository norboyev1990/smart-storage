import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { roleLabel } from '../format'
import { ErrorText, Field, Row, Section } from '../components/ui'
import { useSession } from '../session'
import type { Member, Role, Warehouse } from '../types'

export default function Settings() {
  const { current, user, shops, switchShop } = useSession()
  const queryClient = useQueryClient()
  const isOwner = current.role === 'owner'
  const isManager = current.role !== 'seller'

  const warehouses = useQuery({ queryKey: ['warehouses'], queryFn: () => api<Warehouse[]>('/warehouses') })
  const members = useQuery({ queryKey: ['members'], queryFn: () => api<Member[]>('/members'), enabled: isManager })

  const [warehouseName, setWarehouseName] = useState('')
  const addWarehouse = useMutation({
    mutationFn: () => api('/warehouses', { body: { name: warehouseName } }),
    onSuccess: () => {
      setWarehouseName('')
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
    },
  })

  const [newMember, setNewMember] = useState({ telegram_id: '', first_name: '', role: 'seller' as Role })
  const addMember = useMutation({
    mutationFn: () => api('/members', { body: { ...newMember, telegram_id: Number(newMember.telegram_id) } }),
    onSuccess: () => {
      setNewMember({ telegram_id: '', first_name: '', role: 'seller' })
      queryClient.invalidateQueries({ queryKey: ['members'] })
    },
  })
  const toggleMember = useMutation({
    mutationFn: (m: Member) => api(`/members/${m.id}`, { method: 'PATCH', body: { is_active: !m.is_active } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] }),
  })

  return (
    <>
      <h1>Настройки</h1>
      <Section title="Профиль">
        <Row label="Имя" value={user.first_name} />
        <Row label="Telegram ID" value={user.telegram_id} />
        <Row label="Роль" value={roleLabel[current.role]} />
      </Section>

      <Section title="Магазин" action={<button className="link" onClick={() => switchShop(null)}>{shops.length > 1 ? "Сменить" : "Новый магазин"}</button>}>
        <Row label="Название" value={current.shop.name} />
        <Row label="Валюта" value={current.shop.default_currency} />
      </Section>

      <Section title="Склады">
        {warehouses.data?.map((w) => <Row key={w.id} label={w.name} value={w.address ?? ''} />)}
        {isManager && (
          <>
            <input placeholder="Название нового склада" value={warehouseName} onChange={(e) => setWarehouseName(e.target.value)} />
            <button className="secondary" disabled={!warehouseName} onClick={() => addWarehouse.mutate()}>Добавить склад</button>
            <ErrorText error={addWarehouse.error} />
          </>
        )}
      </Section>

      {isManager && (
        <Section title="Сотрудники">
          {members.data?.map((m) => (
            <div key={m.id} className={`row ${m.is_active ? '' : 'cancelled'}`}>
              <span>
                {m.user.first_name || `ID ${m.user.telegram_id}`} <small className="muted">{roleLabel[m.role]}</small>
              </span>
              {isOwner && m.user.id !== user.id && (
                <button className="link" onClick={() => toggleMember.mutate(m)}>{m.is_active ? 'Отключить' : 'Включить'}</button>
              )}
            </div>
          ))}
          {isOwner && (
            <>
              <Field label="Telegram ID сотрудника">
                <input inputMode="numeric" value={newMember.telegram_id} onChange={(e) => setNewMember({ ...newMember, telegram_id: e.target.value })} />
              </Field>
              <div className="grid2">
                <input placeholder="Имя" value={newMember.first_name} onChange={(e) => setNewMember({ ...newMember, first_name: e.target.value })} />
                <select value={newMember.role} onChange={(e) => setNewMember({ ...newMember, role: e.target.value as Role })}>
                  <option value="seller">Продавец</option>
                  <option value="manager">Менеджер</option>
                  <option value="owner">Владелец</option>
                </select>
              </div>
              <button className="secondary" disabled={!newMember.telegram_id} onClick={() => addMember.mutate()}>Добавить сотрудника</button>
              <ErrorText error={addMember.error} />
            </>
          )}
        </Section>
      )}
    </>
  )
}
