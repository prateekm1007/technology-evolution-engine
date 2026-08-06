"""Inventor Agent - Generates transformations. Law 1: Transformation, not object."""


class Inventor:
    """Generates transformation candidates via rewrite operators."""

    OPERATORS = [
        'eliminate', 'substitute', 'miniaturize', 'distribute',
        'modularize', 'software_substitution',
        'change_energy_domain', 'change_information_domain'
    ]

    def __init__(self, graph):
        self.graph = graph

    def generate(self, undesirable_state, desirable_state, operator):
        if operator not in self.OPERATORS:
            raise ValueError(f'Unknown operator: {operator}')
        return {
            'undesirable_state': undesirable_state,
            'desirable_state': desirable_state,
            'operator': operator,
            'status': 'PROPOSED'
        }