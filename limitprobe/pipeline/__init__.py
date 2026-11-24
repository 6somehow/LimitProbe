"""One entry point for the whole limitation pipeline (paper side + code side + integration).

    python -m pipeline init  ...              # write data/<id>/artifact.json for a new paper
    python -m pipeline status <id>            # which stages are done, what is missing
    python -m pipeline run <id> [--pdf P]     # run what is missing; output: all limitations of <id>
    python -m pipeline setup-paperside        # install Zhaopeng's paper-side dependencies (pip + npm)

See docs/10_pipeline.md.
"""
