export function titleCase(value: string): string {
  return value
    .replaceAll('_', ' ')
    .split(' ')
    .filter(Boolean)
    .map((chunk: string) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

export function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}
