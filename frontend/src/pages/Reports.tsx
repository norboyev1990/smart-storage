import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { date, money } from '../format'
import { Field, Row, Section, Totals } from '../components/ui'
import { useCanSeeProfit } from '../session'
import type { InStockRow, SoldRow, Summary } from '../types'

function isoDay(d: Date) {
  return d.toISOString().slice(0, 10)
}

export default function Reports() {
  const canSeeProfit = useCanSeeProfit()
  const [tab, setTab] = useState<'sold' | 'stock'>('sold')
  const [from, setFrom] = useState(() => {
    const today = new Date()
    return isoDay(new Date(today.getFullYear(), today.getMonth(), 1))
  })
  const [to, setTo] = useState(() => isoDay(new Date()))
  const [minDays, setMinDays] = useState('0')

  const range = { date_from: `${from}T00:00:00`, date_to: `${to}T23:59:59` }
  const summary = useQuery({ queryKey: ['summary', from, to], queryFn: () => api<Summary>('/reports/summary', { query: range }) })
  const sold = useQuery({ queryKey: ['sold', from, to], queryFn: () => api<SoldRow[]>('/reports/sold', { query: range }), enabled: tab === 'sold' })
  const stock = useQuery({
    queryKey: ['in-stock', minDays],
    queryFn: () => api<InStockRow[]>('/reports/in-stock', { query: { min_days: minDays } }),
    enabled: tab === 'stock',
  })

  return (
    <>
      <h1>Отчёты</h1>
      <div className="tabs">
        <button className={tab === 'sold' ? 'active' : ''} onClick={() => setTab('sold')}>Проданные</button>
        <button className={tab === 'stock' ? 'active' : ''} onClick={() => setTab('stock')}>Непроданные</button>
      </div>

      {tab === 'sold' && (
        <>
          <div className="grid2">
            <Field label="С"><input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
            <Field label="По"><input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></Field>
          </div>
          <Section>
            <Row label="Продано" value={summary.data?.sold_count ?? '…'} />
            <Row label="Выручка" value={<Totals items={summary.data?.revenue} />} />
            {canSeeProfit && <Row label="Прибыль" value={<Totals items={summary.data?.profit} />} />}
          </Section>
          <div className="card">
            {sold.data?.map((r) => (
              <Link key={r.sale_id} to={`/phones/${r.phone_id}`} className="list-item">
                <span>
                  <b>{r.brand} {r.model}</b>
                  <br />
                  <small className="muted">{date(r.sold_at)} · {r.imei1}</small>
                </span>
                <span className="right">
                  {money(r.price, r.currency)}
                  {canSeeProfit && r.profit !== null && (
                    <><br /><small className={Number(r.profit) >= 0 ? 'ok' : 'error'}>{money(r.profit, r.currency)}</small></>
                  )}
                </span>
              </Link>
            ))}
            {sold.data?.length === 0 && <p className="muted pad">Нет продаж за период</p>}
          </div>
        </>
      )}

      {tab === 'stock' && (
        <>
          <Field label="На складе не меньше, дней">
            <input inputMode="numeric" value={minDays} onChange={(e) => setMinDays(e.target.value || '0')} />
          </Field>
          <Section>
            <Row label="Телефонов" value={stock.data?.length ?? '…'} />
            {canSeeProfit && <Row label="Себестоимость склада" value={<Totals items={summary.data?.in_stock_cost} />} />}
          </Section>
          <div className="card">
            {stock.data?.map((r) => (
              <Link key={r.phone_id} to={`/phones/${r.phone_id}`} className="list-item">
                <span>
                  <b>{r.brand} {r.model}</b>
                  <br />
                  <small className="muted">{r.imei1}</small>
                </span>
                <span className="right">
                  {r.days_in_stock} дн.
                  <br />
                  <small className="muted">{canSeeProfit ? money(r.cost, r.currency) : money(r.asking_price, r.asking_currency)}</small>
                </span>
              </Link>
            ))}
            {stock.data?.length === 0 && <p className="muted pad">Склад пуст</p>}
          </div>
        </>
      )}
    </>
  )
}
