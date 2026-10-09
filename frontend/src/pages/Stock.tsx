import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { money, statusLabel } from '../format'
import { scanCode } from '../telegram'
import type { Page, Phone, PhoneStatus, Warehouse } from '../types'

export default function Stock() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('q') ?? '')
  const status = (params.get('status') ?? '') as PhoneStatus | ''
  const warehouseId = params.get('warehouse_id') ?? ''

  const warehouses = useQuery({ queryKey: ['warehouses'], queryFn: () => api<Warehouse[]>('/warehouses') })
  const phones = useQuery({
    queryKey: ['phones', status, warehouseId, params.get('q')],
    queryFn: () => api<Page<Phone>>('/phones', { query: { status, warehouse_id: warehouseId, q: params.get('q'), limit: 100 } }),
  })

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  const scan = async () => {
    const code = await scanCode('Наведите на штрихкод IMEI')
    if (code) {
      setQ(code)
      update('q', code)
    }
  }

  return (
    <>
      <h1>Склад</h1>
      <div className="search">
        <input
          value={q}
          placeholder="Модель или IMEI"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && update('q', q)}
          onBlur={() => update('q', q)}
        />
        <button className="secondary" onClick={scan}>Скан</button>
      </div>
      <div className="filters">
        <select value={status} onChange={(e) => update('status', e.target.value)}>
          <option value="">Все статусы</option>
          {Object.entries(statusLabel).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        {(warehouses.data?.length ?? 0) > 1 && (
          <select value={warehouseId} onChange={(e) => update('warehouse_id', e.target.value)}>
            <option value="">Все склады</option>
            {warehouses.data!.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        )}
      </div>
      <p className="muted">Найдено: {phones.data?.total ?? '…'}</p>
      <div className="card">
        {phones.data?.items.map((p) => (
          <Link key={p.id} to={`/phones/${p.id}`} className="list-item">
            <span>
              <b>{p.brand} {p.model}</b> {p.storage_gb ? `${p.storage_gb} ГБ` : ''}
              <br />
              <small className="muted">IMEI {p.imei1}</small>
            </span>
            <span className="right">
              <span className={`badge ${p.status}`}>{statusLabel[p.status]}</span>
              <br />
              <small>{money(p.asking_price, p.asking_currency)}</small>
            </span>
          </Link>
        ))}
        {phones.data?.items.length === 0 && <p className="muted pad">Ничего не найдено</p>}
      </div>
    </>
  )
}
