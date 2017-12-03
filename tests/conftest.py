import asyncio

import pytest

import adocker.api as a_api
import adocker.errors as a_errors


@pytest.fixture()
def adocker_api(request, event_loop):
    asyncio.set_event_loop(event_loop)
    with pytest.warns(a_errors.AioDockerDeprecationWarning):
        api = a_api.APIClient()

    def cleanup():
        event_loop.run_until_complete(api.close())
    request.addfinalizer(cleanup)
    return api
