"""
Unit tests for secret providers.

Tests all providers with mocks to avoid requiring actual secrets.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any

from agent.secrets import (
    SecretProvider,
    EnvVarProvider,
    DotEnvProvider,
    BitwardenProvider,
    CompositeProvider,
    SecretProviderFactory,
    SecretBackend,
    get_secret_provider,
    SecretNotFoundError,
    ProviderUnavailableError,
)
from agent.secrets.factory import EnvironmentDetector


class TestEnvVarProvider(unittest.TestCase):
    """Test environment variable provider."""

    @patch.dict(os.environ, {"TEST_SECRET": "test_value"}, clear=True)
    def test_get_secret_exists(self):
        """Test retrieving an existing environment variable."""
        provider = EnvVarProvider()
        value = provider.get_secret("TEST_SECRET")
        self.assertEqual(value, "test_value")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_secret_not_found(self):
        """Test error when secret doesn't exist."""
        provider = EnvVarProvider()
        with self.assertRaises(SecretNotFoundError) as ctx:
            provider.get_secret("NONEXISTENT")
        self.assertIn("NONEXISTENT", str(ctx.exception))

    @patch.dict(os.environ, {"APP_SECRET": "value1", "APP_TOKEN": "value2"}, clear=True)
    def test_prefix_filtering(self):
        """Test prefix-based filtering."""
        provider = EnvVarProvider({"prefix": "APP_"})
        value = provider.get_secret("SECRET")  # Will look for APP_SECRET
        self.assertEqual(value, "value1")

    @patch.dict(os.environ, {"secret": "lower", "SECRET": "upper"}, clear=True)
    def test_case_transformation(self):
        """Test uppercase transformation."""
        provider = EnvVarProvider({"uppercase": True})
        value = provider.get_secret("secret")  # Will look for SECRET
        self.assertEqual(value, "upper")

    @patch.dict(os.environ, {"KEY1": "val1", "KEY2": "val2", "OTHER": "val3"}, clear=True)
    def test_list_secrets(self):
        """Test listing all environment variables."""
        provider = EnvVarProvider()
        secrets = provider.list_secrets()
        self.assertIn("KEY1", secrets)
        self.assertIn("KEY2", secrets)
        self.assertIn("OTHER", secrets)

    @patch.dict(os.environ, {"APP_KEY1": "val1", "APP_KEY2": "val2", "OTHER": "val3"}, clear=True)
    def test_list_secrets_with_prefix(self):
        """Test listing with prefix filter."""
        provider = EnvVarProvider({"prefix": "APP_", "strip_prefix": True})
        secrets = provider.list_secrets()
        self.assertIn("KEY1", secrets)
        self.assertIn("KEY2", secrets)
        self.assertNotIn("OTHER", secrets)

    def test_is_available_always_true(self):
        """Test that EnvVarProvider is always available."""
        provider = EnvVarProvider()
        self.assertTrue(provider.is_available())

    @patch.dict(os.environ, {"CACHED": "initial"}, clear=True)
    def test_caching(self):
        """Test that values are cached."""
        provider = EnvVarProvider({"cache_enabled": True})

        # First retrieval
        value1 = provider.get_secret("CACHED")
        self.assertEqual(value1, "initial")

        # Change the environment variable
        os.environ["CACHED"] = "changed"

        # Should still return cached value
        value2 = provider.get_secret("CACHED")
        self.assertEqual(value2, "initial")

        # After refresh, should get new value
        provider.refresh()
        value3 = provider.get_secret("CACHED")
        self.assertEqual(value3, "changed")


