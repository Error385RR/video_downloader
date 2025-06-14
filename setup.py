from setuptools import setup, find_packages

setup(
    name='video_downloader',
    version='1.3',
    packages=find_packages(),
    install_requires=[
        'yt-dlp'
    ],
    entry_points={
        'console_scripts': [
            'video_downloader = video_downloader.main:main',
        ],
    },
    author='Error385RR',
    description='A YouTube downloader CLI using yt-dlp',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
