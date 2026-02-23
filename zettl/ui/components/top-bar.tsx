"use client"

import Link from "next/link"
import { ThemeSwitcher } from "@/components/theme-switcher"

export function TopBar() {
  const openCommandPalette = () => {
    document.dispatchEvent(
      new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true })
    )
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-14 border-b bg-background/80 backdrop-blur-sm">
      <div className="flex h-full items-center justify-between px-4 md:px-6">
        {/* Logo */}
        <Link href="/" className="text-lg font-bold text-foreground hover:text-primary transition-colors">
          Zettl
        </Link>

        {/* Cmd+K trigger */}
        <button
          onClick={openCommandPalette}
          className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <kbd className="pointer-events-none inline-flex h-6 select-none items-center gap-1 rounded border bg-muted px-2 font-mono text-xs font-medium text-muted-foreground">
            <span className="text-xs">⌘</span>K
          </kbd>
          <span>to navigate</span>
        </button>

        {/* Theme toggle */}
        <ThemeSwitcher />
      </div>
    </header>
  )
}
