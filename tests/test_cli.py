from unittest import TestCase
from unittest.mock import patch

import main


class BuildCommandTest(TestCase):
    @patch("main._run_compose", return_value=0)
    def test_build_uses_cache_by_default(self, run_compose):
        self.assertEqual(main.main(["build"]), 0)

        run_compose.assert_called_once_with(["build"], False)

    @patch("main._run_compose", return_value=0)
    def test_build_force_disables_cache(self, run_compose):
        self.assertEqual(main.main(["build", "--force"]), 0)

        run_compose.assert_called_once_with(["build", "--no-cache"], False)

    @patch("main._run_compose", return_value=0)
    def test_build_force_short_flag_disables_cache(self, run_compose):
        self.assertEqual(main.main(["build", "-f"]), 0)

        run_compose.assert_called_once_with(["build", "--no-cache"], False)

    @patch("main._run_compose", return_value=0)
    def test_build_force_preserves_verbose(self, run_compose):
        self.assertEqual(main.main(["-v", "build", "--force"]), 0)

        run_compose.assert_called_once_with(["build", "--no-cache"], True)
