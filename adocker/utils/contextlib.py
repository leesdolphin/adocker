"""
An asynchronous-flavoured `contextlib`.

This contains significant portions of code from the `CPython project`_;
specifically the outline of :class:`AsyncExitStack` which has an almost
identical API to :class:`contextlib.ExitStack`

.. _CPython project: https://github.com/python/cpython/blob/3.6/Lib/contextlib.py#L259

This source file is based off the significant work of the Python developers,
the Python code is released under the following license:

    Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
    2011, 2012, 2013, 2014, 2015, 2016, 2017 Python Software Foundation. All
    rights reserved.

    Copyright (c) 2000 BeOpen.com. All rights reserved.

    Copyright (c) 1995-2001 Corporation for National Research Initiatives. All
    rights reserved.

    Copyright (c) 1991-1995 Stichting Mathematisch Centrum. All rights
    reserved.

    See the file "PYTHON-LICENSE" for information on the history of this
    software, terms & conditions for usage, and a DISCLAIMER OF ALL WARRANTIES.
"""

import abc
import collections
import inspect
import sys


class AsyncContextManager(metaclass=abc.ABCMeta):
    async def __aenter__(self):
        return self

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        return NotImplemented


class AsyncExitStack(AsyncContextManager):
    """Context manager for dynamic management of a stack of exit callbacks
    For example::

        async with AsyncExitStack() as stack:
            files = [stack.enter_context(open(fname)) for fname in filenames]
            # All opened files will automatically be closed at the end of
            # the with statement, even if attempts to open files later
            # in the list raise an exception
            session = await stack.enter_async_context(aiohttp.ClientSession())
            # Any errors now will close the session asynchronously.

    .. warning::
        Calling methods on this object whilst a call to
        :func:`enter_async_context` is in progress(for example during )
    """

    def __init__(self):
        self._exit_callbacks = collections.deque()

    def pop_all(self):
        """Preserve the context stack by transferring it to a new instance"""
        new_stack = type(self)()
        new_stack._exit_callbacks = self._exit_callbacks
        self._exit_callbacks = collections.deque()
        return new_stack

    def _push_cm_exit(self, cm, cm_exit):
        """Helper to correctly register callbacks to __exit__ methods"""

        def _exit_wrapper(*exc_details):
            return cm_exit(cm, *exc_details)

        _exit_wrapper.__self__ = cm
        self.push(_exit_wrapper)

    def _push_cm_aexit(self, cm, cm_aexit):
        """Helper to correctly register callbacks to __aexit__ methods"""

        async def _exit_wrapper(*exc_details):
            return await cm_aexit(cm, *exc_details)

        _exit_wrapper.__self__ = cm
        self.push(_exit_wrapper)

    def push(self, exit):
        """Registers a callback with the standard __exit__ method signature
        Can suppress exceptions the same way __exit__ methods can.
        Also accepts any object with an __exit__ method (registering a call
        to the method instead of the object itself).

        Note: This looks for exit methods in the following order:
        ``exit.__aexit__``, ``exit.__exit__``, ``exit``. It will also handle
        the case where ``exit`` is an asynchronous
        function(:func:`inspect.isawaitable` returns ``True``) by awaiting it
        during exiting.
        """
        # We use an unbound method rather than a bound method to follow
        # the standard lookup behaviour for special methods
        _cb_type = type(exit)
        try:
            aexit_method = _cb_type.__aexit__
        except AttributeError:
            try:
                exit_method = _cb_type.__exit__
            except AttributeError:
                # Not a context manager, so assume its a callable
                self._exit_callbacks.append(exit)
            else:
                self._push_cm_exit(exit, exit_method)
        else:
            self._push_cm_aexit(exit, aexit_method)
        return exit  # Allow use as a decorator

    def callback(self, callback, *args, **kwds):
        """Registers an arbitrary callback and arguments.
        Cannot suppress exceptions.

        If ``callback`` is an awaitable function(:func:`inspect.isawaitable`
        returns ``True``), then the the function will be awaited on in the
        ``__aexit__`` method.
        """
        if inspect.isawaitable(callback):
            async def _exit_wrapper(exc_type, exc, tb):
                await callback(*args, **kwds)
        else:

            def _exit_wrapper(exc_type, exc, tb):
                callback(*args, **kwds)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help with introspection
        _exit_wrapper.__wrapped__ = callback
        self.push(_exit_wrapper)
        return callback  # Allow use as a decorator

    def enter_context(self, cm):
        """Enters the supplied context manager
        If successful, also pushes its __exit__ method as a callback and
        returns the result of the __enter__ method.
        """
        # We look up the special methods on the type to match the with statement
        _cm_type = type(cm)
        _exit = _cm_type.__exit__
        result = _cm_type.__enter__(cm)
        self._push_cm_exit(cm, _exit)
        return result

    async def enter_async_context(self, cm):
        """Enters the supplied asynchronous context manager
        If successful, also pushes its __aexit__ method as a callback and
        returns the result of awaiting the __aenter__ method.

        """
        # We look up the special methods on the type to match the with statement
        _cm_type = type(cm)
        _aexit = _cm_type.__aexit__
        result = await _cm_type.__aenter__(cm)
        self._push_cm_aexit(cm, _aexit)
        return result

    async def close(self):
        """Immediately unwind the context stack"""
        await self.__aexit__(None, None, None)

    async def __aexit__(self, *exc_details):
        received_exc = exc_details[0] is not None

        # We manipulate the exception state so it behaves as though
        # we were actually nesting multiple with statements
        frame_exc = sys.exc_info()[1]

        def _fix_exception_context(new_exc, old_exc):
            # Context may not be correct, so find the end of the chain
            while 1:
                exc_context = new_exc.__context__
                if exc_context is old_exc:
                    # Context is already set correctly (see issue 20317)
                    return
                if exc_context is None or exc_context is frame_exc:
                    break
                new_exc = exc_context
            # Change the end of the chain to point to the exception
            # we expect it to reference
            new_exc.__context__ = old_exc

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = False
        pending_raise = False
        while self._exit_callbacks:
            cb = self._exit_callbacks.pop()
            try:
                if inspect.isawaitable(cb):
                    result = await cb(*exc_details)
                else:
                    result = cb(*exc_details)
                if result:
                    suppressed_exc = True
                    pending_raise = False
                    exc_details = (None, None, None)
            except:  # noqa: E722 - Bare Except
                new_exc_details = sys.exc_info()
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc_details[1], exc_details[1])
                pending_raise = True
                exc_details = new_exc_details
        if pending_raise:
            try:
                # bare "raise exc_details[1]" replaces our carefully
                # set-up context
                fixed_ctx = exc_details[1].__context__
                raise exc_details[1]
            except BaseException:
                exc_details[1].__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc
