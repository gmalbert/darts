import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Player } from "../../types";
import { natFlag } from "../../utils/formatters";

interface PlayerPickerProps {
  players: Player[];
  value: Player | null;
  onChange: (player: Player) => void;
  onClear?: () => void;
  placeholder?: string;
  ariaLabel?: string;
  autoFocus?: boolean;
}

const MAX_VISIBLE = 60;

function matches(player: Player, query: string): boolean {
  if (!query) return true;
  return (
    player.name.toLowerCase().includes(query) ||
    (player.nickname ?? "").toLowerCase().includes(query)
  );
}

export function PlayerPicker({
  players,
  value,
  onChange,
  onClear,
  placeholder = "Search 813 players by name…",
  ariaLabel = "Select a player",
  autoFocus = false,
}: PlayerPickerProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputId = useId();
  const listId = `${inputId}-list`;

  useEffect(() => {
    if (!open) return;
    const onDocPointerDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", onDocPointerDown);
    return () => document.removeEventListener("mousedown", onDocPointerDown);
  }, [open]);

  const normalized = query.trim().toLowerCase();

  const results = useMemo(() => {
    const pool = normalized
      ? players.filter((p) => matches(p, normalized))
      : players;
    return pool.slice(0, MAX_VISIBLE);
  }, [players, normalized]);

  const matchCount = useMemo(
    () => (normalized ? players.filter((p) => matches(p, normalized)).length : players.length),
    [players, normalized],
  );

  const commit = (player: Player) => {
    onChange(player);
    setQuery("");
    setOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveIndex(0);
        return;
      }
      setActiveIndex((i) => {
        const next = e.key === "ArrowDown" ? i + 1 : i - 1;
        if (next < 0) return results.length - 1;
        if (next >= results.length) return 0;
        return next;
      });
      return;
    }
    if (e.key === "Enter") {
      if (open && results[activeIndex]) {
        e.preventDefault();
        commit(results[activeIndex]);
      }
      return;
    }
    if (e.key === "Escape") {
      if (open) {
        e.stopPropagation();
        setOpen(false);
        setQuery("");
      }
    }
  };

  const fieldText = open ? query : (value?.name ?? "");

  return (
    <div className="player-picker" ref={wrapRef}>
      <label htmlFor={inputId}>{ariaLabel}</label>
      <div className="picker-field">
        <input
          id={inputId}
          className="picker-input"
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          autoComplete="off"
          autoFocus={autoFocus}
          placeholder={placeholder}
          value={fieldText}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            setActiveIndex(0);
          }}
          onFocus={() => {
            setOpen(true);
            setActiveIndex(0);
          }}
          onKeyDown={handleKeyDown}
        />
        {value && (
          <button
            type="button"
            className="picker-clear"
            aria-label="Clear player selection"
            onClick={() => {
              onClear?.();
              setQuery("");
              setOpen(false);
            }}
          >
            ✕
          </button>
        )}
      </div>

      {open && (
        <ul className="picker-list" id={listId} role="listbox">
          {results.length === 0 ? (
            <li className="picker-empty">No player matches “{query.trim()}”.</li>
          ) : (
            results.map((p, i) => (
              <li
                key={p.id}
                role="option"
                aria-selected={value?.id === p.id}
                className={[
                  "picker-option",
                  i === activeIndex ? "is-active" : "",
                  value?.id === p.id ? "is-selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onMouseEnter={() => setActiveIndex(i)}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => commit(p)}
              >
                <span aria-hidden="true">{natFlag(p.nationality)}</span>
                <span className="picker-name">{p.name}</span>
                <span className="picker-sub">{Math.round(p.elo)}</span>
              </li>
            ))
          )}
        </ul>
      )}

      {open && matchCount > results.length && (
        <div className="picker-hint">
          Showing {results.length} of {matchCount} matches — keep typing to narrow it down.
        </div>
      )}
    </div>
  );
}
