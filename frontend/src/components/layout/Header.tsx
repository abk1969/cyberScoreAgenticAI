'use client'

import { Bell, Search, User } from 'lucide-react'

interface HeaderProps {
  title?: string
}

export function Header({ title = 'Dashboard' }: HeaderProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <h2 className="text-lg font-semibold text-[#2C3E50]">{title}</h2>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher..."
            className="h-9 w-64 rounded-lg border border-gray-200 bg-gray-50 pl-10 pr-4 text-sm focus:border-[#2E75B6] focus:outline-none"
            aria-label="Rechercher"
          />
        </div>
        <button
          className="relative rounded-lg p-2 hover:bg-gray-100"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5 text-[#2C3E50]" />
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#C0392B] text-[10px] font-bold text-white">
            3
          </span>
        </button>
        <div className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-1.5">
          <User className="h-5 w-5 text-[#2C3E50]" />
          <span className="text-sm font-medium text-[#2C3E50]">RSSI</span>
        </div>
      </div>
    </header>
  )
}
