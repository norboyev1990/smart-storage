import type { Condition, Currency, PaymentMethod, PhoneStatus, Role } from './types'

export function money(amount: string | number | null | undefined, currency: Currency | null | undefined) {
  if (amount === null || amount === undefined || !currency) return '—'
  const value = Number(amount)
  return `${value.toLocaleString('ru-RU', { maximumFractionDigits: currency === 'USD' ? 2 : 0 })} ${currency === 'USD' ? '$' : 'сум'}`
}

export function date(value: string) {
  return new Date(value).toLocaleDateString('ru-RU')
}

export const statusLabel: Record<PhoneStatus, string> = {
  in_stock: 'На складе',
  reserved: 'Бронь',
  sold: 'Продан',
  returned: 'Возврат',
  written_off: 'Списан',
}

export const conditionLabel: Record<Condition, string> = {
  new: 'Новый',
  excellent: 'Отличное',
  good: 'Хорошее',
  fair: 'Среднее',
  broken: 'Неисправен',
}

export const paymentLabel: Record<PaymentMethod, string> = { cash: 'Наличные', card: 'Карта', transfer: 'Перевод' }

export const roleLabel: Record<Role, string> = { owner: 'Владелец', manager: 'Менеджер', seller: 'Продавец' }
