import base64
import requests as http_requests
from github import Github, GithubException
from core.logger import get_configured_logger
from schemas.exceptions.base import ResourceNotFoundException, ForbiddenException, BaseException, UnauthorizedException


class GiteaRestClient:
    """Gitea API client using requests (avoids PyGithub hostname validation issues)."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.session = http_requests.Session()
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self.logger = get_configured_logger(self.__class__.__name__)

    def _handle_response(self, response):
        if response.status_code == 404:
            raise ResourceNotFoundException()
        elif response.status_code in (401, 403):
            raise ForbiddenException(
                message='Git access token is invalid or does not have the required permissions.'
            )
        elif not response.ok:
            self.logger.error(f"Gitea API error: {response.status_code} {response.text[:200]}")
            raise BaseException('Error connecting to git service.')

    def create_file(self, repo_name: str, file_path: str, content: str):
        url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
        payload = {
            "message": "Create file",
            "content": base64.b64encode(content.encode()).decode()
        }
        response = self.session.post(url, json=payload)
        self._handle_response(response)

    def delete_file(self, repo_name: str, file_path: str):
        url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
        response = self.session.get(url)
        self._handle_response(response)
        sha = response.json().get("sha")
        payload = {
            "message": "Remove file",
            "sha": sha
        }
        response = self.session.delete(url, json=payload)
        self._handle_response(response)

    def get_contents(self, repo_name: str, file_path: str, commit_sha: str | None = None):
        url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
        params = {"ref": commit_sha} if commit_sha else {}
        response = self.session.get(url, params=params)
        self._handle_response(response)
        return response.json()

    def get_commits(self, repo_name: str, number_of_commits: int = 1):
        url = f"{self.base_url}/repos/{repo_name}/commits"
        response = self.session.get(url, params={"limit": number_of_commits})
        self._handle_response(response)
        return response.json()

    def get_tag(self, repo_name: str, tag_name: str):
        url = f"{self.base_url}/repos/{repo_name}/tags/{tag_name}"
        response = self.session.get(url)
        if response.status_code == 404:
            return None
        self._handle_response(response)
        return response.json()

    def get_tags(self, repo_name: str, as_list=True):
        url = f"{self.base_url}/repos/{repo_name}/tags"
        response = self.session.get(url)
        self._handle_response(response)
        return response.json()

    def get_commit(self, repo_name: str, commit_sha: str):
        url = f"{self.base_url}/repos/{repo_name}/git/commits/{commit_sha}"
        response = self.session.get(url)
        self._handle_response(response)
        return response.json()

    def compare_commits(self, repo_name: str, base_sha: str, head_sha: str):
        url = f"{self.base_url}/repos/{repo_name}/compare/{base_sha}...{head_sha}"
        response = self.session.get(url)
        self._handle_response(response)
        return response.json()


class GithubRestClient:
    """Unified Git client: uses GiteaRestClient when base_url is set, PyGithub otherwise."""

    def __init__(self, token: str | None = None, base_url: str | None = None):
        if token == "":
            token = None
        self.logger = get_configured_logger(self.__class__.__name__)
        if base_url:
            self._client = GiteaRestClient(base_url=base_url, token=token)
            self._is_gitea = True
        else:
            self._client = Github(login_or_token=token)
            self._is_gitea = False

    def _handle_github_exception(self, _exception):
        if _exception.status == 404:
            self.logger.info('Resource not found in github: %s', _exception)
            raise ResourceNotFoundException()
        elif _exception.status in (403, 401):
            self.logger.info('Forbidden in github: %s', _exception)
            self.logger.exception(_exception)
            raise ForbiddenException(message='Github access token is invalid or does not have the required permissions.')
        else:
            self.logger.exception(_exception)
            raise BaseException('Error connecting to github service.')

    def get_contents(self, repo_name: str, file_path: str, commit_sha: str | None = None):
        if self._is_gitea:
            return self._client.get_contents(repo_name, file_path, commit_sha)
        try:
            repo = self._client.get_repo(repo_name)
            if not commit_sha:
                return repo.get_contents(file_path)
            return repo.get_contents(file_path, ref=commit_sha)
        except GithubException as e:
            self._handle_github_exception(e)

    def create_file(self, repo_name: str, file_path: str, content: str):
        if self._is_gitea:
            return self._client.create_file(repo_name, file_path, content)
        try:
            repo = self._client.get_repo(repo_name)
            repo.create_file(file_path, 'Create file', content)
        except GithubException as e:
            self.logger.info('Could not create file in github: %s', e)
            self._handle_github_exception(e)

    def delete_file(self, repo_name: str, file_path: str):
        if self._is_gitea:
            return self._client.delete_file(repo_name, file_path)
        try:
            repo = self._client.get_repo(repo_name)
            contents = repo.get_contents(file_path)
            repo.delete_file(contents.path, "Remove file", contents.sha)
        except GithubException as e:
            self.logger.info('Could not delete file in github: %s', e)
            self._handle_github_exception(e)

    def get_commits(self, repo_name: str, number_of_commits: int = 1):
        if self._is_gitea:
            return self._client.get_commits(repo_name, number_of_commits)
        try:
            repo = self._client.get_repo(repo_name)
            return [e for e in repo.get_commits()[:number_of_commits]]
        except GithubException as e:
            self._handle_github_exception(e)

    def get_tag(self, repo_name: str, tag_name: str):
        if self._is_gitea:
            return self._client.get_tag(repo_name, tag_name)
        try:
            repo = self._client.get_repo(repo_name)
            for tag in repo.get_tags():
                if str(tag.name) == tag_name:
                    return tag
            return None
        except GithubException as e:
            self.logger.exception('Could not get tag in github: %s', e)
            self._handle_github_exception(e)

    def get_tags(self, repo_name: str, as_list=True):
        if self._is_gitea:
            return self._client.get_tags(repo_name, as_list)
        try:
            repo = self._client.get_repo(repo_name)
            tags = repo.get_tags()
            if as_list:
                tags = [e for e in tags]
            return tags
        except GithubException as e:
            self.logger.exception('Could not get tags in github: %s', e)
            self._handle_github_exception(e)

    def get_commit(self, repo_name: str, commit_sha: str):
        if self._is_gitea:
            return self._client.get_commit(repo_name, commit_sha)
        try:
            repo = self._client.get_repo(repo_name)
            return repo.get_commit(commit_sha)
        except GithubException as e:
            self.logger.exception('Could not get commit in github: %s', e)
            self._handle_github_exception(e)

    def compare_commits(self, repo_name: str, base_sha: str, head_sha: str):
        if self._is_gitea:
            return self._client.compare_commits(repo_name, base_sha, head_sha)
        try:
            repo = self._client.get_repo(repo_name)
            return repo.compare(base_sha, head_sha)
        except GithubException as e:
            self.logger.exception('Could not compare commits in github: %s', e)
            self._handle_github_exception(e)
