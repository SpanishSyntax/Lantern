"""Terminal UI interface for Lantern, powered directly by Prism."""

from __future__ import annotations

from prism import (
    UI,
    Spinner,
    add_agent_args,
    add_color_args,
    apply_agent_args,
    apply_color_args,
    confirm_input,
    detect_color_support,
    get_terminal_columns,
    handle_agent_args,
    handle_color_args,
    multiselect_menu,
    prompt_input,
    render_error_panel,
    render_panel,
    select_menu,
    spinner_context,
    strip_ansi,
    visual_len,
)

try:
    from prism import render_help
except ImportError:
    try:
        from prism.help import render_help
    except ImportError:
        render_help = None  # type: ignore

try:
    from prism import handle_version_arg
except ImportError:
    try:
        from prism.color import handle_version_arg
    except ImportError:
        handle_version_arg = None  # type: ignore

try:
    from prism import get_agent_env, get_json_env, get_toon_env
except ImportError:
    get_agent_env = None  # type: ignore
    get_json_env = None  # type: ignore
    get_toon_env = None  # type: ignore

try:
    from prism.cards import render_status_card
except ImportError:
    render_status_card = None  # type: ignore

try:
    from prism import check_agent_env
except ImportError:
    from prism.styling import check_agent_env

ui = UI(app_name="lantern", icon="🏮", badge_color="1;36")
ui.check_agent_env = check_agent_env  # type: ignore


def _render_help(
    tagline: str,
    usage: Sequence[str] | str,
    commands: Sequence[tuple[str, str]] | dict[str, str] | None = None,
    options: Sequence[tuple[str, str]] | dict[str, str] | None = None,
    sections: Sequence[tuple[str, Sequence[tuple[str, str]] | str]] | None = None,
    examples: Sequence[tuple[str, str]] | Sequence[str] | None = None,
    version: str | None = None,
    app_name: str | None = None,
    is_agent: bool | None = None,
) -> str:
    name = app_name or "Lantern"
    agent = is_agent if is_agent is not None else ui.is_agent
    try:
        from prism.help import render_help as _rh

        return _rh(
            app_name=name,
            tagline=tagline,
            usage=usage,
            commands=commands,
            options=options,
            sections=sections,
            examples=examples,
            version=version,
            is_agent=agent,
        )
    except Exception:
        lines: list[str] = []
        clean_tagline = tagline.strip()
        v_str = f" v{version}" if version else ""
        if agent:
            lines.append(f"{name}{v_str} - {clean_tagline}")
            if usage:
                lines.append("")
                u_list = [usage] if isinstance(usage, str) else list(usage)
                lines.append(f"Usage: {u_list[0]}")
                for u in u_list[1:]:
                    lines.append(f"       {u}")
            if commands:
                lines.append("\nCommands:")
                cmd_dict = (
                    dict(commands)
                    if isinstance(commands, (list, tuple))
                    else commands
                )
                for k, v in cmd_dict.items():
                    lines.append(f"  {k:<20} {v}")
            if options:
                lines.append("\nOptions:")
                opt_dict = (
                    dict(options)
                    if isinstance(options, (list, tuple))
                    else options
                )
                for k, v in opt_dict.items():
                    lines.append(f"  {k:<20} {v}")
            if sections:
                for s_title, s_items in sections:
                    lines.append(f"\n{s_title}:")
                    s_dict = (
                        dict(s_items)
                        if isinstance(s_items, (list, tuple))
                        else s_items
                    )
                    for k, v in s_dict.items():
                        lines.append(f"  {k:<12} {v}")
            return "\n".join(lines) + "\n"
        else:
            lines.append(f"{ui.badge()} {ui.bold(f'{clean_tagline}{v_str}')}")
            if usage:
                lines.append(f"\n{ui.blue('Usage:')}")
                u_list = [usage] if isinstance(usage, str) else list(usage)
                for u in u_list:
                    lines.append(f"  {u}")
            if commands:
                lines.append(f"\n{ui.blue('Commands:')}")
                cmd_dict = (
                    dict(commands)
                    if isinstance(commands, (list, tuple))
                    else commands
                )
                for k, v in cmd_dict.items():
                    lines.append(f"  {k:<20} {v}")
            if options:
                lines.append(f"\n{ui.blue('Options:')}")
                opt_dict = (
                    dict(options)
                    if isinstance(options, (list, tuple))
                    else options
                )
                for k, v in opt_dict.items():
                    lines.append(f"  {k:<20} {v}")
            if sections:
                for s_title, s_items in sections:
                    lines.append(f"\n{ui.blue(f'{s_title}:')}")
                    s_dict = (
                        dict(s_items)
                        if isinstance(s_items, (list, tuple))
                        else s_items
                    )
                    for k, v in s_dict.items():
                        lines.append(f"  {ui.bold(k):<20} {v}")
            return "\n".join(lines) + "\n"


ui.render_help = _render_help  # type: ignore

__all__ = [
    "ui",
    "UI",
    "Spinner",
    "spinner_context",
    "add_agent_args",
    "apply_agent_args",
    "handle_agent_args",
    "add_color_args",
    "apply_color_args",
    "handle_color_args",
    "handle_version_arg",
    "render_help",
    "render_panel",
    "render_error_panel",
    "render_status_card",
    "prompt_input",
    "confirm_input",
    "select_menu",
    "multiselect_menu",
    "detect_color_support",
    "strip_ansi",
    "visual_len",
    "get_terminal_columns",
    "get_agent_env",
    "get_json_env",
]
