import asyncio
import errno
import sys
from asyncio import AbstractEventLoop
from enum import Enum
from threading import Thread
from typing import Callable, Coroutine, Tuple, Any, Dict

from lib.config.loader import ConfigLoaderFileNotFoundError


class ExitCode(Enum):
    OK = 0
    GENERAL_ERROR = 1
    FILE_NOT_FOUND_ERROR = 2
    PORT_OPEN_ERROR = 5
    SIGINT = 130


def _process_exception(exception: BaseException) -> ExitCode:
    if isinstance(exception, FileNotFoundError) or \
        isinstance(exception, ConfigLoaderFileNotFoundError):
        return ExitCode.FILE_NOT_FOUND_ERROR
    elif isinstance(exception, OSError) and \
        exception.errno == errno.EADDRINUSE:
        return ExitCode.PORT_OPEN_ERROR
    elif isinstance(exception, KeyboardInterrupt):
        return ExitCode.SIGINT
    else:
        return ExitCode.GENERAL_ERROR


def _exception_handler(context: Dict[str, Any],
                       kill_run: Callable,
                       exit_code: asyncio.Future) -> None:
    """Handles exceptions thrown by running loop.

    :param context: The context set by set_exception_handler method from which
    to extract thrown exception object.
    :param kill_run: Function used to kill running loop.
    :param exit_code: Future for setting program exit code.
    """
    exception = context.get('exception')
    print("_exception_handler: ", exception)

    exit_code.set_result(_process_exception(exception).value)

    kill_run()


def run(
    main_coro: Callable[
        [AbstractEventLoop, AbstractEventLoop],
        Coroutine[None, None, None]
    ]
) -> None:
    # Create communication loop which will handle abus-related data flow
    # throughout the application.
    # Everything else will be done on main thread (the one this code is
    # currently running on).
    #asyncio.run(_run(main_coro))

    communication_loop, kill_communication_loop = (
        create_thread_loop("CommunicationThread")
    )

    running_loop = asyncio.new_event_loop()
    completed = running_loop.create_future()
    exit_code = asyncio.Future()

    try:
        def kill_run_loop():
            kill_communication_loop()
            completed.done()
            for t in asyncio.all_tasks():
                t.cancel()
            running_loop.stop()

        running_loop.set_exception_handler(
            lambda _, context: _exception_handler(
                context, kill_run_loop, exit_code
            )
        )
        running_loop.create_task(main_coro(running_loop, communication_loop))
        running_loop.run_until_complete(completed)
        running_loop.close()
        print("x")
        if exit_code.done():
            sys.exit(exit_code.result())
    except KeyboardInterrupt:
        kill_communication_loop()
        sys.exit(ExitCode.SIGINT.value)
    except Exception as ex:
        if exit_code.done():
            sys.exit(exit_code.result())
        else:
            sys.exit(_process_exception(ex).value)


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
        if not loop.is_closed():
            loop.call_soon_threadsafe(lambda: kill_switch.set_result(True))

    return loop, kill
