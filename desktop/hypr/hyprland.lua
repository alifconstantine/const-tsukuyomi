local terminal = "kitty"
local lock = "constos-lock"

hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 8,
        border_size = 2,
        layout = "dwindle",
    },
    binds = { movefocus_cycles_fullscreen = true },
    decoration = {
        rounding = 12,
        blur = { enabled = true, size = 6, passes = 2 },
    },
    input = {
        kb_layout = os.getenv("XKB_DEFAULT_LAYOUT") or "us",
        kb_variant = os.getenv("XKB_DEFAULT_VARIANT") or "",
    },
    misc = { disable_hyprland_logo = true, disable_splash_rendering = true, force_default_wallpaper = 0 },
})

hl.on("hyprland.start", function()
    hl.exec_cmd("constos-session-start")
end)

-- Keep Kitty tiled when it tries to restore a maximized window.
hl.window_rule({
    name = "kitty-suppress-maximize",
    match = { class = "^kitty$" },
    suppress_event = "maximize",
})

hl.bind("SUPER + Return", hl.dsp.exec_cmd(terminal))
hl.bind("SUPER + B", hl.dsp.exec_cmd("constos-browser"))
hl.bind("SUPER + E", hl.dsp.exec_cmd("nautilus"))
hl.bind("SUPER + N", hl.dsp.exec_cmd("mousepad"))
hl.bind("SUPER + Space", hl.dsp.exec_cmd("dms ipc call spotlight toggle || wofi --show drun"))
hl.bind("SUPER + Tab", hl.dsp.exec_cmd("dms ipc call hypr toggleOverview"))
hl.bind("SUPER + comma", hl.dsp.exec_cmd("dms ipc call settings focusOrToggle"))
hl.bind("SUPER + A", hl.dsp.exec_cmd("dms ipc call control-center toggle"))
hl.bind("SUPER + Escape", hl.dsp.exec_cmd("dms ipc call control-center toggle"))
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + F", function()
    local window = hl.get_active_window()
    if not window then
        return
    end
    if window.fullscreen == 0 then
        hl.dispatch(hl.dsp.window.fullscreen())
    else
        hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 0, client = 0 }))
    end
end)
hl.bind("ALT + Tab", hl.dsp.focus({ last = true }))
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + L", hl.dsp.exec_cmd(lock))
hl.bind("SUPER + SHIFT + M", hl.dsp.exit())
hl.bind("Print", hl.dsp.exec_cmd("constos-screenshot region"))
hl.bind("ALT + Print", hl.dsp.exec_cmd("constos-screenshot screen"))
hl.bind("SUPER + SHIFT + S", hl.dsp.exec_cmd("constos-screenshot region"))
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"))
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl set 5%+"), { repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 5%-"), { repeating = true })

for _, direction in ipairs({ "left", "right", "up", "down" }) do
    hl.bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }))
    hl.bind("SUPER + SHIFT + " .. direction, hl.dsp.window.move({ direction = direction }))
end

for workspace = 1, 10 do
    local key = tostring(workspace % 10)
    hl.bind("SUPER + " .. key, hl.dsp.focus({ workspace = workspace }))
    hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace }))
end
