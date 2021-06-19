from pathlib import Path

from setuptools import find_packages, setup

readme = Path(__file__).with_name('README.md')
readme_content = ''
if readme.is_file():
    with readme.open("r", encoding='utf-8') as fh:
        readme_content = fh.read()

setup(
    name='zone_api',
    package_dir={"": "src"},
    packages=find_packages('src'),
    version='0.2.1',
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description='Reusable Home Automation rules.',
    long_description=readme_content,
    long_description_content_type="text/markdown",
    author='YF',
    # author_email='',
    url='https://github.com/yfaway/zone-apis',
    download_url='https://github.com/yfaway/zone-apis/archive/refs/tags/v_01.tar.gz',
    keywords=['zone api', 'home automation', 'openhab', 'habapp'],
    install_requires=[
        'habapp>=0.30.3',
        'requests',
        'schedule',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',
        "Topic :: Home Automation",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
