"""All DB query functions. Audience-aware: owner queries are never called from visitor paths."""

from typing import Optional
from app.db.client import get_supabase


# ── Agent profile ──

def get_agent(agent_id: str) -> Optional[dict]:
    db = get_supabase()
    r = db.table("living_agents").select("*").eq("id", agent_id).limit(1).execute()
    return r.data[0] if r.data else None


# ── Owner auth ──

def get_owner_id(agent_id: str) -> Optional[str]:
    db = get_supabase()
    r = db.table("agent_owners").select("owner_id").eq("agent_id", agent_id).limit(1).execute()
    return r.data[0]["owner_id"] if r.data else None


# ── Threads ──

def get_or_create_thread(agent_id: str, actor_type: str, actor_id: str) -> dict:
    db = get_supabase()
    r = (db.table("conversation_threads")
         .select("*")
         .eq("agent_id", agent_id)
         .eq("actor_type", actor_type)
         .eq("actor_id", actor_id)
         .eq("status", "active")
         .limit(1)
         .execute())
    if r.data:
        return r.data[0]
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


def get_recent_activity(agent_id: str, limit: int = 5) -> list[dict]:
    db = get_supabase()
    r = (db.table("living_activity_events")
         .select("event_type, content, created_at")
         .eq("agent_id", agent_id)
         .order("created_at", desc=True)
         .limit(limit)
         .execute())
    return r.data


# ── Public writes (proactive behavior) ──

def insert_diary(agent_id: str, text: str) -> dict:
    db = get_supabase()
    r = (db.table("living_diary")
         .insert({"agent_id": agent_id, "text": text})
         .execute())
    return r.data[0]


def update_agent_status(agent_id: str, status: str):
    db = get_supabase()
    db.table("living_agents").update({"status": status}).eq("id", agent_id).execute()


# ── Jobs ──

def get_due_jobs(job_type: str = "public_act") -> list[dict]:
    db = get_supabase()
    r = (db.table("agent_jobs")
         .select("*")
         .eq("job_type", job_type)
         .is_("completed_at", "null")
         .is_("locked_at", "null")
         .lte("run_after", "now()")
         .order("priority", desc=False)
         .limit(10)
         .execute())
    return r.data


def lock_job(job_id: str):
    from datetime import datetime, timezone
    db = get_supabase()
    db.table("agent_jobs").update({"locked_at": datetime.now(timezone.utc).isoformat()}).eq("id", job_id).execute()


def complete_job(job_id: str):
    from datetime import datetime, timezone
    db = get_supabase()
    db.table("agent_jobs").update({"completed_at": datetime.now(timezone.utc).isoformat()}).eq("id", job_id).execute()


def reschedule_job(agent_id: str, job_type: str = "public_act", delay_minutes: int = 120):
    """Create a new job scheduled delay_minutes from now."""
    from datetime import datetime, timezone, timedelta
    import random
    jitter = random.randint(0, 30)
    run_after = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes + jitter)
    db = get_supabase()
    db.table("agent_jobs").insert({
        "agent_id": agent_id,
        "job_type": job_type,
        "run_after": run_after.isoformat(),
    }).execute()


# ── Conversation activity check (for proactive trigger) ──

def has_recent_conversation(agent_id: str) -> bool:
    """Check if agent had any conversation since its last diary post."""
    db = get_supabase()
    # Get last diary post time
    diary = (db.table("living_diary")
             .select("created_at")
             .eq("agent_id", agent_id)
             .order("created_at", desc=True)
             .limit(1)
             .execute())
    last_post = diary.data[0]["created_at"] if diary.data else "2000-01-01T00:00:00Z"

    # Check for any messages since then
    msgs = (db.table("conversation_messages")
            .select("id")
            .eq("agent_id", agent_id)
            .gt("created_at", last_post)
            .limit(1)
            .execute())
    return bool(msgs.data)


# ── Bootstrap ──

def insert_agent(name: str, bio: str, visitor_bio: str, status: str,
                 accent_color: str = "#ffffff", showcase_emoji: str = "✨") -> dict:
    db = get_supabase()
    r = (db.table("living_agents")
         .insert({
             "name": name,
             "bio": bio,
             "visitor_bio": visitor_bio,
             "status": status,
             "accent_color": accent_color,
             "showcase_emoji": showcase_emoji,
         })
         .execute())
    return r.data[0]


def insert_owner(agent_id: str, owner_id: str) -> dict:
    db = get_supabase()
    r = (db.table("agent_owners")
         .insert({"agent_id": agent_id, "owner_id": owner_id})
         .execute())
    return r.data[0]


def insert_initial_job(agent_id: str):
    db = get_supabase()
    db.table("agent_jobs").insert({
        "agent_id": agent_id,
        "job_type": "public_act",
    }).execute()
