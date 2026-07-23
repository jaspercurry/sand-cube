# CAD workflow acceleration brief

## User request

> Is there any other process work we should do here? Like all the feedback you've given is about this specific enclosure and about how we should go about building it, etc. but is there anything we should work on with regards to how the AI is working? It still feels like it's taking a long time per change but maybe that's just normal.

> I think I told it to reread that long prompt every time it re-compacted, which is probably stupid of me so that's on me
>
> Could we not do this now? I know that things are working now but it's just doing its thing. Why not just let it go while we kind of change the world around it and if it notices, great. If it doesn't, that's okay

## Interpreted scope

Improve the repository-level AI CAD feedback process without touching, moving,
or observing the implementation details of the currently running enclosure
change. Work in an isolated branch and worktree. The result should be safe to
merge after that task finishes and should not require the running agent to
adopt it mid-task.

The durable project brief and verification contract remain authoritative.
Compaction recovery should use a small current-state record that points to
those documents and verifies them by hash instead of repeatedly injecting the
entire prompt.
