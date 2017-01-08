from .bitbucket import BitBucketRequestParser
from .github import GitHubRequestParser
from .gitlab import GitLabRequestParser
from .gitlabci import GitLabCIRequestParser
from .generic import GenericRequestParser
from .coding import CodingRequestParser


def get_service_handler(request_headers, request_body, action):
    """Parses the incoming request and attempts to determine whether
    it originates from GitHub, GitLab or any other known service."""
    import json

    payload = json.loads(request_body)

    if not isinstance(payload, dict):
        raise ValueError("Invalid JSON object")

    user_agent = 'user-agent' in request_headers and request_headers['user-agent']
    content_type = 'content-type' in request_headers and request_headers['content-type']

    # Assume Coding if the X-Coding-Event HTTP header is set
    if 'x-coding-event' in request_headers:
        return CodingRequestParser

    # Assume GitLab if the X-Gitlab-Event HTTP header is set
    elif 'x-gitlab-event' in request_headers:

        # Special Case for Gitlab CI
        if content_type == "application/json" and "build_status" in payload:
            return GitLabCIRequestParser
        else:
            return GitLabRequestParser

    # Assume GitHub if the X-GitHub-Event HTTP header is set
    elif 'x-github-event' in request_headers:

        return GitHubRequestParser

    # Assume BitBucket if the User-Agent HTTP header is set to
    # 'Bitbucket-Webhooks/2.0' (or something similar)
    elif user_agent and user_agent.lower().find('bitbucket') != -1:

        return BitBucketRequestParser

    # This handles old GitLab requests and Gogs requests for example.
    elif content_type == "application/json":

        action.log_info("Received event from unknown origin.")
        return GenericRequestParser

    action.log_error("Unable to recognize request origin. Don't know how to handle the request.")
    return