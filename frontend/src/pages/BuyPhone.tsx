import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { conditionLabel, paymentLabel } from '../format'
import { haptic, scanCode } from '../telegram'
import ClientSelect, { type ClientChoice } from '../components/ClientSelect'
import { ErrorText, Field, Section } from '../components/ui'
import { useSession } from '../session'
import type { Condition, Currency, PaymentMethod, PhoneDetail, Warehouse } from '../types'

export default function BuyPhone() {
  const { current } = useSession()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const warehouses = useQuery({ queryKey: ['warehouses'], queryFn: () => api<Warehouse[]>('/warehouses') })

  const [form, setForm] = useState({
    warehouse_id: '',
    brand: '',
    model: '',
    storage_gb: '',
    color: '',
    imei1: '',
    imei2: '',
    condition: 'good' as Condition,
    battery_health: '',
    kit: '',
    notes: '',
    asking_price: '',
    price: '',
    currency: current.shop.default_currency as Currency,
    payment_method: 'cash' as PaymentMethod,
  })
  const [client, setClient] = useState<ClientChoice>(null)
  const set = (key: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [key]: e.target.value })
  const warehouseId = form.warehouse_id || String(warehouses.data?.find((w) => w.is_active)?.id ?? '')

  const save = useMutation({
    mutationFn: () =>
      api<PhoneDetail>('/phones', {
        body: {
          warehouse_id: Number(warehouseId),
          brand: form.brand,
          model: form.model,
          storage_gb: form.storage_gb ? Number(form.storage_gb) : null,
          color: form.color || null,
          imei1: form.imei1,
          imei2: form.imei2 || null,
          condition: form.condition,
          battery_health: form.battery_health ? Number(form.battery_health) : null,
          kit: form.kit || null,
          notes: form.notes || null,
          asking_price: form.asking_price || null,
          asking_currency: form.asking_price ? form.currency : null,
          purchase: { price: form.price, currency: form.currency, payment_method: form.payment_method, ...(client ?? {}) },
        },
      }),
    onSuccess: (phone) => {
      haptic('success')
      queryClient.invalidateQueries()
      navigate(`/phones/${phone.id}`, { replace: true })
    },
    onError: () => haptic('error'),
  })

  const scan = async () => {
    const code = await scanCode('Наведите на штрихкод IMEI')
    if (code) setForm({ ...form, imei1: code.replace(/\D/g, '') })
  }

  const valid = form.brand && form.model && form.imei1.length >= 8 && form.price && warehouseId

  return (
    <>
      <h1>Принять телефон</h1>
      <Section title="Телефон">
        <Field label="Бренд"><input value={form.brand} onChange={set('brand')} placeholder="Apple, Samsung…" /></Field>
        <Field label="Модель"><input value={form.model} onChange={set('model')} placeholder="iPhone 13" /></Field>
        <div className="grid2">
          <Field label="Память, ГБ"><input inputMode="numeric" value={form.storage_gb} onChange={set('storage_gb')} /></Field>
          <Field label="Цвет"><input value={form.color} onChange={set('color')} /></Field>
        </div>
        <Field label="IMEI 1">
          <div className="search">
            <input inputMode="numeric" value={form.imei1} onChange={set('imei1')} />
            <button className="secondary" onClick={scan}>Скан</button>
          </div>
        </Field>
        <Field label="IMEI 2"><input inputMode="numeric" value={form.imei2} onChange={set('imei2')} /></Field>
        <div className="grid2">
          <Field label="Состояние">
            <select value={form.condition} onChange={set('condition')}>
              {Object.entries(conditionLabel).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </Field>
          <Field label="Батарея, %"><input inputMode="numeric" value={form.battery_health} onChange={set('battery_health')} /></Field>
        </div>
        <Field label="Комплект"><input value={form.kit} onChange={set('kit')} placeholder="коробка, зарядка" /></Field>
        <Field label="Заметки"><textarea value={form.notes} onChange={set('notes')} /></Field>
        {(warehouses.data?.length ?? 0) > 1 && (
          <Field label="Склад">
            <select value={warehouseId} onChange={set('warehouse_id')}>
              {warehouses.data!.filter((w) => w.is_active).map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </Field>
        )}
      </Section>
      <Section title="Покупка">
        <div className="grid2">
          <Field label="Цена покупки"><input inputMode="decimal" value={form.price} onChange={set('price')} /></Field>
          <Field label="Валюта">
            <select value={form.currency} onChange={set('currency')}>
              <option value="UZS">UZS</option>
              <option value="USD">USD</option>
            </select>
          </Field>
        </div>
        <Field label="Оплата">
          <select value={form.payment_method} onChange={set('payment_method')}>
            {Object.entries(paymentLabel).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>
        <Field label="Цена продажи (план)"><input inputMode="decimal" value={form.asking_price} onChange={set('asking_price')} /></Field>
      </Section>
      <Section title="Продавец (клиент)">
        <ClientSelect onChange={setClient} />
      </Section>
      <ErrorText error={save.error} />
      <button className="primary big" disabled={!valid || save.isPending} onClick={() => save.mutate()}>
        Сохранить
      </button>
    </>
  )
}
