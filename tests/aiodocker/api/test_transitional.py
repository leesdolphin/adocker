import pytest

import adocker.api.base as a_base
import adocker.api.transitional as a_transitional
import adocker.errors as a_errors


async def test_deprecated_docker_host(adocker_api):
    with pytest.warns(
            a_errors.AioDockerDeprecationWarning,
            match=r'Accessing `.docker_host` is deprecated.'):
        host = adocker_api.docker_host
    assert adocker_api.base_url == host

    host = 'localhost:7000'
    with pytest.warns(
            a_errors.AioDockerDeprecationWarning,
            match=r'Setting `.docker_host` is deprecated.'):
        adocker_api.docker_host = host
    assert adocker_api.base_url == host


async def test_deprecated_api_version_with_v(adocker_api):
    version = '1.27'
    with pytest.warns(
            a_errors.AioDockerDeprecationWarning,
            match=r'Setting `.api_version` a "v.*? is deprecated.'):
        adocker_api.api_version = 'v' + version
    assert adocker_api.api_version == version


async def test_no_deprecated_api_version_without_v(adocker_api):
    version = '1.27'
    # TODO: have a test that asserts the deprecation warnings are being caught.
    adocker_api.api_version = version
    assert adocker_api.api_version == version
