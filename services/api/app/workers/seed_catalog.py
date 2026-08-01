"""Catalog seed fixtures (Growth Stories, Tools, Mentors). Owner: Backend. milestones.md M6.

Tagged against AIA's bottleneck taxonomy (scoring/constants.py-adjacent)
and the demo persona's stage/identity so AIS's ranking has real tags to
match against. Deterministic, upserted by fixed id — same idempotent
pattern as the rest of seed.py.
"""

from __future__ import annotations

from app.models.catalog import GrowthStoryModel, MentorModel, ToolModel

_STORIES = [
    ("story_public_speaking_fear", "From Shaking Hands to the Main Stage", "Priya N.",
     "Overcame stage fright by starting with 60-second Toastmasters slots.",
     "Now runs a monthly speaking meetup.", ["public_speaker"], ["beginner"], ["confidence"]),
    ("story_ship_first_project", "Shipping My First Public Repo", "Dev K.",
     "Went from tutorial hoarding to publishing one small tool a month.",
     "First open-source project hit 200 stars.", ["builder"], ["beginner"], ["execution"]),
    ("story_consistency_streak", "The 100-Day Build Streak", "Amara O.",
     "Used a public commit streak to break a stop-start pattern.",
     "Shipped 3 side projects in 100 days.", ["builder"], ["intermediate"], ["consistency"]),
    ("story_accountability_partner", "Finding My Accountability Partner", "Leo M.",
     "Paired with a peer for weekly demo days to stay honest about progress.",
     "Never missed a weekly demo for 6 months.", ["builder"], ["intermediate"], ["accountability"]),
    ("story_networking_cold_dm", "Cold DMs That Changed My Career", "Sara T.",
     "Started reaching out to one new person a week in the field.",
     "Landed a mentor and a job offer within a year.", ["public_speaker"], ["intermediate"], ["networking"]),
    ("story_burnout_recovery", "Recovering From Builder Burnout", "Jon P.",
     "Learned to ship smaller and rest without guilt.",
     "Sustainable weekly cadence for 2 years since.", ["builder"], ["advanced"], ["burnout"]),
    ("story_focus_deep_work", "Reclaiming Focus From the Feed", "Mina R.",
     "Replaced doomscrolling blocks with scheduled deep-work sprints.",
     "Doubled weekly creation output.", ["builder"], ["beginner"], ["focus"]),
    ("story_knowledge_to_teaching", "From Learner to Teacher", "Chidi A.",
     "Started writing up what she learned instead of just consuming it.",
     "Now teaches a weekly community workshop.", ["public_speaker"], ["advanced"], ["knowledge"]),
]

_TOOLS = [
    ("tool_toastmasters", "Toastmasters Local Club", "Structured public-speaking practice with feedback.",
     "https://www.toastmasters.org", "Attend one meeting as a guest this week.",
     ["beginner"], ["confidence"]),
    ("tool_github", "GitHub", "Host and publish code publicly.",
     "https://github.com", "Push your first commit to a public repo.",
     ["beginner"], ["execution"]),
    ("tool_obsidian", "Obsidian", "Personal knowledge base for notes and reflections.",
     "https://obsidian.md", "Create a daily note template.",
     ["beginner"], ["knowledge"]),
    ("tool_notion", "Notion", "Plan and track micro-missions and habits.",
     "https://notion.so", "Set up a weekly commitment tracker.",
     ["beginner"], ["consistency"]),
    ("tool_calendar", "Google Calendar", "Block deep-work focus sessions.",
     "https://calendar.google.com", "Block one 45-minute focus session tomorrow.",
     ["beginner"], ["focus"]),
    ("tool_discord_community", "A Builder Discord Community", "Peer accountability and demo days.",
     "https://discord.com", "Post your current project in #introductions.",
     ["intermediate"], ["accountability"]),
    ("tool_linkedin", "LinkedIn", "Reach out and build a professional network.",
     "https://linkedin.com", "Send one thoughtful connection request today.",
     ["intermediate"], ["networking"]),
    ("tool_anki", "Anki", "Spaced-repetition flashcards for retaining what you learn.",
     "https://apps.ankiweb.net", "Create a 10-card deck from this week's learning.",
     ["beginner"], ["knowledge"]),
    ("tool_figma", "Figma", "Sketch and share visual project ideas quickly.",
     "https://figma.com", "Mock up one screen of your next project.",
     ["intermediate"], ["execution"]),
    ("tool_cursor", "Cursor", "AI-assisted editor for shipping code faster.",
     "https://cursor.sh", "Use it to finish one small feature this week.",
     ["intermediate"], ["execution"]),
]

_MENTORS = [
    ("mentor_priya", "Priya N.", "Overcame speaking anxiety to become a community speaker.",
     ["public speaking", "confidence building"], ["beginner"], ["confidence"]),
    ("mentor_dev", "Dev K.", "Shipped their first public project after years of tutorials.",
     ["shipping", "open source"], ["beginner"], ["execution"]),
    ("mentor_amara", "Amara O.", "Built a 100-day consistency streak from scratch.",
     ["habit building", "consistency"], ["intermediate"], ["consistency"]),
    ("mentor_jon", "Jon P.", "Recovered from burnout into a sustainable builder rhythm.",
     ["sustainable pace", "burnout recovery"], ["advanced"], ["burnout"]),
    ("mentor_sara", "Sara T.", "Grew a network from cold outreach alone.",
     ["networking", "career growth"], ["intermediate"], ["networking"]),
]


def seed_catalog(session) -> tuple[int, int, int]:
    """Idempotent — upserts by fixed id. Returns (stories, tools, mentors) inserted counts."""
    inserted = [0, 0, 0]

    for sid, title, author, summary, outcome, identity_tags, stage_tags, bottleneck_tags in _STORIES:
        if session.get(GrowthStoryModel, sid) is None:
            session.add(
                GrowthStoryModel(
                    id=sid, title=title, author=author, summary=summary, outcome=outcome,
                    identity_tags=identity_tags, stage_tags=stage_tags, bottleneck_tags=bottleneck_tags,
                )
            )
            inserted[0] += 1

    for tid, name, description, url, starter_action, stage_tags, bottleneck_tags in _TOOLS:
        if session.get(ToolModel, tid) is None:
            session.add(
                ToolModel(
                    id=tid, name=name, description=description, url=url,
                    starter_action=starter_action, stage_tags=stage_tags, bottleneck_tags=bottleneck_tags,
                )
            )
            inserted[1] += 1

    for mid, name, journey, strengths, stage_tags, bottleneck_tags in _MENTORS:
        if session.get(MentorModel, mid) is None:
            session.add(
                MentorModel(
                    id=mid, name=name, journey=journey, strengths=strengths,
                    stage_tags=stage_tags, bottleneck_tags=bottleneck_tags,
                )
            )
            inserted[2] += 1

    session.commit()
    return tuple(inserted)
