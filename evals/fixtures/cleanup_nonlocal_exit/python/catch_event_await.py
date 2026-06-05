import asyncio


class StepWriter:
    def __init__(self) -> None:
        self._committed: dict[str, asyncio.Event] = {}

    async def create_step(self, step_id: str, parent_id: str) -> None:
        if step_id and step_id not in self._committed:
            self._committed[step_id] = asyncio.Event()  # acquire

        # An await BEFORE the try: a CancelledError raised here (client
        # disconnect / timeout / shutdown) unwinds before the finally is armed,
        # so the event is popped/set never runs — every later reader waiting on
        # this step's event hangs forever.
        if event := self._committed.get(parent_id):
            await event.wait()

        try:
            await self._call("create_step", step_id)
        finally:
            if e := self._committed.pop(step_id, None):
                e.set()  # cleanup — only runs if the try was entered
