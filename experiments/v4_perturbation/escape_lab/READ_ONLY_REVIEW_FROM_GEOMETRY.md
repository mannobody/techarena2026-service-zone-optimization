# Geometry-lab review of frozen escape component

Read-only comments received from /root/geometry during the development screen:

* Incremental journal hashing is symmetric for add/remove and open/close, with
  disjoint site/office token ranges; the native clear/undo journal invariant is
  required and preserved by the inspected hooks.
* try_dp synchronizes the hash and tick restore invalidates worker wsig.
* Mode0 has the original acceptance short-circuit and RNG behavior.
* Mode4 changes the post-LNS trajectory by restoring its retained best; label it
  retention-only, not pure telemetry.
* Full verification on a newly observed local record is uninterruptible and can
  cross a local deadline; measured process wall-time remains necessary.
* Episode statistics are endpoint observations. Global incumbent publication
  remains safe through the unchanged offer.

These comments led to reporting clarifications, not a change to frozen quality
code or parameters. No correctness-blocking finding was identified in this review.