class TestBitwardenProvider(unittest.TestCase):
    """Test Bitwarden provider."""

    @patch("agent.secrets.bitwarden.shutil.which")
    @patch("agent.secrets.bitwarden.subprocess.run")
    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test_token"})
    def test_get_secret_success(self, mock_run, mock_which):
        """Test successful secret retrieval from Bitwarden."""
        # Mock bws binary location
        mock_which.return_value = "/usr/bin/bws"

        # Mock secret list response
        list_response = MagicMock()
        list_response.stdout = json.dumps([
            {"id": "secret-1", "key": "TEST_KEY", "value": "test_value"},
            {"id": "secret-2", "key": "OTHER_KEY", "value": "other_value"},
        ])
        list_response.returncode = 0

        # Mock get secret response
        get_response = MagicMock()
        get_response.stdout = json.dumps({
            "id": "secret-1",
            "key": "TEST_KEY",
            "value": "test_value"
        })
        get_response.returncode = 0

        mock_run.side_effect = [list_response, get_response]

        provider = BitwardenProvider()
        value = provider.get_secret("TEST_KEY")
        self.assertEqual(value, "test_value")

        # Verify correct commands were called
        self.assertEqual(mock_run.call_count, 2)

    @patch("agent.secrets.bitwarden.shutil.which")
    @patch.dict(os.environ, {}, clear=True)
    def test_not_available_no_token(self, mock_which):
        """Test provider not available when token missing."""
        mock_which.return_value = "/usr/bin/bws"
        provider = BitwardenProvider()
        self.assertFalse(provider.is_available())

    @patch("agent.secrets.bitwarden.shutil.which")
    def test_not_available_no_binary(self, mock_which):
        """Test provider not available when bws not installed."""
        mock_which.return_value = None
        with self.assertRaises(ProviderUnavailableError):
            BitwardenProvider()

    @patch("agent.secrets.bitwarden.shutil.which")
    @patch("agent.secrets.bitwarden.subprocess.run")
    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test_token"})
    def test_secret_not_found(self, mock_run, mock_which):
        """Test error when secret doesn't exist."""
        mock_which.return_value = "/usr/bin/bws"

        # Mock empty secret list
        list_response = MagicMock()
        list_response.stdout = json.dumps([])
        list_response.returncode = 0

        mock_run.return_value = list_response

        provider = BitwardenProvider()
        with self.assertRaises(SecretNotFoundError):
            provider.get_secret("NONEXISTENT")

    @patch("agent.secrets.bitwarden.shutil.which")
    @patch("agent.secrets.bitwarden.subprocess.run")
    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test_token"})
    def test_list_secrets(self, mock_run, mock_which):
        """Test listing secrets from Bitwarden."""
        mock_which.return_value = "/usr/bin/bws"

        list_response = MagicMock()
        list_response.stdout = json.dumps([
            {"id": "1", "key": "KEY1", "projectId": "proj1"},
            {"id": "2", "key": "KEY2", "projectId": "proj1"},
            {"id": "3", "key": "KEY3", "projectId": "proj2"},
        ])
        list_response.returncode = 0

        mock_run.return_value = list_response

        provider = BitwardenProvider()
        secrets = provider.list_secrets()
        self.assertEqual(secrets, ["KEY1", "KEY2", "KEY3"])

    @patch("agent.secrets.bitwarden.shutil.which")
    @patch("agent.secrets.bitwarden.subprocess.run")
    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test_token"})
    def test_project_filtering(self, mock_run, mock_which):
        """Test filtering secrets by project ID."""
        mock_which.return_value = "/usr/bin/bws"

        list_response = MagicMock()
        list_response.stdout = json.dumps([
            {"id": "1", "key": "KEY1", "projectId": "proj1"},
            {"id": "2", "key": "KEY2", "projectId": "proj1"},
            {"id": "3", "key": "KEY3", "projectId": "proj2"},
        ])
        list_response.returncode = 0

        mock_run.return_value = list_response

        provider = BitwardenProvider({"project_id": "proj1"})
        secrets = provider.list_secrets()
        self.assertEqual(secrets, ["KEY1", "KEY2"])


class TestCompositeProvider(unittest.TestCase):
    """Test composite provider with fallback chains."""

    def test_fallback_chain(self):
        """Test fallback through multiple providers."""
        # Create mock providers
        provider1 = MagicMock(spec=SecretProvider)
        provider1.name = "Provider1"
        provider1.is_available.return_value = True
        provider1.get_secret.side_effect = SecretNotFoundError("KEY", "Provider1")

        provider2 = MagicMock(spec=SecretProvider)
        provider2.name = "Provider2"
        provider2.is_available.return_value = True
        provider2.get_secret.return_value = "value_from_provider2"

        provider3 = MagicMock(spec=SecretProvider)
        provider3.name = "Provider3"
        provider3.is_available.return_value = True
        provider3.get_secret.return_value = "value_from_provider3"

        # Create composite
        composite = CompositeProvider([provider1, provider2, provider3])

        # Should get value from provider2 (first success)
        value = composite.get_secret("KEY")
        self.assertEqual(value, "value_from_provider2")

        # Verify provider1 was tried
        provider1.get_secret.assert_called_once_with("KEY")
        # Verify provider2 was tried and succeeded
        provider2.get_secret.assert_called_once_with("KEY")
        # Verify provider3 was NOT tried (provider2 succeeded)
        provider3.get_secret.assert_not_called()

    def test_all_providers_fail(self):
        """Test error when all providers fail."""
        provider1 = MagicMock(spec=SecretProvider)
        provider1.name = "Provider1"
        provider1.is_available.return_value = True
        provider1.get_secret.side_effect = SecretNotFoundError("KEY", "Provider1")

        provider2 = MagicMock(spec=SecretProvider)
        provider2.name = "Provider2"
        provider2.is_available.return_value = True
        provider2.get_secret.side_effect = SecretNotFoundError("KEY", "Provider2")

        composite = CompositeProvider([provider1, provider2])

        with self.assertRaises(SecretNotFoundError):
            composite.get_secret("KEY")

    def test_unavailable_providers_skipped(self):
        """Test that unavailable providers are skipped."""
        provider1 = MagicMock(spec=SecretProvider)
        provider1.name = "Provider1"
        provider1.is_available.return_value = False  # Not available

        provider2 = MagicMock(spec=SecretProvider)
        provider2.name = "Provider2"
        provider2.is_available.return_value = True
        provider2.get_secret.return_value = "value"

        composite = CompositeProvider([provider1, provider2])

        value = composite.get_secret("KEY")
        self.assertEqual(value, "value")

        # Provider1 should not be called since it's unavailable
        provider1.get_secret.assert_not_called()

    def test_list_secrets_combined(self):
        """Test listing secrets from all providers."""
        provider1 = MagicMock(spec=SecretProvider)
        provider1.name = "Provider1"
        provider1.is_available.return_value = True
        provider1.list_secrets.return_value = ["KEY1", "KEY2", "COMMON"]

        provider2 = MagicMock(spec=SecretProvider)
        provider2.name = "Provider2"
        provider2.is_available.return_value = True
        provider2.list_secrets.return_value = ["KEY3", "KEY4", "COMMON"]

        composite = CompositeProvider([provider1, provider2])

        secrets = composite.list_secrets()
        # Should be deduplicated and sorted
        self.assertEqual(secrets, ["COMMON", "KEY1", "KEY2", "KEY3", "KEY4"])


