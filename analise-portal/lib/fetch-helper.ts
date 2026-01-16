/**
 * Helper para fazer requisições fetch com autenticação automática
 * Funciona tanto no cliente quanto no servidor (Next.js)
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  // Verificar se estamos no cliente (browser)
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token')
    
    const headers = new Headers(options.headers)
    
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    
    return fetch(url, {
      ...options,
      headers,
    })
  }
  
  // No servidor, fazer fetch normal
  return fetch(url, options)
}
