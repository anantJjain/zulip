import cProfile
import logging
import tempfile
from typing import Any

from django.contrib.sessions.backends.base import SessionBase
from django.core.management.base import CommandParser
from django.http import HttpRequest, HttpResponse

from zerver.lib.management import ZulipBaseCommand
from zerver.lib.request import get_request_notes
from zerver.lib.test_helpers import HostRequestMock
from zerver.middleware import LogRequests
from zerver.models import UserMessage
from zerver.views.message_fetch import get_messages_backend

request_logger = LogRequests()


class MockSession(SessionBase):
    def __init__(self) -> None:
        self.modified = False


def profile_request(request: HttpRequest) -> HttpResponse:
    request_logger.process_request(request)
    prof = cProfile.Profile()
    prof.enable()
    ret = get_messages_backend(request, request.user, apply_markdown=True)
    prof.disable()
    with tempfile.NamedTemporaryFile(prefix="profile.data.", delete=False) as stats_file:
        prof.dump_stats(stats_file.name)
        request_logger.process_response(request, ret)
        logging.info("Profiling data written to %s", stats_file.name)
    return ret


class Command(ZulipBaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("email", metavar="<email>", help="Email address of the user")
        self.add_realm_args(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        realm = self.get_realm(options)
        user = self.get_user(options["email"], realm)
        anchor = UserMessage.objects.filter(user_profile=user).order_by("-message")[200].message_id
        mock_request = HostRequestMock(
            post_data={
                "anchor": anchor,
                "num_before": 1200,
                "num_after": 200,
            },
            user_profile=user,
            meta_data={"REMOTE_ADDR": "127.0.0.1"},
            path="/",
        )
        mock_request.session = MockSession()
        get_request_notes(mock_request).log_data = None

        profile_request(mock_request)
