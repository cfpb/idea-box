from idea.models import State

def get_first_state():
    """ Get the first state for an idea. """
    return State.objects.get(previous__isnull=True)
