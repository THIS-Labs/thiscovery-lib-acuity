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
    import local.dev_config  # set env variables
    import local.secrets  # set env variables
except ModuleNotFoundError:
    pass

import datetime
import functools
import json
import requests
from http import HTTPStatus

import thiscovery_lib.utilities as utils
from pprint import pprint
from simplejson.errors import JSONDecodeError
from thiscovery_lib.sns_utilities import SnsClient


def response_handler(func):
    """
    Decorator to process the response of an API call to Acuity. If the
    call is successful, returns only the json representation
    of the response body (or the response if not json-encoded).
    If the call is not successful, raises an error.

    Args:
        func: the decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.ok:
            try:
                return response.json()
            except JSONDecodeError:
                return response
        else:
            logger = utils.get_logger()
            logger.error(
                f"Acuity API call failed with response: {response}",
                extra={"response.content": response.content},
            )
            raise utils.DetailedValueError(
                f"Acuity API call failed with response: {response}",
                details={"response": response.content},
            )

    return wrapper


class AcuityClient:
    base_url = "https://acuityscheduling.com/api/v1/"
    strftime_format_str = "%Y-%m-%d %I:%M%p"
    anon_ut_id_form_id = 8861964
    anon_psu_id_form_id = 8941105

    def __init__(self, correlation_id=None):
        acuity_credentials = utils.get_secret("acuity-connection")
        self.session = requests.Session()
        self.session.auth = (
            acuity_credentials["user-id"],
            acuity_credentials["api-key"],
        )
        self.logger = utils.get_logger()
        self.calendars = None
        self.correlation_id = correlation_id
        self.app_endpoint = self.base_url + "appointments"
        self.clients_endpoint = self.base_url + "clients"

    # region appointments
    @response_handler
    def get_appointments(self, **kwargs):
        return self.session.get(self.app_endpoint, params=kwargs)

    @response_handler
    def get_appointment_by_id(self, appointment_id):
        return self.session.get(f"{self.app_endpoint}/{appointment_id}")

    @response_handler
    def create_appointment(
        self,
        appointment_datetime,
        type_id,
        email,
        first_name,
        last_name,
        anon_user_task_id=None,
        anon_project_specific_user_id=None,
        calendar_id=None,
    ):

        data = {
            "datetime": appointment_datetime.strftime(self.strftime_format_str),
            "appointmentTypeID": type_id,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "fields": self.user_metadata_form_fields(
                anon_project_specific_user_id, anon_user_task_id
            ),
        }
        if calendar_id:
            data["calendarID"] = int(calendar_id)

        return self.session.post(self.app_endpoint, json=data)

    def reschedule_appointment(self, appointment_id, new_datetime, **kwargs):
        response = self.session.put(
            url=f"{self.base_url}appointments/{appointment_id}/reschedule",
            data=json.dumps(
                {**kwargs, "datetime": new_datetime.strftime("%Y-%m-%dT%H:%M:%S%Z")}
            ),
        )
        if response.ok:
            return response.status_code
        else:
            error_message = (
                f"Acuity call failed with status code: {response.status_code}"
            )
            error_dict = {"response": response.content}
            self.logger.error(error_message, extra=error_dict)
            raise utils.DetailedValueError(error_message, details=error_dict)

    def cancel_appointment(self, appointment_id):
        return self.session.put(f"{self.app_endpoint}/{appointment_id}/cancel")

    # endregion

    # region clients
    @response_handler
    def get_clients(self, **kwargs):
        return self.session.get(self.clients_endpoint, params=kwargs)

    @response_handler
    def post_client(self, **kwargs):
        return self.session.post(self.clients_endpoint, json=kwargs)

    def delete_client(self, **kwargs):
        return self.session.delete(self.clients_endpoint, params=kwargs)

    # endregion

    @classmethod
    def user_metadata_form_fields(cls, anon_psu_id, anon_ut_id):
        def field_dict(field_id, value):
            return {
                "id": field_id,
                "value": value,
            }

        form_fields = list()
        if anon_ut_id:
            form_fields.append(field_dict(cls.anon_ut_id_form_id, anon_ut_id))
        if anon_psu_id:
            form_fields.append(
                field_dict(
                    cls.anon_psu_id_form_id,
                    anon_psu_id,
                )
            )

        return form_fields

    @response_handler
    def get_appointment_types(self):
        return self.session.get(f"{self.base_url}appointment-types")

    @response_handler
    def get_webhooks(self):
        return self.session.get(f"{self.base_url}webhooks")

    @response_handler
    def delete_webhooks(self, webhook_id):
        return self.session.delete(f"{self.base_url}webhooks/{webhook_id}")

    @response_handler
    def post_webhooks(self, appointment_event, target=None):
        if target is None:
            env_name = utils.get_environment_name()
            if env_name == "prod":
                api_base_url = f"https://interviews-api.thiscovery.org"
            else:
                api_base_url = f"https://{env_name}-interviews-api.thiscovery.org"
            target = f"{api_base_url}/v1/interview-appointment"

        body_params = {
            "event": appointment_event,
            "target": target,
        }
        body_json = json.dumps(body_params)
        return self.session.post(f"{self.base_url}webhooks", data=body_json)

    def get_calendars(self):
        response = self.session.get(f"{self.base_url}calendars")
        if response.ok:
            calendars = response.json()
            self.calendars = {x["id"]: x for x in calendars}
            return response.json()
        else:
            raise utils.DetailedValueError(
                f"Acuity get calendars call failed with response: {response}",
                details={},
            )

    def get_calendar_by_id(self, calendar_id):
        if self.calendars is None:
            self.get_calendars()
        return self.calendars[calendar_id]

    @response_handler
    def get_blocks(self, calendar_id=None):
        query_parameters = None
        if calendar_id:
            query_parameters = {"calendarID": int(calendar_id)}
        return self.session.get(f"{self.base_url}blocks", params=query_parameters)

    def post_block(self, calendar_id, start, end, notes="automated block"):
        """

        Args:
            calendar_id (int): acuity calendar id
            start (datetime.datetime): start time of block
            end (datetime.datetime): end time of block
            notes (str): any notes to include for the blocked off time

        Returns:

        """
        body_params = {
            "calendarID": calendar_id,
            "start": start.strftime(self.strftime_format_str),
            "end": end.strftime(self.strftime_format_str),
            "notes": notes,
        }
        body_json = json.dumps(body_params)
        self.logger.debug(
            "Acuity API call",
            extra={
                "body_params": body_params,
                "correlation_id": self.correlation_id,
            },
        )
        response = self.session.post(f"{self.base_url}blocks", data=body_json)
        if response.ok:
            return response.json()
        elif response.status_code == HTTPStatus.BAD_REQUEST:
            error_message = f"Acuity post block call failed with status code: {response.status_code}"
            error_dict = {"calendar_id": calendar_id}
            self.logger.error(error_message, extra=error_dict)
            return None
        else:
            raise utils.DetailedValueError(
                f"Acuity post block call failed with response: {response.status_code}, {response.text}",
                details={},
            )

    def delete_block(self, block_id):
        response = self.session.delete(f"{self.base_url}blocks/{block_id}")
        if response.ok:
            return response.status_code
        else:
            error_message = f"Acuity delete block call failed with status code: {response.status_code}"
            error_dict = {"block_id": block_id}
            self.logger.error(error_message, extra=error_dict)
            raise utils.DetailedValueError(error_message, details=error_dict)


class InvalidBookingHandler:
    """
    Handles invalid_acuity_booking events posted by the interview system

    Example event (invalid due to null anon_user_task_id):
        {
        'detail-type': invalid_acuity_booking,
        'detail': {
            'anon_project_specific_user_id': 'f2fac677-cb2c-42a0-9fa6-494059352569',
            'anon_user_task_id': null,
            'appointment_type_id': 123456,
            'appointment_datetime': '2021-01-08T10:15:00+0000',
            'calendar_name': 'Andre',
            'calendar_id': 123456,
            'appointment_type': 'Interview for GPs',
            'appointment_id': 123456,
        }
    """

    def __init__(self, event):
        self.sns_client = SnsClient()
        self.detail = SnsClient.dict_to_plaintext_list(event["detail"])

    def notify_sns_topic(self, message, subject):
        topic_arn = utils.get_secret("sns-topics")["interview-notifications-arn"]
        self.sns_client.publish(
            message=message,
            topic_arn=topic_arn,
            Subject=subject,
        )

    def main(self):
        self.notify_sns_topic(
            message=f"Invalid Acuity booking received. Please log into Acuity and fix the following appointment:\n\n"
            f"{self.detail}",
            subject="Action needed: invalid acuity booking",
        )
