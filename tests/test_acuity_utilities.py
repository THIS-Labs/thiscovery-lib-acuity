#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
try:
    import local.dev_config
    import local.secrets
except ModuleNotFoundError:
    pass

import datetime
from http import HTTPStatus

import thiscovery_dev_tools.testing_tools as test_utils

from thiscovery_lib_acuity.acuity_utilities import AcuityClient
from tests.test_data import test_calendar, test_block


class TestAcuityClient(test_utils.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.acuity_client = AcuityClient()

    def post_test_block(self):
        block_start = datetime.datetime(2030, 12, 25, 9, 0)
        block_end = datetime.datetime(2030, 12, 25, 17, 0)
        block_notes = "Xmas break"
        return self.acuity_client.post_block(
            test_calendar["id"], block_start, block_end, notes=block_notes
        )

    def post_test_block_bad_cal_id(self):
        block_start = datetime.datetime(2030, 12, 25, 9, 0)
        block_end = datetime.datetime(2030, 12, 25, 17, 0)
        bad_cal_id = 12345
        return self.acuity_client.post_block(bad_cal_id, block_start, block_end)

    def test_get_calendars(self):
        response = self.acuity_client.get_calendars()
        for c in response:
            del c["replyTo"]

        expected_acuity_cal = {
            "description": test_calendar["description"],
            "email": test_calendar["email"],
            "id": test_calendar["id"],
            "image": test_calendar["image"],
            "location": test_calendar["location"],
            "name": test_calendar["name"],
            "thumbnail": test_calendar["thumbnail"],
            "timezone": test_calendar["timezone"],
        }

        self.assertIn(expected_acuity_cal, response)

    def test_01_post_get_and_delete_block_ok(self):
        # post test
        response = self.post_test_block()
        block_id = response["id"]
        expected_block_in_get_response = response.copy()
        del response["id"]
        self.assertEqual(test_block, response)
        # get test
        response = self.acuity_client.get_blocks(calendar_id=test_calendar["id"])
        self.assertIn(expected_block_in_get_response, response)
        # delete test
        delete_response = self.acuity_client.delete_block(block_id)
        self.assertEqual(HTTPStatus.NO_CONTENT, delete_response)

    def test_02_post_cal_does_not_exist(self):
        response = self.post_test_block_bad_cal_id()
        self.assertIsNone(response)

    def test_03_post_and_delete_client(self):
        contact_dict = {
            "firstName": "Herbie",
            "lastName": "Hancock",
        }
        posting_response = self.acuity_client.post_client(**contact_dict)
        self.assertDictEqual(
            {
                "firstName": "Herbie",
                "lastName": "Hancock",
                "email": "",
                "phone": "",
                "notes": "",
            },
            posting_response,
        )
        deletion_response = self.acuity_client.delete_client(**contact_dict)
        self.assertEqual(HTTPStatus.NO_CONTENT, deletion_response.status_code)
