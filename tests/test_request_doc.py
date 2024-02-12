"""Test RequestDoc model functionality."""

import ipaddress

# Third-Party Libraries
import pytest
from pydantic import ValidationError
from hypothesis import given, strategies as st

# cisagov Libraries
from cyhy_db.models import RequestDoc
from cyhy_db.models.request_doc import Agency


async def test_init():
    # Create a RequestDoc object

    request_doc = RequestDoc(
        agency=Agency(
            name="Cybersecurity and Infrastructure Security Agency", acronym="CISA"
        )
    )

    await request_doc.save()

    # Verify that the id was set to the acronym
    assert (
        request_doc.id == request_doc.agency.acronym
    ), "id was not correctly set to agency acronym"


# @given(st.builds(RequestDoc))
# def test_dump_model(instance):
#     print(instance)