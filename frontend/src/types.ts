export type Currency = 'UZS' | 'USD'
export type Role = 'owner' | 'manager' | 'seller'
export type PhoneStatus = 'in_stock' | 'reserved' | 'sold' | 'returned' | 'written_off'
export type Condition = 'new' | 'excellent' | 'good' | 'fair' | 'broken'
export type PaymentMethod = 'cash' | 'card' | 'transfer'

export interface User { id: number; telegram_id: number; first_name: string; last_name: string | null; username: string | null }
export interface Shop { id: number; name: string; default_currency: Currency }
export interface MyShop { shop: Shop; role: Role }
export interface Member { id: number; role: Role; is_active: boolean; user: User }
export interface Warehouse { id: number; name: string; address: string | null; is_active: boolean }
export interface Client { id: number; full_name: string; phone_number: string | null; document: string | null; notes: string | null }
export interface ClientIn { full_name: string; phone_number?: string | null }

export interface Phone {
  id: number
  warehouse_id: number
  brand: string
  model: string
  storage_gb: number | null
  ram_gb: number | null
  color: string | null
  imei1: string
  imei2: string | null
  condition: Condition
  battery_health: number | null
  kit: string | null
  notes: string | null
  status: PhoneStatus
  asking_price: string | null
  asking_currency: Currency | null
  created_at: string
}

export interface Purchase { id: number; client: Client | null; price: string; currency: Currency; payment_method: PaymentMethod; purchased_at: string }
export interface Sale {
  id: number; client: Client | null; price: string; currency: Currency; payment_method: PaymentMethod
  warranty_days: number; sold_at: string; is_cancelled: boolean; cancelled_reason: string | null
}
export interface Expense { id: number; amount: string; currency: Currency; description: string; created_at: string }
export interface PhoneDetail extends Phone { purchase: Purchase | null; sales: Sale[]; expenses: Expense[] }

export interface Page<T> { items: T[]; total: number }
export interface MoneyTotal { currency: Currency; amount: string }
export interface Summary { in_stock_count: number; in_stock_cost: MoneyTotal[]; sold_count: number; revenue: MoneyTotal[]; profit: MoneyTotal[] | null }
export interface SoldRow { sale_id: number; phone_id: number; brand: string; model: string; imei1: string; sold_at: string; price: string; currency: Currency; cost: string | null; profit: string | null }
export interface InStockRow { phone_id: number; brand: string; model: string; imei1: string; warehouse_id: number; days_in_stock: number; cost: string | null; currency: Currency | null; asking_price: string | null; asking_currency: Currency | null }
