set -g fish_greeting

if status is-interactive
    if test -t 1; and type -q fastfetch
        fastfetch
    end
end
