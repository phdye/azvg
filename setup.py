"""Setup configuration for azvg package."""

# Use distutils for Python 3.2.5 compatibility
from distutils.core import setup
import os.path

# Read long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
try:
    with open(readme_path, "r") as fh:
        long_description = fh.read()
except IOError:
    long_description = "Manage Azure DevOps Library items locally"

setup(
    name="azvg",
    version="0.1.0",
    author="Azure DevOps Library Manager",
    author_email="azvg@example.com",
    description="Manage Azure DevOps Library items locally",
    long_description=long_description,
    url="https://github.com/yourusername/azvg",
    packages=["azvg"],
    package_dir={"": "src"},
    scripts=["bin/azvg"],  # Will create this script
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Environment :: Console",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
    ],
    requires=[],  # No external dependencies for Python 3.2.5
)
