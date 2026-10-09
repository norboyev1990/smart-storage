import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import type { Client, ClientIn, Page } from '../types'

export type ClientChoice = { client_id: number } | { client: ClientIn } | null

/** Pick an existing client by name/phone, or type a new one. */
export default function ClientSelect({ onChange }: { onChange(choice: ClientChoice): void }) {
  const [q, setQ] = useState('')
  const [phone, setPhone] = useState('')
  const [picked, setPicked] = useState<Client | null>(null)
  const found = useQuery({
    queryKey: ['clients', q],
    queryFn: () => api<Page<Client>>('/clients', { query: { q, limit: 5 } }),
    enabled: q.length >= 2 && !picked,
  })

  if (picked) {
    return (
      <div className="row">
        <span>{picked.full_name} {picked.phone_number && <small className="muted">{picked.phone_number}</small>}</span>
        <button className="link" onClick={() => { setPicked(null); setQ(''); onChange(null) }}>Изменить</button>
      </div>
    )
  }

  const emitNew = (name: string, number: string) =>
    onChange(name ? { client: { full_name: name, phone_number: number || null } } : null)

  return (
    <>
      <input placeholder="Имя клиента" value={q} onChange={(e) => { setQ(e.target.value); emitNew(e.target.value, phone) }} />
      {found.data?.items.map((c) => (
        <button key={c.id} className="list-item" onClick={() => { setPicked(c); onChange({ client_id: c.id }) }}>
          <span>{c.full_name}</span>
          <small className="muted">{c.phone_number}</small>
        </button>
      ))}
      <input placeholder="Телефон клиента (для нового)" value={phone} onChange={(e) => { setPhone(e.target.value); emitNew(q, e.target.value) }} />
    </>
  )
}
