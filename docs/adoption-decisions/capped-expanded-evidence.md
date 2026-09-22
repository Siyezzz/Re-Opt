# Capped Proposal Adoption Decision

weights: weights/proposed-capped-expanded-evidence.json
cap_review: docs/weight-caps/expanded-evidence.md
evidence_review: docs/outcome-evidence/simulated-next-outcome.md
decision: defer

Decision signals:

- adoption_status: clean
- largest_clean_ratio: 0.011
- evidence_source: synthetic simulation
- all_rounded_utility_deltas_zero: True

Rationale:

- The proposal is regression-clean, but the largest clean cap is below the review threshold.
- Every seed utility delta rounds to +0.000, so the change has no visible benchmark effect.
- The supporting outcome is synthetic, so this should wait for observed task evidence.
