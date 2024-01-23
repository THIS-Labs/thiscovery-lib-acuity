import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thiscovery-lib",  # Replace with your own username
    version="2021.2.3.2",
    author="Thiscovery team",
    author_email="support@thiscovery.org",
    description="Thiscovery library",
    install_requires=[
        "boto3",
        "botocore",
        "python-dateutil",
        "jsons",
        "python-json-logger",
        "requests",
        # requests==2.28.2
        "simplejson",
        "validators",
        "sendgrid",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/THIS-Labs/thiscovery-lib",
    package_data={
        "thiscovery_lib": ["countries.json"],
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