class TestEnvironmentDetector(unittest.TestCase):
    """Test environment detection."""

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_detect_github_actions(self):
        """Test GitHub Actions detection."""
        self.assertTrue(EnvironmentDetector.is_github_actions())
        self.assertEqual(EnvironmentDetector.detect_environment(), "github")

    @patch.dict(os.environ, {"GITLAB_CI": "true"})
    def test_detect_gitlab_ci(self):
        """Test GitLab CI detection."""
        self.assertTrue(EnvironmentDetector.is_gitlab_ci())
        self.assertEqual(EnvironmentDetector.detect_environment(), "gitlab")

    @patch.dict(os.environ, {"JENKINS_URL": "http://jenkins.example.com"})
    def test_detect_jenkins(self):
        """Test Jenkins detection."""
        self.assertTrue(EnvironmentDetector.is_jenkins())
        self.assertEqual(EnvironmentDetector.detect_environment(), "jenkins")

    @patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"})
    def test_detect_kubernetes(self):
        """Test Kubernetes detection."""
        self.assertTrue(EnvironmentDetector.is_kubernetes())
        self.assertEqual(EnvironmentDetector.detect_environment(), "k8s")

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1"})
    def test_detect_aws(self):
        """Test AWS detection."""
        self.assertTrue(EnvironmentDetector.is_aws())
        self.assertEqual(EnvironmentDetector.detect_environment(), "aws")

    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test_token"})
    def test_has_bitwarden(self):
        """Test Bitwarden availability detection."""
        self.assertTrue(EnvironmentDetector.has_bitwarden())

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_local(self):
        """Test local environment detection."""
        self.assertEqual(EnvironmentDetector.detect_environment(), "local")


class TestSecretProviderFactory(unittest.TestCase):
    """Test secret provider factory."""

    def test_create_single_provider(self):
        """Test creating a single provider."""
        provider = SecretProviderFactory.create_provider(SecretBackend.ENVVAR)
        self.assertIsInstance(provider, EnvVarProvider)

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_auto_detect_github(self):
        """Test auto-detection in GitHub Actions."""
        provider = SecretProviderFactory.create_auto_provider()
        self.assertIsInstance(provider, EnvVarProvider)

    @patch.dict(os.environ, {"BWS_ACCESS_TOKEN": "test", "TEST": "value"})
    @patch("agent.secrets.factory.EnvironmentDetector.detect_environment")
    @patch("agent.secrets.bitwarden.shutil.which")
    def test_auto_detect_local_with_bitwarden(self, mock_which, mock_detect):
        """Test auto-detection in local environment with Bitwarden."""
        mock_detect.return_value = "local"
        mock_which.return_value = "/usr/bin/bws"

        # Mock subprocess for Bitwarden availability check
        with patch("agent.secrets.bitwarden.subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps([])
            mock_run.return_value.returncode = 0

            provider = SecretProviderFactory.create_auto_provider()

            # Should create a composite provider
            self.assertIsInstance(provider, CompositeProvider)
            # Should have Bitwarden and EnvVar providers
            self.assertEqual(len(provider.providers), 2)

    def test_get_secret_provider_function(self):
        """Test convenience function."""
        provider = get_secret_provider("envvar", {"prefix": "APP_"})
        self.assertIsInstance(provider, EnvVarProvider)
        self.assertEqual(provider.config["prefix"], "APP_")


if __name__ == "__main__":
    unittest.main()