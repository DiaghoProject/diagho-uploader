class TestDiaghoApiTest(TestCase):
    @mock.patch('requests.get')
    def test_diagho_api_test_success(self, mock_get):
        """Test pour une requête réussie avec un code 200."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with mock.patch('builtins.print') as mock_print:
            result = diagho_api_test('http://example.com')
            mock_print.assert_called_once_with(">>> OK")
            assert result == True

    @mock.patch('requests.get')
    def test_diagho_api_test_http_error(self, mock_get):
        """Test pour une erreur HTTP (ex. 404)."""
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with mock.patch('builtins.print') as mock_print:
            result = diagho_api_test('http://example.com')
            assert mock_print.call_count == 3
            assert ">>> ERROR: HTTP error occurred." in [call[0][0] for call in mock_print.call_args_list]
            assert result == False

    @mock.patch('requests.get')
    def test_diagho_api_test_request_exception(self, mock_get):
        """Test pour une autre exception de requête."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with mock.patch('builtins.print') as mock_print:
            result = diagho_api_test('http://example.com')
            mock_print.assert_called_with(">>> ERROR: Request exception occurred.")
            assert result == False

    @mock.patch('requests.get')
    def test_diagho_api_test_exit_on_error(self, mock_get):
        """Test pour la sortie du programme en cas d'erreur avec exit_on_error=True."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with self.assertRaises(SystemExit):
            diagho_api_test('http://example.com', exit_on_error=True)

if __name__ == '__main__':
    unittest.main()