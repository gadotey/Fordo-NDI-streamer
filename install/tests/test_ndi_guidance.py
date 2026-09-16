import io
import unittest
from contextlib import redirect_stdout

from platforms.ndi_runtime import (
    NDI_SDK_DOWNLOAD_URL,
    ndi_runtime_problem,
    print_ndi_installation_guidance,
)


def state(
    *,
    header=False,
    library=False,
    architecture=None,
    compatible=None,
    ready=False,
):
    return {
        "header": header,
        "library": library,
        "library_architecture": architecture,
        "architecture_compatible": compatible,
        "runtime_ready": ready,
    }


class TestNDIRuntimeGuidance(unittest.TestCase):

    def test_missing_runtime_reason(self):
        result = ndi_runtime_problem(
            state(),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI SDK/runtime was not found.",
        )

    def test_missing_header_reason(self):
        result = ndi_runtime_problem(
            state(library=True),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI development header was not found.",
        )

    def test_missing_library_reason(self):
        result = ndi_runtime_problem(
            state(header=True),
            machine_architecture="arm64",
        )
        self.assertEqual(
            result,
            "NDI shared library was not found.",
        )

    def test_incompatible_architecture_reason(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture="arm32",
                compatible=False,
            ),
            machine_architecture="arm64",
        )

        self.assertIn("arm32", result)
        self.assertIn("arm64", result)
        self.assertIn("incompatible", result.lower())

    def test_unknown_library_architecture_reason(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture=None,
                compatible=None,
            ),
            machine_architecture="arm64",
        )

        self.assertIn(
            "could not be determined",
            result,
        )

    def test_ready_runtime_has_no_problem(self):
        result = ndi_runtime_problem(
            state(
                header=True,
                library=True,
                architecture="arm64",
                compatible=True,
                ready=True,
            ),
            machine_architecture="arm64",
        )

        self.assertIsNone(result)

    def test_missing_runtime_guidance(self):
        output = io.StringIO()

        with redirect_stdout(output):
            print_ndi_installation_guidance(
                state(),
                machine_architecture="arm64",
            )

        rendered = output.getvalue()

        self.assertIn("NDI Runtime Requirement", rendered)
        self.assertIn("arm64", rendered)
        self.assertIn(NDI_SDK_DOWNLOAD_URL, rendered)
        self.assertIn(
            "python3 install/install.py --dry-run",
            rendered,
        )
        self.assertIn(
            "does not bundle or redistribute",
            rendered,
        )

    def test_ready_runtime_prints_no_guidance(self):
        output = io.StringIO()

        with redirect_stdout(output):
            print_ndi_installation_guidance(
                state(
                    header=True,
                    library=True,
                    architecture="arm64",
                    compatible=True,
                    ready=True,
                ),
                machine_architecture="arm64",
            )

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
