# HCI_EVALUATION.md

This document maps Nielsen's 10 usability heuristics to AMATS design choices.

- Visibility of system status: Dashboard shows real-time counts, recent activity feed, and network last-seen timestamps.
- Match between system and the real world: Asset fields (serial, model, location) mirror physical labeling and QR codes use UTV-XXX format.
- User control & freedom: Issue/return workflows include undo and confirmation modals.
- Consistency & standards: Bootstrap 5 + Crispy forms maintain consistent UI patterns.
- Error prevention: Form validation, dropdowns for categories, and confirmation steps for destructive actions.
- Recognition rather than recall: Showing asset history and recent assignments reduces memory load.
- Flexibility & efficiency: Keyboard shortcuts, quick-scan QR flow, and filters for power users.
- Aesthetic & minimal design: Clean dashboard with charts and sensible color usage.
- Help users recognize, diagnose, recover: Helpful error pages and in-form guidance.
- Help & documentation: Inline help text, printable QR labels, and this project's documentation set.
