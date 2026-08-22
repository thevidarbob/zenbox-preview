-- ZenBox — right-quadrant inbox on Omarchy (Hyprland Lua / Quattro).
-- Loaded from ~/.config/hypr/hyprland.lua via: require("hypr.zenbox")

-- Super+Shift+Z is unused in stock Omarchy bindings (Ctrl+Z is zoom).
o.bind("SUPER + SHIFT + Z", "ZenBox", "zenbox")
o.bind("SUPER + SHIFT + ALT + Z", "ZenBox quick add", "zenbox add")

-- Chromium --app plus --class=zenbox; also match the document title.
o.window("zenbox", {
  float = true,
  size = { 420, "100%" },
  move = { "(monitor_w-window_w-10)", 0 },
  tag = "-default-opacity",
  opacity = "1 1",
})

o.window({ title = "^(Inbox|ZenBox)$" }, {
  float = true,
  size = { 420, "100%" },
  move = { "(monitor_w-window_w-10)", 0 },
  tag = "-default-opacity",
  opacity = "1 1",
})
