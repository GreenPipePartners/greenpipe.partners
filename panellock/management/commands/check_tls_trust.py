import ssl
from urllib.error import HTTPError
from urllib.request import urlopen

import botocore.session
import requests
import stripe
from botocore.awsrequest import AWSRequest
from botocore.httpsession import URLLib3Session
from django.core.management.base import BaseCommand, CommandError


COMPROMISED_URLS = (
    "https://dv-g3b-emudhra.we-have-a-problem.com/",
    "https://dv-g3b-aaa-emudhra.we-have-a-problem.com/",
)
CONTROL_URL = "https://example.com/"
TIMEOUT = 10


def _certificate_error(error):
    pending = [error]
    seen = set()
    while pending:
        current = pending.pop()
        if not isinstance(current, BaseException) or id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, ssl.SSLCertVerificationError):
            return True
        pending.extend(current.args)
        pending.extend((current.__cause__, current.__context__, getattr(current, "reason", None)))
    return False


def _urllib_get(url):
    try:
        with urlopen(url, timeout=TIMEOUT):
            pass
    except HTTPError as error:
        # An HTTP error still means that TLS verification succeeded.
        error.close()


def _requests_get(url):
    with requests.get(url, timeout=TIMEOUT, allow_redirects=False, stream=True):
        pass


def _botocore_get(url):
    verify = botocore.session.get_session().get_config_variable("ca_bundle") or True
    session = URLLib3Session(verify=verify, timeout=TIMEOUT)
    try:
        session.send(AWSRequest(method="GET", url=url).prepare())
    finally:
        session.close()


def _stripe_get(url):
    client = stripe.RequestsClient(timeout=TIMEOUT)
    try:
        client.request("get", url, headers={})
    finally:
        client.close()


class Command(BaseCommand):
    help = "Check HTTPS clients reject the compromised eMudhra certificate chains."

    def handle(self, *args, **options):
        failures = []
        for name, get in (
            ("urllib/system CA", _urllib_get),
            ("Requests", _requests_get),
            ("Botocore", _botocore_get),
            ("Stripe", _stripe_get),
        ):
            try:
                get(CONTROL_URL)
            except Exception as error:
                failures.append(f"{name}: valid HTTPS control failed ({type(error).__name__})")
                continue
            for url in COMPROMISED_URLS:
                try:
                    get(url)
                except Exception as error:
                    if _certificate_error(error):
                        self.stdout.write(self.style.SUCCESS(f"{name}: rejected {url}"))
                    else:
                        failures.append(f"{name}: inconclusive {url} ({type(error).__name__})")
                else:
                    failures.append(f"{name}: TRUSTED compromised certificate at {url}")
        if failures:
            raise CommandError("\n".join(failures))
        self.stdout.write(self.style.SUCCESS("All HTTPS clients rejected both compromised chains."))
