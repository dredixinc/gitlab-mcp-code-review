import unittest
from unittest.mock import patch, MagicMock

# This is a basic test skeleton for the server
# You would need to add more comprehensive tests


class TestGitLabMCP(unittest.TestCase):
    """Test cases for GitLab MCP server"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_ctx = MagicMock()
        self.mock_lifespan_context = MagicMock()
        self.mock_ctx.request_context.lifespan_context = self.mock_lifespan_context
        self.mock_lifespan_context.token = "fake_token"
        self.mock_lifespan_context.host = "gitlab.com"

    @patch('requests.get')
    def test_make_gitlab_api_request(self, mock_get):
        """Test the GitLab API request function"""
        # Import here to avoid module-level imports before patching
        from server import make_gitlab_api_request
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "test_project"}
        mock_get.return_value = mock_response
        
        # Test the function
        result = make_gitlab_api_request(self.mock_ctx, "projects/123")
        
        # Assertions
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": 123, "name": "test_project"})

    @patch('requests.post')
    def test_add_merge_request_comment_regular(self, mock_post):
        """Test adding a regular (non-resolvable) comment uses the /notes endpoint"""
        from server import add_merge_request_comment

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "body": "Great work!"}
        mock_post.return_value = mock_response

        result = add_merge_request_comment(self.mock_ctx, "123", "5", "Great work!")

        call_url = mock_post.call_args[0][0]
        self.assertIn("/notes", call_url)
        self.assertNotIn("/discussions", call_url)
        self.assertEqual(result, {"id": 1, "body": "Great work!"})

    @patch('requests.post')
    def test_add_merge_request_comment_resolvable(self, mock_post):
        """Test adding a resolvable comment uses the /discussions endpoint"""
        from server import add_merge_request_comment

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 2, "notes": [{"body": "Please fix this"}]}
        mock_post.return_value = mock_response

        result = add_merge_request_comment(self.mock_ctx, "123", "5", "Please fix this", resolvable=True)

        call_url = mock_post.call_args[0][0]
        self.assertIn("/discussions", call_url)
        self.assertNotIn("/notes", call_url)
        self.assertEqual(result, {"id": 2, "notes": [{"body": "Please fix this"}]})

    @patch('requests.get')
    def test_get_merge_request_comments(self, mock_get):
        """Test fetching comments for a merge request"""
        from server import get_merge_request_comments

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "body": "First comment"},
            {"id": 2, "body": "Second comment"},
        ]
        mock_get.return_value = mock_response

        result = get_merge_request_comments(self.mock_ctx, "123", "5")

        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        self.assertIn("/notes", call_url)
        self.assertIn("sort=asc", call_url)
        self.assertIn("order_by=created_at", call_url)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["body"], "First comment")

    @patch('requests.get')
    def test_get_merge_request_comments_custom_sort(self, mock_get):
        """Test fetching comments with custom sort and order_by parameters"""
        from server import get_merge_request_comments

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 3, "body": "Latest comment"}]
        mock_get.return_value = mock_response

        result = get_merge_request_comments(self.mock_ctx, "123", "5", sort="desc", order_by="updated_at")

        call_url = mock_get.call_args[0][0]
        self.assertIn("sort=desc", call_url)
        self.assertIn("order_by=updated_at", call_url)
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()