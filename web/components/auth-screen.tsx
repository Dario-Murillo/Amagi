"use client";

import { useState, type FormEvent } from "react";
import { Wordmark } from "@/components/wordmark";
import type { AuthMode } from "@/lib/types";

type Props = {
  error: string;
  isLoading: boolean;
  onLogin: (username: string, password: string) => void;
  onRegister: (username: string, password: string) => void;
  onClearError: () => void;
};

export default function AuthScreen({
  error,
  isLoading,
  onLogin,
  onRegister,
  onClearError,
}: Props) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function switchMode(next: AuthMode) {
    setMode(next);
    onClearError();
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (mode === "login") onLogin(username, password);
    else onRegister(username, password);
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(200,255,71,0.015)_2px,rgba(200,255,71,0.015)_4px)]" />

      <div className="relative z-10 w-full max-w-95 animate-fade-in border border-border border-t-2 border-t-accent bg-surface px-10 py-11">
        <div className="mb-1.5 flex items-baseline gap-2.5">
          <Wordmark />
          <span className="rounded-sharp border border-border px-1.5 py-0.5 text-[10px] tracking-[2px] text-muted">
            v2.0
          </span>
        </div>
        <p className="mb-8 text-[10px] tracking-[2px] text-muted">
          encrypted · real-time · minimal
        </p>

        <div className="relative mb-7 flex border-b border-border">
          <Tab
            active={mode === "login"}
            onClick={() => switchMode("login")}
            label="LOGIN"
          />
          <Tab
            active={mode === "register"}
            onClick={() => switchMode("register")}
            label="REGISTER"
          />
          <div
            className={`absolute -bottom-px h-0.5 w-1/2 bg-accent transition-[left] duration-250 ease-out ${
              mode === "login" ? "left-0" : "left-1/2"
            }`}
          />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4.5">
          <Field
            label="USERNAME"
            type="text"
            value={username}
            onChange={setUsername}
            placeholder="your_handle"
            autoComplete="username"
          />
          <Field
            label="PASSWORD"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder={mode === "login" ? "••••••••" : "min. 8 characters"}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
          />

          {error && (
            <div className="py-1.5 text-[11px] tracking-[0.5px] text-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="flex min-h-10.5 w-full items-center justify-center rounded-sharp bg-accent text-xs font-medium tracking-[2px] text-bg transition-opacity hover:not-disabled:opacity-85 active:not-disabled:scale-98 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <span className="size-3.5 animate-spin rounded-full border-2 border-black/30 border-t-bg" />
            ) : mode === "login" ? (
              "ENTER →"
            ) : (
              "CREATE ACCOUNT →"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

function Tab({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative z-10 flex-1 p-2.5 text-[10px] tracking-[2px] transition-colors ${
        active ? "text-accent" : "text-muted"
      }`}
    >
      {label}
    </button>
  );
}

function Field({
  label,
  type,
  value,
  onChange,
  placeholder,
  autoComplete,
}: {
  label: string;
  type: "text" | "password";
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  autoComplete: string;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[9px] tracking-[2px] text-muted">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className="w-full rounded-sharp border border-border bg-bg px-3 py-2.5 text-[13px] text-text outline-none transition-colors placeholder:text-muted focus:border-accent"
      />
    </label>
  );
}
