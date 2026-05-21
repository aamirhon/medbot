import type { TFunction } from 'i18next';

export const STATUS_COLORS: Record<string, string> = {
  draft:      '#9ca3af',
  pending_1c: '#9ca3af',
  invoiced:   '#f59e0b',
  paid:       '#3b82f6',
  shipped:    '#8b5cf6',
  completed:  '#10b981',
  cancelled:  '#ef4444',
};

export function getStatusLabel(status: string, t: TFunction): string {
  return t(`order_status.${status}`, { defaultValue: status });
}

export function getStatusColor(status: string): string {
  return STATUS_COLORS[status] ?? '#9ca3af';
}
