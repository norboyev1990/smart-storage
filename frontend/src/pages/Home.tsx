import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Row, Section, Totals } from '../components/ui'
import { useSession } from '../session'
import type { Summary } from '../types'

function monthStart() {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString()
}

export default function Home() {
  const { current, user } = useSession()
  const summary = useQuery({
    queryKey: ['summary', 'month'],
    queryFn: () => api<Summary>('/reports/summary', { query: { date_from: monthStart() } }),
  })
  const s = summary.data

  return (
    <>
      <h1>{current.shop.name}</h1>
      <p className="muted">Здравствуйте, {user.first_name}</p>
      <div className="actions">
        <Link className="primary big" to="/phones/new">＋ Принять телефон</Link>
        <Link className="secondary big" to="/stock?status=in_stock">Продать</Link>
      </div>
      <Section title="Склад">
        <Row label="Телефонов на складе" value={s?.in_stock_count ?? '…'} />
        {s?.profit !== null && <Row label="Себестоимость" value={<Totals items={s?.in_stock_cost} />} />}
      </Section>
      <Section title="Этот месяц">
        <Row label="Продано" value={s?.sold_count ?? '…'} />
        <Row label="Выручка" value={<Totals items={s?.revenue} />} />
        {s?.profit !== null && <Row label="Прибыль" value={<Totals items={s?.profit} />} />}
      </Section>
    </>
  )
}
