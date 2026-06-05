import asyncio


class StepWriter:
    def __init__(self) -> None:
        self._committed: dict[str, asyncio.Event] = {}

    async def create_step(self, step_id: str, parent_id: str) -> None:
        if step_id and step_id not in self._committed:
            self._committed[step_id] = asyncio.Event()  # acquire

        # The try spans every await, so a CancelledError at any wait point still
        # runs the finally and sets the event. Nothing exitable sits in the gap
        # between the acquire and the guard.
        try:
            if event := self._committed.get(parent_id):
                await event.wait()
            await self._call("create_step", step_id)
        finally:
            if e := self._committed.pop(step_id, None):
                e.set()
