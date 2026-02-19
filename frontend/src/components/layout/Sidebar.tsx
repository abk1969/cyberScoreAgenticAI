'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  BarChart3,
  Building2,
  FileQuestion,
  FileText,
  Bell,
  Network,
  Shield,
  MessageCircle,
  Settings,
  Globe,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/executive', label: 'Exécutif', icon: BarChart3 },
  { href: '/vendors', label: 'Fournisseurs', icon: Building2 },
  { href: '/questionnaires', label: 'Questionnaires', icon: FileQuestion },
  { href: '/reports', label: 'Rapports', icon: FileText },
  { href: '/alerts', label: 'Alertes', icon: Bell },
  { href: '/supply-chain', label: 'Supply Chain', icon: Network },
  { href: '/compliance/dora', label: 'Conformité', icon: Shield },
  { href: '/chat', label: 'Chat IA', icon: MessageCircle },
  { href: '/portal', label: 'Portail Fournisseur', icon: Globe },
  { href: '/admin', label: 'Admin', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center border-b border-gray-200 px-6">
        <h1 className="text-xl font-bold text-[#1B3A5C]">
          MH-CyberScore
        </h1>
      </div>
      <nav className="space-y-1 p-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-[#2E75B6]/10 text-[#2E75B6]'
                  : 'text-[#2C3E50] hover:bg-gray-100'
              }`}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
