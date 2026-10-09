import type { ReactNode } from 'react'
import type { MoneyTotal } from '../types'
import { money } from '../format'

export function Section({ title, children, action }: { title?: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="section">
      {(title || action) && (
        <div className="section-head">
          <h2>{title}</h2>
          {action}
        </div>
      )}
      <div className="card">{children}</div>
    </section>
  )
}

export function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="row">
      <span className="muted">{label}</span>
      <span>{value}</span>
    </div>
  )
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  )
}

export function Totals({ items }: { items: MoneyTotal[] | null | undefined }) {
  if (!items || items.length === 0) return <>—</>
  return <>{items.map((t) => money(t.amount, t.currency)).join(' + ')}</>
}

export function ErrorText({ error }: { error: Error | null }) {
  return error ? <p className="error">{error.message}</p> : null
}
