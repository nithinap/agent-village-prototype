"""All DB query functions. Audience-aware: owner queries are never called from visitor paths."""

from typing import Optional
from app.db.client import get_supabase


# ── Agent profile ──

def get_agent(agent_id: str) -> Optional[dict]:
    db = get_supabase()
    r = db.table("living_agents").select("*").eq("id", agent_id).maybe_single().execute()
    return r.data


# ── Owner auth ──

def get_owner_id(agent_id: str) -> Optional[str]:
    db = get_supabase()
    r = db.table("agent_owners").select("owner_id").eq("agent_id", agent_id).maybe_single().execute()
    return r.data["owner_id"] if r.data else None


# ── Threads ──

def get_or_create_thread(agent_id: str, actor_type: str, actor_id: str) -> dict:
    db = get_supabase()
    r = (db.table("conversation_threads")
         .select("*")
         .eq("agent_id", agent_id)
         .eq("actor_type", actor_type)
         .eq("actor_id", actor_id)
         .eq("status", "active")
         .maybe_single()
         .execute())
    if r.data:
        return r.data
    r = (db.table("conversation_threads")
         .insert({"agent_id": agent_id, "actor_type": actor_type, "actor_id": actor_id})
         .execute())
    return r.data[0]


# ── Messages ──

def get_recent_messages(thread_id: str, limit: int = 20) -> list[dict]:
    db = get_supabase()
    r = (db.table("conversation_messages")
         .select("role, body, created_at")
         .eq("thread_id", thread_id)
         .order("created_at", desc=False)
         .limit(limit)
         .execute())
    return r.data


def insert_message(thread_id: str, agent_id: str, role: str, body: str) -> dict:
    db = get_supabase()
    r = (db.table("conversation_messages")
         .insert({"thread_id": thread_id, "agent_id": agent_id, "role": role, "body": body})
         .execute())
    db.table("conversation_threads").update({"last_message_at": "now()"}).eq("id", thread_id).execute()
    return r.data[0]


# ── Owner memories ──

def get_memories(agent_id: str, owner_id: str, limit: int = 10) -> list[dict]:
    db = get_supabase()
    r = (db.table("agent_relationship_memory")
         .select("*")
         .eq("agent_id", agent_id)
         .eq("owner_id", owner_id)
         .order("created_at", desc=True)
         .limit(limit)
         .execute())
    return r.data


def insert_memory(agent_id: str, owner_id: str, memory_text: str,
                   memory_type: str = "fact", sensitivity: str = "private") -> dict:
    db = get_supabase()
    r = (db.table("agent_relationship_memory")
         .insert({
             "agent_id": agent_id,
             "owner_id": owner_id,
             "memory_text": memory_text,
             "memory_type": memory_type,
             "sensitivity": sensitivity,
             "source": "owner_chat",
         })
         .execute())
    return r.data[0]


# ── Public feed (read-only, used by visitor + public paths) ──

def get_recent_diary(agent_id: str, limit: int = 5) -> list[dict]:
    db = get_supabase()
    r = (db.table("living_diary")
         .select("text, entry_date, created_at")
         .eq("agent_id", agent_id)
         .order("created_at", desc=True)
         .limit(limit)
         .execute())
    return r.data


def get_recent_logs(agent_id: str, limit: int = 5) -> list[dict]:
    db = get_supabase()
    r = (db.table("living_log")
         .select("text, emoji, created_at")
         .eq("agent_id", agent_id)
         .order("created_at", desc=True)
         .limit(limit)
         .execute())
    return r.data
