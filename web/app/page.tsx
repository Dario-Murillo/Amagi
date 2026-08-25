"use client";

import { useState } from "react";
import AuthScreen from "@/components/auth-screen";
import ChatScreen from "@/components/chat-screen";
import RoomsScreen from "@/components/rooms-screen";
import Splash from "@/components/splash";
import { useAuth } from "@/hooks/use-auth";
import type { Room } from "@/lib/types";

export default function Home() {
  const { session, ready, error, isLoading, login, register, logout, clearError } =
    useAuth();
  const [activeRoom, setActiveRoom] = useState<Room | null>(null);

  // Hold the first paint until the stored session has been read, so a returning
  // user never sees the auth screen flash before the room list.
  if (!ready) return <Splash />;

  if (!session) {
    return (
      <AuthScreen
        error={error}
        isLoading={isLoading}
        onLogin={login}
        onRegister={register}
        onClearError={clearError}
      />
    );
  }

  function handleLogout() {
    setActiveRoom(null);
    logout();
  }

  if (activeRoom) {
    return (
      <ChatScreen
        // Remount per room so the socket, messages, and roster all reset.
        key={activeRoom.slug}
        session={session}
        room={activeRoom}
        onLeave={() => setActiveRoom(null)}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <RoomsScreen
      session={session}
      onJoin={setActiveRoom}
      onLogout={handleLogout}
    />
  );
}
