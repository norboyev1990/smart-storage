import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import type { Client, Page } from '../types'

export default function Clients() {
  const [q, setQ] = useState('')
  const clients = useQuery({
    queryKey: ['clients', 'list', q],
    queryFn: () => api<Page<Client>>('/clients', { query: { q, limit: 100 } }),
  })

  return (
    <>
      <h1>Клиенты</h1>
      <input placeholder="Имя или телефон" value={q} onChange={(e) => setQ(e.target.value)} />
      <p className="muted">Всего: {clients.data?.total ?? '…'}</p>
      <div className="card">
        {clients.data?.items.map((c) => (
          <div key={c.id} className="list-item">
            <span>{c.full_name}</span>
            <a className="muted" href={c.phone_number ? `tel:${c.phone_number}` : undefined}>{c.phone_number}</a>
          </div>
        ))}
      </div>
    </>
  )
}
