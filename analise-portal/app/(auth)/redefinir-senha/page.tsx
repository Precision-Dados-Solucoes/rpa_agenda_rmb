'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ArrowLeft } from 'lucide-react'

function RedefinirSenhaContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [senha, setSenha] = useState('')
  const [confirmarSenha, setConfirmarSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [validando, setValidando] = useState(true)
  const [tokenValido, setTokenValido] = useState(false)
  const [erro, setErro] = useState('')

  useEffect(() => {
    if (!token) {
      setErro('Token inválido ou ausente')
      setValidando(false)
      return
    }

    // Validar token
    fetch(`/api/auth/validar-token-reset?token=${token}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.valido) {
          setTokenValido(true)
        } else {
          setErro(data.error || 'Token inválido ou expirado')
        }
        setValidando(false)
      })
      .catch(() => {
        setErro('Erro ao validar token')
        setValidando(false)
      })
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErro('')

    if (senha !== confirmarSenha) {
      setErro('As senhas não coincidem')
      return
    }

    if (senha.length < 6) {
      setErro('A senha deve ter no mínimo 6 caracteres')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('/api/auth/redefinir-senha', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, senha }),
      })

      const data = await response.json()

      if (!response.ok) {
        setErro(data.error || 'Erro ao redefinir senha')
        setLoading(false)
        return
      }

      // Sucesso - redirecionar para login
      router.push('/login?senha-redefinida=true')
    } catch (err) {
      setErro('Erro ao conectar com o servidor')
      setLoading(false)
    }
  }

  if (validando) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 px-4 py-12">
        <div className="w-full max-w-md">
          <Card className="w-full shadow-lg border-0">
            <CardContent className="p-8">
              <div className="flex items-center justify-center">
                <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p className="text-center mt-4 text-gray-600">Validando token...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (!tokenValido) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 px-4 py-12">
        <div className="w-full max-w-md">
          <Card className="w-full shadow-lg border-0">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-2xl text-slate-800">Token inválido</CardTitle>
              <CardDescription className="text-slate-600">
                O token de redefinição de senha é inválido ou expirou.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-r mb-4">
                <p className="font-medium">{erro}</p>
              </div>
              <Button
                onClick={() => router.push('/esqueci-senha')}
                className="w-full h-11 text-base font-semibold bg-blue-600 hover:bg-blue-700"
              >
                Solicitar novo link
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Cabeçalho com nome da empresa */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            Advocacia Roberto Matos de Brito
          </h1>
          <h2 className="text-lg font-semibold text-blue-600 uppercase tracking-wide">
            Portal de Análises
          </h2>
        </div>

        <Card className="w-full shadow-lg border-0">
          <CardHeader className="space-y-1 pb-4">
            <div className="flex items-center gap-2 mb-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/login')}
                className="h-8 w-8"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <CardTitle className="text-2xl text-slate-800 flex-1">Redefinir senha</CardTitle>
            </div>
            <CardDescription className="text-slate-600">
              Digite sua nova senha abaixo.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              {erro && (
                <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-r">
                  <p className="font-medium">{erro}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="senha" className="text-slate-700 font-medium">
                  Nova senha
                </Label>
                <Input
                  id="senha"
                  type="password"
                  placeholder="••••••••"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11"
                  autoComplete="new-password"
                  minLength={6}
                />
                <p className="text-xs text-gray-500">Mínimo de 6 caracteres</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmarSenha" className="text-slate-700 font-medium">
                  Confirmar nova senha
                </Label>
                <Input
                  id="confirmarSenha"
                  type="password"
                  placeholder="••••••••"
                  value={confirmarSenha}
                  onChange={(e) => setConfirmarSenha(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11"
                  autoComplete="new-password"
                  minLength={6}
                />
              </div>

              <Button
                type="submit"
                className="w-full h-11 text-base font-semibold bg-blue-600 hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Redefinindo...
                  </span>
                ) : (
                  'Redefinir senha'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function RedefinirSenhaPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <p>Carregando...</p>
      </div>
    }>
      <RedefinirSenhaContent />
    </Suspense>
  )
}
