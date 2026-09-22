"""
CloudHub CPU Utilization Report

Fetches CloudHub applications from Anypoint Platform,
retrieves CPU utilization statistics for each application,
and writes the maximum CPU utilization to a CSV file.

Required environment variables:
    ANYPOINT_USERNAME
    ANYPOINT_PASSWORD
    ANYPOINT_ENV_ID
    ANYPOINT_ORG_ID
"""

import csv
import logging
import os
import sys
from datetime import datetime
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://anypoint.mulesoft.com"

LOGIN_URL = f"{BASE_URL}/accounts/login"
APPLICATIONS_URL = f"{BASE_URL}/cloudhub/api/applications"

OUTPUT_FILE = "CpuUtilizationLogs.csv"

REQUEST_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration / Credentials
# ---------------------------------------------------------------------------

USERNAME = os.getenv("ANYPOINT_USERNAME")
PASSWORD = os.getenv("ANYPOINT_PASSWORD")
ENV_ID = os.getenv("ANYPOINT_ENV_ID")
ORG_ID = os.getenv("ANYPOINT_ORG_ID")


def validate_configuration():
    """Validate required environment variables."""

    required = {
        "ANYPOINT_USERNAME": USERNAME,
        "ANYPOINT_PASSWORD": PASSWORD,
        "ANYPOINT_ENV_ID": ENV_ID,
        "ANYPOINT_ORG_ID": ORG_ID,
    }

    missing = [
        name for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: {}".format(
                ", ".join(missing)
            )
        )


# ---------------------------------------------------------------------------
# HTTP Session
# ---------------------------------------------------------------------------

def create_session():
    """
    Create a requests session with retry support.

    Retries:
        - HTTP 429
        - HTTP 500
        - HTTP 502
        - HTTP 503
        - HTTP 504
    """

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy
    )

    session = requests.Session()

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_access_token(session):
    """Authenticate with Anypoint Platform and return access token."""

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
    }

    headers = {
        "Content-Type": "application/json"
    }

    logger.info("Authenticating with Anypoint Platform")

    response = session.post(
        LOGIN_URL,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    token = data.get("access_token")

    if not token:
        raise RuntimeError(
            "Authentication succeeded but access_token was not returned"
        )

    logger.info("Authentication successful")

    return token


# ---------------------------------------------------------------------------
# Common CloudHub Headers
# ---------------------------------------------------------------------------

def get_api_headers(token):
    """Build common CloudHub API headers."""

    return {
        "Authorization": f"Bearer {token}",
        "X-ANYPNT-ENV-ID": ENV_ID,
        "X-ANYPNT-ORG-ID": ORG_ID,
    }


# ---------------------------------------------------------------------------
# Get Applications
# ---------------------------------------------------------------------------

def get_applications(session, token):
    """Return all CloudHub applications."""

    headers = get_api_headers(token)

    logger.info("Fetching CloudHub applications")

    response = session.get(
        APPLICATIONS_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    applications = response.json()

    if not isinstance(applications, list):
        raise RuntimeError(
            "Unexpected applications API response"
        )

    logger.info(
        "Found %d CloudHub applications",
        len(applications)
    )

    return applications


# ---------------------------------------------------------------------------
# Get CPU Utilization
# ---------------------------------------------------------------------------

def get_cpu_usage(session, token, app_name):
    """
    Get CPU utilization statistics for an application.

    Returns:
        max_cpu
        timestamp
    """

    encoded_app_name = quote(
        app_name,
        safe=""
    )

    url = (
        f"{BASE_URL}/cloudhub/api/v2/applications/"
        f"{encoded_app_name}/dashboardStats"
    )

    headers = get_api_headers(token)

    response = session.get(
        url,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    worker_statistics = data.get(
        "workerStatistics",
        []
    )

    if not worker_statistics:
        logger.warning(
            "No worker statistics available for '%s'",
            app_name
        )

        return None, None

    cpu_data = (
        worker_statistics[0]
        .get("statistics", {})
        .get("cpu", {})
    )

    if not cpu_data:
        logger.warning(
            "No CPU data available for '%s'",
            app_name
        )

        return None, None

    # Find timestamp with maximum CPU
    max_timestamp, max_cpu = max(
        cpu_data.items(),
        key=lambda item: item[1]
    )

    # Existing CloudHub response appears to use
    # timestamps such as "1661234567000ms".
    timestamp_value = int(
        max_timestamp.rstrip("ms")
    )

    # Handle milliseconds
    if timestamp_value > 10_000_000_000:
        timestamp_value /= 1000

    timestamp = datetime.fromtimestamp(
        timestamp_value
    ).strftime("%b %d %Y %H:%M:%S")

    return max_cpu, timestamp


# ---------------------------------------------------------------------------
# Write CSV
# ---------------------------------------------------------------------------

def write_csv(results, filename):
    """Write CPU utilization results to CSV."""

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "app_name",
            "DateAndTime",
            "CpuUsage",
        ])

        writer.writerows(results)

    logger.info(
        "CSV report written to %s",
        filename
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    validate_configuration()

    session = create_session()

    # Authenticate
    token = get_access_token(
        session
    )

    # Get applications
    applications = get_applications(
        session,
        token
    )

    results = []

    # Process applications
    for application in applications:

        app_name = application.get("domain")

        if not app_name:
            logger.warning(
                "Skipping application without domain"
            )
            continue

        logger.info(
            "Fetching CPU utilization for '%s'",
            app_name
        )

        try:

            max_cpu, timestamp = get_cpu_usage(
                session,
                token,
                app_name
            )

            if max_cpu is None:
                continue

            results.append([
                app_name,
                timestamp,
                max_cpu,
            ])

        except requests.RequestException as exc:

            logger.error(
                "API request failed for '%s': %s",
                app_name,
                exc
            )

        except (ValueError, KeyError, TypeError) as exc:

            logger.error(
                "Invalid response for '%s': %s",
                app_name,
                exc
            )

    # Write report
    write_csv(
        results,
        OUTPUT_FILE
    )

    logger.info(
        "Completed. %d applications written to report",
        len(results)
    )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    except Exception as exc:

        logger.error(
            "Script failed: %s",
            exc
        )

        sys.exit(1)
