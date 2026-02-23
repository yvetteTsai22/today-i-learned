"use client"

import * as React from "react"
import { Command } from "cmdk"
import { useRouter } from "next/navigation"
import {
  PenLine,
  Search,
  Sparkles,
  LayoutDashboard,
  Sun,
  Moon,
  Monitor,
  Palette,
} from "lucide-react"
import { useTheme } from "next-themes"
import { Dialog, VisuallyHidden } from "radix-ui"

const colorThemes = [
  { name: "teal", label: "Teal" },
  { name: "indigo", label: "Indigo" },
  { name: "rose", label: "Rose" },
  { name: "amber", label: "Amber" },
  { name: "emerald", label: "Emerald" },
  { name: "violet", label: "Violet" },
] as const

export function CommandPalette() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()
  const { setTheme } = useTheme()

  // Toggle on Cmd+K / Ctrl+K
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = React.useCallback(
    (command: () => void) => {
      setOpen(false)
      command()
    },
    []
  )

  const setColorTheme = (theme: string) => {
    localStorage.setItem("color-theme", theme)
    document.documentElement.setAttribute("data-theme", theme)
  }

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      className="fixed inset-0 z-50"
    >
      <VisuallyHidden.Root>
        <Dialog.Title>Command palette</Dialog.Title>
        <Dialog.Description>Navigate, switch themes, or search commands</Dialog.Description>
      </VisuallyHidden.Root>

      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />

      {/* Dialog */}
      <div className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 px-4">
        <div className="overflow-hidden rounded-xl border bg-popover shadow-2xl">
          <Command.Input
            placeholder="Type a command or search..."
            className="w-full border-b bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            {/* Navigation */}
            <Command.Group heading="Navigate" className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              <Command.Item
                onSelect={() => runCommand(() => router.push("/"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <LayoutDashboard className="h-4 w-4 text-muted-foreground" />
                Dashboard
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push("/capture"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <PenLine className="h-4 w-4 text-muted-foreground" />
                Capture Note
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push("/search"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <Search className="h-4 w-4 text-muted-foreground" />
                Search Knowledge
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push("/digest"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <Sparkles className="h-4 w-4 text-muted-foreground" />
                Weekly Digest
              </Command.Item>
            </Command.Group>

            {/* Appearance — light/dark/system */}
            <Command.Separator className="my-1 h-px bg-border" />
            <Command.Group heading="Appearance" className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              <Command.Item
                onSelect={() => runCommand(() => setTheme("light"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <Sun className="h-4 w-4 text-muted-foreground" />
                Light Mode
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => setTheme("dark"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <Moon className="h-4 w-4 text-muted-foreground" />
                Dark Mode
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => setTheme("system"))}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
              >
                <Monitor className="h-4 w-4 text-muted-foreground" />
                System Theme
              </Command.Item>
            </Command.Group>

            {/* Color Theme — 6 OKLCH themes */}
            <Command.Separator className="my-1 h-px bg-border" />
            <Command.Group heading="Color Theme" className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              {colorThemes.map((theme) => (
                <Command.Item
                  key={theme.name}
                  onSelect={() => runCommand(() => setColorTheme(theme.name))}
                  className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent"
                >
                  <Palette className="h-4 w-4 text-muted-foreground" />
                  {theme.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </div>
      </div>
    </Command.Dialog>
  )
}
