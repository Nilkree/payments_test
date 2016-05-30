from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='TestApp',
      version='1.0',
      description='A basic Flask app with static files',
      author='Dima Lyubatskiy',
      author_email='lyubatskiy.dima@gmail.com',
      install_requires=required,
      )