import { Plugin } from "@opencode/plugin/tui"
import { createSignal } from "solid-js"

// Noise characters used by the scramble-in text effect.
const NOISE = "▓▒░#*+~"
// Equalizer bar heights, low to high.
const EQ_H = ["▁", "▂", "▃", "▄", "▅", "▆", "▇"]
// Phrases typed out on the home footer.
const PHRASES = ["animation pack", "/anim to toggle", "vibrant edition"]
// Rotating glyphs for the permission pulse and activity ribbon.
const SPIN_GLYPH = ["◐", "◓", "◑", "◒"]
const PULSE_GLYPH = ["·", "•", "●", "•"]

type Phase = "done" | "fail"
type Flash = { phase: Phase; at: number }
type Stage = { text: string; at: number }

// Reveals target left to right; unrevealed characters show noise, the rest are blank.
const scramble = (target: string, progress: number, seed: number) => {
  let out = ""
  for (let i = 0; i < target.length; i++) {
    const at = (i + 1) / target.length
    if (progress >= at) out += target[i]
    else if (progress >= at - 0.5) out += NOISE[(seed + i * 5) % NOISE.length]
    else out += " "
  }
  return out
}

// Six-bar equalizer that waves slowly.
const eqLine = (frame: number) => {
  let out = ""
  for (let i = 0; i < 6; i++) {
    const value = Math.sin((frame + i * 11) * 0.22) * 3.4 + 3.4
    out += EQ_H[Math.max(0, Math.min(6, Math.round(value)))]
  }
  return out
}

const clockLine = (seconds: number) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  const pad = (n: number) => String(n).padStart(2, "0")
  return h > 0 ? h + ":" + pad(m) + ":" + pad(s) : pad(m) + ":" + pad(s)
}

