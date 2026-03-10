# app/core/events.py

class AuditEvent:
    CASE_CREATED = "CASE_CREATED"
    CASE_VIEWED = "CASE_VIEWED"
    CASES_LISTED = "CASES_LISTED"
    CASE_NOT_FOUND = "CASE_NOT_FOUND"


class ActorType:
    SYSTEM = "system"
    HUMAN = "human"
    AI = "ai"