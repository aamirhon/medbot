export const formatMoney = (n: number): string =>
  `${new Intl.NumberFormat('ru-RU').format(Math.round(n))} сум`;

export const formatDate = (iso: string): string => {
  const d = new Date(iso);
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d);
};
