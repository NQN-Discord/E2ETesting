import itertools
from behave.model import Table, Row


def process_tags(context):
    """
    Process scenarios with special tags.
    This function should be called in before_all.
    """
    tag_handlers = {"matrix": expand_matrix_tag}

    for feature in context._runner.features:
        for scenario in feature.scenarios:
            for tag in scenario.tags:
                if tag in tag_handlers:
                    tag_handlers[tag](scenario)


def expand_matrix_tag(scenario):
    if len(scenario.examples) < 2:
        return

    _all_headers = set()
    all_headers = []
    for examples in scenario.examples:
        assert _all_headers & set(examples.table.headings) == set()
        _all_headers.update(examples.table.headings)
        all_headers.extend(examples.table.headings)

    tables = [examples.table for examples in scenario.examples]

    new_table = Table(all_headers)
    for row in itertools.product(*tables):
        new_table.add_row(Row(headings=all_headers, cells=[cell for r in row for cell in r]))

    scenario.examples[0].table = new_table
    scenario.examples = [scenario.examples[0]]
