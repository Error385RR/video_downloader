from setuptools import setup, find_packages

setup(
    name='onedl',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'yt-dlp'
    ],
    entry_points={
        'console_scripts': [
            'onedl = onedl.main:main',
        ],
    },
    author='Your Name',
    description='A YouTube downloader CLI using yt-dlp',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
