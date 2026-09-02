export function formatCurrency(amount: number | null): string {
  if (amount === null) return '예상 금액 별도 확인';
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPriceRange(
  amountMin?: number | null,
  amountMax?: number | null,
  fallbackAmount?: number | null,
): string {
  const formatter = new Intl.NumberFormat('ko-KR');
  if (amountMin !== null && amountMin !== undefined && amountMax !== null && amountMax !== undefined) {
    return `${formatter.format(amountMin)}원 ~ ${formatter.format(amountMax)}원`;
  }
  if (fallbackAmount !== null && fallbackAmount !== undefined) {
    return `${formatter.format(fallbackAmount)}원`;
  }
  return '예상 가격 범위 확인 필요';
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat('ko-KR', {
    style: 'percent',
    maximumFractionDigits: 0,
  }).format(value);
}
