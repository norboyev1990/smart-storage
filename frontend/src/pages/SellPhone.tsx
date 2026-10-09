import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { money, paymentLabel } from '../format'
import { haptic } from '../telegram'
import ClientSelect, { type ClientChoice } from '../components/ClientSelect'
import { ErrorText, Field, Section } from '../components/ui'
import type { Currency, PaymentMethod, PhoneDetail, Sale } from '../types'

export default function SellPhone() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const phone = useQuery({ queryKey: ['phone', id], queryFn: () => api<PhoneDetail>(`/phones/${id}`) })
  const [price, setPrice] = useState('')
  const [currency, setCurrency] = useState<Currency | ''>('')
  const [payment, setPayment] = useState<PaymentMethod>('cash')
  const [warranty, setWarranty] = useState('0')
  const [client, setClient] = useState<ClientChoice>(null)

  const p = phone.data
  const cur = currency || p?.asking_currency || p?.purchase?.currency || 'UZS'
  const sell = useMutation({
    mutationFn: () =>
      api<Sale>(`/phones/${id}/sell`, {
        body: { price: price || p?.asking_price, currency: cur, payment_method: payment, warranty_days: Number(warranty), ...(client ?? {}) },
      }),
    onSuccess: () => {
      haptic('success')
      queryClient.invalidateQueries()
      navigate(`/phones/${id}`, { replace: true })
    },
    onError: () => haptic('error'),
  })

  if (!p) return <div className="center muted">Загрузка…</div>

  return (
    <>
      <h1>Продажа</h1>
      <p><b>{p.brand} {p.model}</b> · IMEI {p.imei1}</p>
      <Section title="Оплата">
        <div className="grid2">
          <Field label="Цена">
            <input inputMode="decimal" value={price} placeholder={p.asking_price ?? ''} onChange={(e) => setPrice(e.target.value)} />
          </Field>
          <Field label="Валюта">
            <select value={cur} onChange={(e) => setCurrency(e.target.value as Currency)}>
              <option value="UZS">UZS</option>
              <option value="USD">USD</option>
            </select>
          </Field>
        </div>
        {p.asking_price && <p className="muted">План: {money(p.asking_price, p.asking_currency)}</p>}
        <Field label="Способ оплаты">
          <select value={payment} onChange={(e) => setPayment(e.target.value as PaymentMethod)}>
            {Object.entries(paymentLabel).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>
        <Field label="Гарантия, дней"><input inputMode="numeric" value={warranty} onChange={(e) => setWarranty(e.target.value)} /></Field>
      </Section>
      <Section title="Покупатель (необязательно)">
        <ClientSelect onChange={setClient} />
      </Section>
      <ErrorText error={sell.error} />
      <button className="primary big" disabled={!(price || p.asking_price) || sell.isPending} onClick={() => sell.mutate()}>
        Продать
      </button>
    </>
  )
}
