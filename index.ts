import { Plugin } from "@opencode/plugin"

// Server part of the animation pack. All animation logic lives in tui.tsx;
// this entry exists so OpenCode's plugin discovery finds the package.
export default Plugin.define({
  id: "animation-pack",
  setup() {},
})
