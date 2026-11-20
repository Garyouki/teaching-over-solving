"""Teaching-over-solving diagnostic for LLM tutors."""

__version__ = "0.1.1"

from .diagnostic import (MTB_SOLVE, MTB_TEACH, DiagnosticError, composites,  # noqa: E402,F401
                         diagnose, load_scores, reference_scores, with_reference)
