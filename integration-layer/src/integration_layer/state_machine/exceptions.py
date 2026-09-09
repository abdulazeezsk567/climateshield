"""Intervention state machine exceptions."""


class InterventionError(Exception):
    """Base exception for loan intervention workflows."""
    pass


class InvalidInterventionStateTransitionError(InterventionError):
    """Raised when an illegal lifecycle state transition is attempted."""

    def __init__(self, current_status: str, target_status: str, intervention_id: str):
        self.current_status = current_status
        self.target_status = target_status
        self.intervention_id = intervention_id
        super().__init__(
            f"Illegal intervention state transition for '{intervention_id}': "
            f"Cannot transition from '{current_status}' to '{target_status}'."
        )


class InterventionNotFoundError(InterventionError):
    """Raised when an intervention record cannot be found."""

    def __init__(self, intervention_id: str):
        self.intervention_id = intervention_id
        super().__init__(f"Loan intervention '{intervention_id}' was not found.")
