import type { Room } from "@/lib/types";

// Fixed rooms — swap these out for API calls once GET /rooms is wired to the DB.
export const FIXED_ROOMS: Room[] = [
  {
    id: "general",
    name: "General",
    topic: "Chat",
    description: "Open conversation for everyone.",
  },
  {
    id: "tech",
    name: "Tech",
    topic: "Dev",
    description: "Programming, tools, and everything code.",
  },
  {
    id: "random",
    name: "Random",
    topic: "Off-topic",
    description: "Anything goes. No rules here.",
  },
  {
    id: "ideas",
    name: "Ideas",
    topic: "Product",
    description: "Share what you're building or thinking about.",
  },
  {
    id: "help",
    name: "Help",
    topic: "Support",
    description: "Ask questions, get unstuck.",
  },
];
