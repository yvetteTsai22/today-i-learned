"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Palette, Sun, Moon, Monitor } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const colorThemes = [
  { name: "teal", label: "Teal", color: "oklch(0.55 0.15 180)" },
  { name: "indigo", label: "Indigo", color: "oklch(0.50 0.20 265)" },
  { name: "rose", label: "Rose", color: "oklch(0.55 0.20 350)" },
  { name: "amber", label: "Amber", color: "oklch(0.70 0.18 70)" },
  { name: "emerald", label: "Emerald", color: "oklch(0.55 0.17 155)" },
  { name: "violet", label: "Violet", color: "oklch(0.55 0.22 290)" },
] as const

type ColorTheme = (typeof colorThemes)[number]["name"]

export function ThemeSwitcher() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)
  const [isOpen, setIsOpen] = React.useState(false)
  const [colorTheme, setColorTheme] = React.useState<ColorTheme>("teal")
  const dropdownRef = React.useRef<HTMLDivElement>(null)

  // Avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true)
    // Load saved color theme from localStorage
    const savedColorTheme = localStorage.getItem("color-theme") as ColorTheme | null
    if (savedColorTheme && colorThemes.some((t) => t.name === savedColorTheme)) {
      setColorTheme(savedColorTheme)
      document.documentElement.setAttribute("data-theme", savedColorTheme)
    }
  }, [])

  // Close dropdown when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Close on escape key
  React.useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false)
      }
    }
    document.addEventListener("keydown", handleEscape)
    return () => document.removeEventListener("keydown", handleEscape)
  }, [])

  const handleColorThemeChange = (newTheme: ColorTheme) => {
    setColorTheme(newTheme)
    localStorage.setItem("color-theme", newTheme)
    document.documentElement.setAttribute("data-theme", newTheme)
  }

  const handleModeChange = (mode: "light" | "dark" | "system") => {
    setTheme(mode)
  }

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="Theme switcher loading">
        <Palette className="h-5 w-5" />
      </Button>
    )
  }

  const isDark = resolvedTheme === "dark"

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Open theme switcher"
        aria-expanded={isOpen}
        className="cursor-pointer"
      >
        <Palette className="h-5 w-5" />
      </Button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 z-50 min-w-[200px] rounded-lg border bg-popover p-3 shadow-lg"
          role="menu"
          aria-label="Theme options"
        >
          {/* Color Theme Selection */}
          <div className="mb-3">
            <p className="text-xs font-medium text-muted-foreground mb-2">Color Theme</p>
            <div className="grid grid-cols-3 gap-2">
              {colorThemes.map((t) => (
                <button
                  key={t.name}
                  onClick={() => handleColorThemeChange(t.name)}
                  className={cn(
                    "flex flex-col items-center gap-1 rounded-md p-2 transition-colors cursor-pointer",
                    "hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring",
                    colorTheme === t.name && "bg-accent ring-2 ring-primary"
                  )}
                  role="menuitemradio"
                  aria-checked={colorTheme === t.name}
                  aria-label={`${t.label} theme`}
                >
                  <span
                    className="h-6 w-6 rounded-full border-2 border-background shadow-sm"
                    style={{ backgroundColor: t.color }}
                  />
                  <span className="text-xs">{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t my-3" />

          {/* Light/Dark Mode Selection */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Appearance</p>
            <div className="flex gap-1">
              <button
                onClick={() => handleModeChange("light")}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm transition-colors cursor-pointer",
                  "hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring",
                  theme === "light" && "bg-accent ring-2 ring-primary"
                )}
                role="menuitemradio"
                aria-checked={theme === "light"}
                aria-label="Light mode"
              >
                <Sun className="h-4 w-4" />
                <span>Light</span>
              </button>
              <button
                onClick={() => handleModeChange("dark")}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm transition-colors cursor-pointer",
                  "hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring",
                  theme === "dark" && "bg-accent ring-2 ring-primary"
                )}
                role="menuitemradio"
                aria-checked={theme === "dark"}
                aria-label="Dark mode"
              >
                <Moon className="h-4 w-4" />
                <span>Dark</span>
              </button>
              <button
                onClick={() => handleModeChange("system")}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm transition-colors cursor-pointer",
                  "hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring",
                  theme === "system" && "bg-accent ring-2 ring-primary"
                )}
                role="menuitemradio"
                aria-checked={theme === "system"}
                aria-label="System mode"
              >
                <Monitor className="h-4 w-4" />
                <span>Auto</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
