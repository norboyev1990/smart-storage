import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { conditionLabel, date, money, paymentLabel, statusLabel } from '../format'
import { ErrorText, Row, Section } from '../components/ui'
import { useCanSeeProfit } from '../session'
import type { Currency, PhoneDetail } from '../types'

export default function PhonePage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const canSeeCost = useCanSeeProfit()
  const phone = useQuery({ queryKey: ['phone', id], queryFn: () => api<PhoneDetail>(`/phones/${id}`) })
  const [expense, setExpense] = useState({ amount: '', description: '' })

  const refresh = () => queryClient.invalidateQueries()
  const addExpense = useMutation({
    mutationFn: () =>
      api(`/phones/${id}/expenses`, {
        body: { ...expense, currency: (phone.data?.purchase?.currency ?? 'UZS') as Currency },
      }),
    onSuccess: () => {
      setExpense({ amount: '', description: '' })
      refresh()
    },
  })
  const cancelSale = useMutation({
    mutationFn: (saleId: number) => api(`/sales/${saleId}/cancel`, { body: { reason: 'Возврат' } }),
    onSuccess: refresh,
  })

  const p = phone.data
  if (phone.isError) return <p className="error">{phone.error.message}</p>
  if (!p) return <div className="center muted">Загрузка…</div>
  const activeSale = p.sales.find((s) => !s.is_cancelled)

  return (
    <>
      <h1>{p.brand} {p.model}</h1>
      <p><span className={`badge ${p.status}`}>{statusLabel[p.status]}</span></p>
      {(p.status === 'in_stock' || p.status === 'reserved') && (
        <Link className="primary big" to={`/phones/${p.id}/sell`}>Продать</Link>
      )}
      <Section title="Характеристики">
        <Row label="IMEI 1" value={p.imei1} />
        {p.imei2 && <Row label="IMEI 2" value={p.imei2} />}
        {p.storage_gb && <Row label="Память" value={`${p.storage_gb} ГБ`} />}
        {p.color && <Row label="Цвет" value={p.color} />}
        <Row label="Состояние" value={conditionLabel[p.condition]} />
        {p.battery_health !== null && <Row label="Батарея" value={`${p.battery_health}%`} />}
        {p.kit && <Row label="Комплект" value={p.kit} />}
        <Row label="Цена продажи (план)" value={money(p.asking_price, p.asking_currency)} />
        {p.notes && <p>{p.notes}</p>}
      </Section>
      {p.purchase && (
        <Section title="Покупка">
          <Row label="Дата" value={date(p.purchase.purchased_at)} />
          {canSeeCost && <Row label="Цена" value={money(p.purchase.price, p.purchase.currency)} />}
          <Row label="Оплата" value={paymentLabel[p.purchase.payment_method]} />
          <Row label="Продавец" value={p.purchase.client?.full_name ?? '—'} />
        </Section>
      )}
      {canSeeCost && (
        <Section title="Расходы">
          {p.expenses.map((e) => (
            <Row key={e.id} label={e.description} value={money(e.amount, e.currency)} />
          ))}
          <div className="grid2">
            <input placeholder="Что сделано" value={expense.description} onChange={(e) => setExpense({ ...expense, description: e.target.value })} />
            <input placeholder="Сумма" inputMode="decimal" value={expense.amount} onChange={(e) => setExpense({ ...expense, amount: e.target.value })} />
          </div>
          <button className="secondary" disabled={!expense.amount || !expense.description} onClick={() => addExpense.mutate()}>
            Добавить расход
          </button>
          <ErrorText error={addExpense.error} />
        </Section>
      )}
      {p.sales.length > 0 && (
        <Section title="Продажи">
          {p.sales.map((s) => (
            <div key={s.id} className={s.is_cancelled ? 'cancelled' : ''}>
              <Row label={date(s.sold_at)} value={money(s.price, s.currency)} />
              <Row label="Покупатель" value={s.client?.full_name ?? '—'} />
              {s.warranty_days > 0 && <Row label="Гарантия" value={`${s.warranty_days} дн.`} />}
              {s.is_cancelled && <p className="muted">Отменена: {s.cancelled_reason}</p>}
            </div>
          ))}
          {activeSale && canSeeCost && (
            <button className="danger" onClick={() => confirm('Оформить возврат?') && cancelSale.mutate(activeSale.id)}>
              Оформить возврат
            </button>
          )}
          <ErrorText error={cancelSale.error} />
        </Section>
      )}
    </>
  )
}
