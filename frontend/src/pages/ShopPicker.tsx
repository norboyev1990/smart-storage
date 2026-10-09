import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { roleLabel } from '../format'
import { ErrorText, Field, Section } from '../components/ui'
import type { Currency, MyShop, Shop } from '../types'

export default function ShopPicker({ shops, onPick }: { shops: MyShop[]; onPick(id: number): void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [currency, setCurrency] = useState<Currency>('UZS')
  const create = useMutation({
    mutationFn: () => api<Shop>('/shops', { body: { name, default_currency: currency } }),
    onSuccess: async (shop) => {
      await queryClient.invalidateQueries({ queryKey: ['shops'] })
      onPick(shop.id)
    },
  })

  return (
    <main className="page">
      <h1>Smart Storage</h1>
      {shops.length > 0 && (
        <Section title="Ваши магазины">
          {shops.map((s) => (
            <button key={s.shop.id} className="list-item" onClick={() => onPick(s.shop.id)}>
              <span>{s.shop.name}</span>
              <span className="muted">{roleLabel[s.role]}</span>
            </button>
          ))}
        </Section>
      )}
      <Section title="Новый магазин">
        <Field label="Название">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Например, Phone Market" />
        </Field>
        <Field label="Основная валюта">
          <select value={currency} onChange={(e) => setCurrency(e.target.value as Currency)}>
            <option value="UZS">UZS</option>
            <option value="USD">USD</option>
          </select>
        </Field>
        <button className="primary" disabled={!name || create.isPending} onClick={() => create.mutate()}>
          Создать магазин
        </button>
        <ErrorText error={create.error} />
      </Section>
      {shops.length === 0 && (
        <p className="muted">Если вы сотрудник, попросите владельца магазина добавить вас по Telegram ID.</p>
      )}
    </main>
  )
}
