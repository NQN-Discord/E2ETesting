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

    all_headers = []
    for examples in scenario.examples:
        assert len(examples.table.headings) == 1
        header = examples.table.headings[0]
        assert header not in all_headers
        all_headers.append(header)

    tables = [examples.table for examples in scenario.examples]

    new_table = Table(all_headers)
    for row in itertools.product(*tables):
        new_table.add_row(Row(headings=all_headers, cells=[r.cells[0] for r in row]))

    scenario.examples[0].table = new_table
    scenario.examples = [scenario.examples[0]]
