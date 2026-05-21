export function fixPdfUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  // Заменяем внутренний docker hostname на localhost
  return url.replace(/^http:\/\/mock_1c:8001/, 'http://localhost:8001');
}
