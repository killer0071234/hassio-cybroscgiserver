import asyncio
from asyncio import AbstractEventLoop
from threading import Thread
from typing import Callable, Coroutine, Tuple


def run(main_coro: Callable[
    [AbstractEventLoop, AbstractEventLoop],
    Coroutine[None, None, None]
]):
    # Create communication loop which will handle abus-related data flow
    # throughout the application.
    # Everything else will be done on main thread (the one this code is
    # currently running on).
    communication_loop, kill_communication_loop = (
        create_thread_loop("CommunicationThread")
    )

    try:
        running_loop = asyncio.new_event_loop()
        running_loop.create_task(main_coro(running_loop, communication_loop))
        running_loop.run_forever()
    except KeyboardInterrupt:
        kill_communication_loop()
    except BaseException as e:
        print(e)


def create_thread_loop(name: str) -> Tuple[AbstractEventLoop, Callable]:
    """Create new thread and then start new asyncio event loop inside it.

    Args:
        name: Name of the new thread.

    Returns:
        Tuple containing asyncio loop and `kill` function which will stop the
        loop and the associated thread.
    """

    loop = asyncio.new_event_loop()
    kill_switch = loop.create_future()

    # this function will be called in newly created thread.
    def start_loop(loop_to_start):
        asyncio.set_event_loop(loop_to_start)
        loop_to_start.run_until_complete(kill_switch)

    t = Thread(target=start_loop, args=(loop,), name=name)
    t.start()

    def kill():
        loop.call_soon_threadsafe(lambda: kill_switch.set_result(True))

    return loop, kill
