from setuptools import setup

setup(name='pyxi',
      version='0.4',
      description='Python wrapper for xchange-interface API',
      url='http://github.com/altfund/pyxi',
      author='Altfund Capital',
      author_email='altfund@altfund.org',
      license='MIT',
      packages=['pyxi'],
      install_requires=[
          'certifi==2017.7.27.1',
          'chardet==3.0.4',
          'configparser==3.5.0',
          'idna==2.6',
          'invoke==0.20.4',
          'pycrypto==2.6.1',
          'requests==2.18.4',
          'urllib3==1.22',
          'ccxt==1.10.780',
      ],
      zip_safe=False)