export default Plugin.define({
  id: "animation-pack.tui",
  setup(context) {
    const [settings, updateSettings] = context.storage.store("settings", {
      initial: { enabled: true },
    })
    const [frame, setFrame] = createSignal(0)
    const [flashes, setFlashes] = createSignal<Record<string, Flash>>({})
    const [stages, setStages] = createSignal<Record<string, Stage>>({})
    const [waiting, setWaiting] = createSignal<Record<string, boolean>>({})

    const startedAt = new Map<string, number>()

    // One shared clock drives every animation: 90ms per tick.
    const interval = setInterval(() => setFrame((f) => (f + 1) % 100000), 90)

    const timers = new Map<string, ReturnType<typeof setTimeout>>()
    const clearFlashTimer = (sessionID: string) => {
      const pending = timers.get(sessionID)
      if (pending) {
        clearTimeout(pending)
        timers.delete(sessionID)
      }
    }
    const flash = (sessionID: string, phase: Phase) => {
      setFlashes((p) => ({ ...p, [sessionID]: { phase, at: Date.now() } }))
      clearFlashTimer(sessionID)
      timers.set(
        sessionID,
        setTimeout(() => {
          setFlashes((p) => {
            const next = { ...p }
            delete next[sessionID]
            return next
          })
          timers.delete(sessionID)
        }, 2400),
      )
    }
    const setStage = (sessionID: string, text: string) => {
      setStages((p) => ({ ...p, [sessionID]: { text, at: Date.now() } }))
    }
    const clearStage = (sessionID: string) => {
      setStages((p) => {
        if (!(sessionID in p)) return p
        const next = { ...p }
        delete next[sessionID]
        return next
      })
    }

    const offs = [
      context.data.on("session.execution.started", (event) => {
        const id = event.data.sessionID
        clearFlashTimer(id)
        startedAt.set(id, Date.now())
        setFlashes((p) => {
          if (!(id in p)) return p
          const next = { ...p }
          delete next[id]
          return next
        })
        setStage(id, "starting")
      }),
      context.data.on("session.tool.input.started", (event) =>
        setStage(event.data.sessionID, "⚙ " + event.data.name.slice(0, 16)),
      ),
      context.data.on("session.text.started", (event) => setStage(event.data.sessionID, "streaming")),
      context.data.on("session.reasoning.started", (event) => setStage(event.data.sessionID, "reasoning")),
      context.data.on("session.execution.succeeded", (event) => {
        clearStage(event.data.sessionID)
        flash(event.data.sessionID, "done")
      }),
      context.data.on("session.execution.failed", (event) => {
        clearStage(event.data.sessionID)
        flash(event.data.sessionID, "fail")
      }),
      context.data.on("session.execution.interrupted", (event) => {
        clearStage(event.data.sessionID)
        flash(event.data.sessionID, "fail")
      }),
      context.data.on("permission.asked", (event) => {
        setWaiting((p) => ({ ...p, [event.data.sessionID]: true }))
      }),
      context.data.on("permission.replied", (event) => {
        setWaiting((p) => {
          if (!(event.data.sessionID in p)) return p
          const next = { ...p }
          delete next[event.data.sessionID]
          return next
        })
      }),
    ]

    context.keymap.layer(() => ({
      mode: "global",
      priority: 10,
      commands: [
        {
          id: "animation-pack.toggle",
          title: "Toggle animation pack",
          group: "Animation",
          palette: true,
          slash: { name: "anim", aliases: ["animations"], arguments: true },
          run: async (input) => {
            const arg = (input ?? "").trim().toLowerCase()
            const enabled = arg === "on" ? true : arg === "off" ? false : settings.enabled === false
            await updateSettings((draft) => {
              draft.enabled = enabled
            })
            context.ui.toast.show({
              message: enabled ? "Animation pack on" : "Animation pack off",
              variant: enabled ? "success" : "info",
            })
          },
        },
      ],
    }))

    // Permission pulse beats here; otherwise green/red run-out ticks.
    const offStatus = context.ui.slot({
      append: "prompt.footer.status",
      render: (input) => {
        if (settings.enabled === false || !input.sessionID) return null
        const f = frame()
        if (waiting()[input.sessionID]) {
          const glyph = SPIN_GLYPH[Math.floor(f / 4) % SPIN_GLYPH.length]
          return <text fg={context.theme.text.feedback.warning.base}>{glyph + " waiting for you"}</text>
        }
        const flashState = flashes()[input.sessionID]
        if (!flashState) return null
        if (flashState.phase === "done") {
          const started = startedAt.get(input.sessionID) ?? flashState.at
          const seconds = ((flashState.at - started) / 1000).toFixed(1)
          const progress = Math.min(1, (Date.now() - flashState.at) / 700)
          return <text fg={context.theme.text.feedback.success.base}>{scramble("✓ done in " + seconds + "s", progress, f)}</text>
        }
        const progress = Math.min(1, (Date.now() - flashState.at) / 700)
        return <text fg={context.theme.text.feedback.error.base}>{scramble("✕ failed", progress, f)}</text>
      },
    })

    // Activity ribbon above the composer: last thing the agent did, decode-in.
    const offComposer = context.ui.slot({
      append: "session.composer.top",
      render: (input) => {
        if (settings.enabled === false || !input.sessionID) return null
        const stage = stages()[input.sessionID]
        if (!stage) return null
        const f = frame()
        const progress = Math.min(1, (Date.now() - stage.at) / 600)
        const glyph = PULSE_GLYPH[Math.floor(f / 5) % PULSE_GLYPH.length]
        return <text fg={context.theme.text.action.secondary.base}>{glyph + " " + scramble(stage.text, progress, f)}</text>
      },
    })

    // Sidebar vitals: run clock (or session age) plus live cost.
    const offSidebar = context.ui.slot({
      append: "sidebar.footer",
      render: (input) => {
        if (settings.enabled === false || !input.sessionID) return null
        const info = context.data.session.get(input.sessionID)
        if (!info) return null
        const base = startedAt.get(input.sessionID) ?? info.time.created
        const seconds = Math.max(0, Math.floor((Date.now() - base) / 1000))
        const cost = context.data.session.cost(input.sessionID)
        const line = "⏱ " + clockLine(seconds) + " · $" + cost.toFixed(2)
        return <text fg={context.theme.text.muted}>{line}</text>
      },
    })

    // Equalizer bars + typed phrase keep the idle screen alive.
    const offHome = context.ui.slot({
      append: "home.footer.status",
      render: () => {
        if (settings.enabled === false) return null
        const f = frame()
        const cycle = 45
        const phrase = PHRASES[Math.floor(f / cycle) % PHRASES.length]
        const line = eqLine(Math.floor(f / 2)) + " " + scramble(phrase, Math.min(1, (f % cycle) / 8), f)
        return <text fg={context.theme.text.muted}>{line}</text>
      },
    })

    return () => {
      clearInterval(interval)
      for (const timer of timers.values()) clearTimeout(timer)
      timers.clear()
      for (const off of offs) off()
      offStatus()
      offComposer()
      offSidebar()
      offHome()
    }
  },
})
