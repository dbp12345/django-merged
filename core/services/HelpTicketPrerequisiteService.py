"""
Service for managing HelpTicket prerequisites logic.

This module contains simple functions to handle prerequisite checking
and status updates for Help Tickets.
"""


def is_prerequisite_completed(ticket):
    """
    Check if prerequisite ticket is completed.

    Args:
        ticket: HelpTicket instance

    Returns:
        True if prerequisite is completed or no prerequisite exists,
        False if prerequisite is not completed.
    """
    if not ticket.prerequisite:
        return True

    return ticket.prerequisite.status == "completed"


def should_be_waiting(ticket):
    """
    Check if ticket should have 'waiting' status.

    Args:
        ticket: HelpTicket instance

    Returns:
        True if ticket should be waiting, False otherwise.
    """
    if not ticket.prerequisite:
        return False

    return not is_prerequisite_completed(ticket)


def update_ticket_status_if_needed(ticket):
    """
    Update ticket status to 'waiting' if prerequisite is not completed,
    or restore previous status if prerequisite is completed.

    Args:
        ticket: HelpTicket instance

    Returns:
        True if status was changed, False otherwise.
    """
    if should_be_waiting(ticket):
        if ticket.status != "waiting":
            ticket.status = "waiting"
            return True
    elif ticket.status == "waiting" and is_prerequisite_completed(ticket):
        # Restore to default status if prerequisite is now completed
        ticket.status = "send"
        return True

    return False


def get_sibling_tickets(ticket):
    """
    Get all sibling tickets (tickets with the same parent).

    Args:
        ticket: HelpTicket instance

    Returns:
        QuerySet of sibling tickets (excluding current ticket)
    """
    from core.models.HelpTicket import HelpTicket

    parent = ticket.parent
    siblings = HelpTicket.objects.filter(parent=parent).exclude(pk=ticket.pk)

    return siblings


def check_prerequisite_cycle(ticket):
    """
    Check if prerequisite creates a cycle.

    Args:
        ticket: HelpTicket instance

    Returns:
        True if cycle detected, False otherwise.
    """
    if not ticket.prerequisite:
        return False

    seen = set()
    current = ticket.prerequisite

    while current:
        if current.pk == ticket.pk or current.pk in seen:
            return True
        seen.add(current.pk)
        current = current.prerequisite

    return False


def propagate_status_update(ticket):
    """
    When a ticket is completed, update all dependent tickets that are waiting.

    Args:
        ticket: HelpTicket instance that was just completed
    """
    if ticket.status != "completed":
        return

    # Find all tickets waiting for this one
    dependent_tickets = ticket.dependent_tickets.filter(status="waiting")

    for dependent in dependent_tickets:
        if is_prerequisite_completed(dependent):
            dependent.status = "send"
            dependent.save(update_fields=["status"])
