import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Verificar se está em produção e se a requisição é HTTP
  const isProduction = process.env.NODE_ENV === 'production'
  const protocol = request.headers.get('x-forwarded-proto') || request.nextUrl.protocol
  
  // Se for HTTP em produção, redirecionar para HTTPS
  if (isProduction && protocol === 'http:') {
    const url = request.nextUrl.clone()
    url.protocol = 'https:'
    return NextResponse.redirect(url, 301) // Redirecionamento permanente
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
