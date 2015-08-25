from idea.models import State

def get_first_state():
    """ Get the first state for an idea. """
    #return State.objects.get(previous__isnull=True)
    # previous__isnull breaks functionality if someone creates a new state
    # without a previous state set.  since we know the initial state
    # is id=1 per fixtures/state.json, use that instead.
    return State.objects.get(id=1)
