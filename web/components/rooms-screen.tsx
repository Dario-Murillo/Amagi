"use client";

import { Wordmark } from "@/components/wordmark";
import { useRooms } from "@/hooks/use-rooms";
import type { Room, Session } from "@/lib/types";

type Props = {
  session: Session;
  onJoin: (room: Room) => void;
  onLogout: () => void;
};

export default function RoomsScreen({ session, onJoin, onLogout }: Props) {
  const { rooms, error, isLoading, retry } = useRooms(session.token);

  return (
    <div className="fixed inset-0 flex animate-fade-in flex-col overflow-hidden">
      <header className="flex shrink-0 items-center justify-between border-b border-border bg-surface px-8 py-4">
        <div className="flex items-center gap-3">
          <Wordmark size="sm" />
          <span className="flex items-center gap-1.5 rounded-sharp border border-accent/30 px-2 py-0.75 text-[10px] tracking-[2px] text-accent">
            <span className="size-1.5 shrink-0 animate-glow rounded-full bg-accent shadow-[0_0_8px_var(--color-accent)]" />
            LIVE
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.75 rounded-sharp border border-border px-2.5 py-1.25 text-xs text-accent2">
            <span className="size-1.75 shrink-0 rounded-full bg-success shadow-[0_0_6px_var(--color-success)]" />
            {session.username}
          </span>
          <button
            type="button"
            onClick={onLogout}
            className="cursor-pointer rounded-sharp border border-border px-3 py-1.5 text-[10px] tracking-[1.5px] text-muted transition-colors hover:border-danger hover:text-danger"
          >
            LOGOUT
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-8 py-12">
        <div className="mb-9">
          <h2 className="mb-2 font-display text-5xl leading-none tracking-[4px] text-text">
            CHANNELS
          </h2>
          <p className="text-xs tracking-[1px] text-muted">
            Select a room to join the conversation
          </p>
        </div>

        <Channels
          rooms={rooms}
          error={error}
          isLoading={isLoading}
          onRetry={retry}
          onJoin={onJoin}
        />
      </main>
    </div>
  );
}

function Channels({
  rooms,
  error,
  isLoading,
  onRetry,
  onJoin,
}: {
  rooms: Room[];
  error: string;
  isLoading: boolean;
  onRetry: () => void;
  onJoin: (room: Room) => void;
}) {
  if (isLoading) {
    return (
      <p className="animate-glow text-[10px] tracking-[2px] text-muted">
        loading channels
      </p>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-start gap-3">
        <p className="text-xs text-danger">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="cursor-pointer rounded-sharp border border-border px-3 py-1.5 text-[10px] tracking-[1.5px] text-muted transition-colors hover:border-accent hover:text-accent"
        >
          RETRY
        </button>
      </div>
    );
  }

  // The rooms are seeded by migration, so an empty list means the database was
  // never migrated rather than a room nobody created yet.
  if (rooms.length === 0) {
    return (
      <p className="text-xs tracking-[1px] text-muted">
        No channels on the server yet.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
      {rooms.map((room) => (
        <button
          key={room.slug}
          type="button"
          onClick={() => onJoin(room)}
          className="group flex cursor-pointer flex-col gap-2 rounded-sharp border border-border bg-surface p-6 text-left text-text transition-[color,background-color,border-color,transform] hover:-translate-y-0.5 hover:border-accent hover:bg-surface2"
        >
          <div className="flex items-center justify-between">
            <span className="text-[1.1em] text-accent">#</span>
            <span className="rounded-sharp border border-accent2/30 px-1.75 py-0.5 text-[9px] uppercase tracking-[1.5px] text-accent2">
              {room.topic}
            </span>
          </div>
          <div className="font-display text-xl tracking-[2px] text-text">
            {room.name}
          </div>
          <div className="flex-1 text-xs leading-normal text-muted">
            {room.description}
          </div>
          <div className="mt-2 text-[10px] tracking-[1.5px] text-muted transition-colors group-hover:text-accent">
            ENTER ROOM →
          </div>
        </button>
      ))}
    </div>
  );
}
